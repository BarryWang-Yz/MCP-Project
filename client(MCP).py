# response.choices[0]:  Choice(finish_reason='stop', 
# index=0, logprobs=None, 
# message=ChatCompletionMessage(content='Hello! How can I assist you today? 😊', 
# refusal=None, 
# role='assistant', 
# annotations=None, audio=None, function_call=None, tool_calls=None, 
# reasoning_content='Okay, the user greeted me and said, "Hello." I need to respond in a friendly and helpful manner. Let\'s start with a greeting and ask how I can assist them today. Keep it open-ended to encourage them to share their issue. Maybe something like, "Hello! How can I assist you today?" That should work.'))

import asyncio, os, json, sys, textwrap, re
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ---------- 颜色样式 ----------
BOLD = "\033[1m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


load_dotenv()

SYS_PROMPT = (
    "你可以调用以下三种数据库工具："
    "[list_tables]、[describe_table]、[query_table]。请按需调用，只执行只读 SQL。"
    "通常来说，你可以先调用[list_tables]工具将"
    "请注意：如果工具未返回数据，那么请不要生成你的假象值，只需要说'未获得数据'。"
)

class MCPClient():

    def __init__(self) -> None:
        self.exit_stack = AsyncExitStack()
        self.api_key = os.getenv("QWEN_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=os.getenv("QWEN_BASE_URL"),
        )
        self.model = os.getenv("QWEN_MODEL")
        if not self.api_key:
            raise ValueError("无法正确获取API key，请在.env文件中配置。")
        
        # self.client = OpenAI(api_key=self.deepseek_api_key, base_url=self.base_url)
        # self.session: Optional[ClientSession] = None

    async def connect_to_server(self, path_to_script: str):
        cmd = "python" if path_to_script.endswith(".py") else "node"
        server_params = StdioServerParameters(command=cmd, args=[path_to_script])
        self.stdio, self.write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session: ClientSession = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        
        tools = (await self.session.list_tools()).tools
        self.tool_specs = [{
            "type":"function",
            "function":{
                "name":t.name,
                "description":t.description,
                "input_schema":t.inputSchema
            }
        } for t in tools]
        print("✅ 成功连接至服务器\n")
        print("✅ 已注册工具:", [t["function"]["name"] for t in self.tool_specs])

    async def chat_loop(self):
        messages = [{"role": "system", "content": SYS_PROMPT}]
        print("\n欢迎使用 Qwen‑MCP demo，输入 quit 退出。")

        while True:
            user_input = input("\n" + BOLD + "您的输入> " + RESET).strip()
            if user_input.lower() == "quit":
                print("再见！")
                break
            messages.append({"role": "user", "content": user_input})
            await self.query_process(messages)
    
    async def query_process(self, messages):
        """递归地调用模型；只要有 tool_calls，就执行工具并继续对话"""
        is_reasoning = False
        is_answering = False
        while True:
            tool_buffers: dict[int, dict] = {}
            reasoning_buf, answer_buf = [], []

            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tool_specs,
                stream=True,
                extra_body={
                    "enable_thinking": True,
                    # "enable_search": True,
                    # "search_options": {"forced_search": True},
                },
            )

            # ---- 逐块读取流式响应 ----
            
            for chunk in resp:
                delta = chunk.choices[0].delta

                # A. 思考内容
                rc = getattr(delta, "reasoning_content", None)
                txt = getattr(delta, "content", None) or ""

                if txt.startswith("Error executing tool"):
                    # 反馈给模型，让它立即重试
                    messages.append({
                        "role":"system",
                        "content": f"工具调用失败，错误信息：{txt}\n请检查参数或表名后重试。"
                    })
                    # 跳出当前流，让模型重启一次调用
                    return await self.query_process(messages)
                
                if rc:
                    if not is_reasoning:
                        print("\n" + "=" * 20 + f"🧠 深度思考" + "=" * 20 + "\n")
                        is_reasoning = True
                    reasoning_buf.append(delta.reasoning_content)
                    print(BOLD + delta.reasoning_content + RESET, end="", flush=True)
                
                    # print("\n")
                # B. 正文
                else:
                    answer = getattr(delta, "content", None)
                    if answer:
                        if not is_answering:
                            print ("\n" + "=" * 20 + f"最终答案" + "=" * 20 + "\n")
                            is_answering = True    
                        answer_buf.append(delta.content)
                        print(delta.content, end="", flush=True)

                    # C. tool_calls 分片
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            buf = tool_buffers.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                            if tc.id:
                                buf["id"] = tc.id
                            if tc.function.name:
                                buf["name"] = tc.function.name
                            if tc.function.arguments:
                                buf["arguments"] += tc.function.arguments

            # ---- 如果本轮包含工具调用 ----
            if tool_buffers:
                # 打印思考内容
                print("\n" + YELLOW + "⚙️  执行工具…" + RESET)
                
                tool_messages = []
                err_messages = []
                any_error = False
                for buf in tool_buffers.values():
                    # 1. 执行工具
                    name = buf["name"]
                    args = json.loads(buf["arguments"] or "{}")
                    result = await self.session.call_tool(name, args)
                    
                    records = []
                    print("\nDEBUG query_mysql raw content: ", result.content)
                    for item in result.content:
                        # 正确地取出 JSON 字符串
                        print("\nDEBUG text raw content: ", item.text)
                        raw_json = item.text
                        try:
                             row = json.loads(raw_json)
                        except json.JSONDecodeError:
                            continue

                        text = getattr(item, "text", "")
                        records.append(row)
                        if text.startswith("Error executing tool"):
                            any_error = True
                            err_messages.append(text)

                    if any_error:
                        err_block = "\n".join(f"- {m}" for m in err_messages)
                        print("\nDEBUG err_block: ", err_block)
                        correction_msg = {
                            "role": "system",
                            "content": (
                                "注意：上次调用工具时出错，错误信息如下：\n"
                                f"{err_block}\n"
                                "请根据提示重新选择工具或修正参数后再次调用。"
                            )
                        }
                        messages.append(correction_msg)
                        continue

                    human_readable_lines = []
                    for idx, rec in enumerate(records, 1):
                        parts = [f"{k} : {v}" for k, v in rec.items()]
                        human_readable_lines.append(f"{idx}. " + " ; ".join(parts))
                    
                    human_readable = "\n".join(human_readable_lines)

                    # 2. 构造 tool 消息
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": buf["id"],
                        "content": human_readable,
                    })
                    print(GREEN + f"\n【{name} 返回】\n" + RESET + human_readable)

                # 3. 构造 assistant 消息（带 tool_calls 元信息）
                assistant_msg = {
                    "role": "assistant",
                    "content": human_readable,
                    "tool_calls": [
                        {
                            "id": buf["id"],
                            "function": {"name": buf["name"], "arguments": buf["arguments"]}
                        }
                        for buf in tool_buffers.values()
                    ],
                }
                messages.extend([assistant_msg, *tool_messages])
                continue
            print()            # 换行
            return

    async def cleanup (self):
        await self.exit_stack.aclose()

async def main ():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()

    finally:
        await client.cleanup()



if __name__ == "__main__":
    asyncio.run(main())





