from dotenv import load_dotenv
from openai import OpenAI
import os
import dashscope
import json

load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(
    # 如果没有配置环境变量，请用百炼API Key替换：api_key="sk-xxx"
    api_key = os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

reasoning_content = ""  # 定义完整思考过程
answer_content = ""     # 定义完整回复


messages = []
conversation_index = 1

while True:
    is_answering = False
    print("\n" + "="*20 + f"{conversation_index}th conversation" + "="*20 + "\n")
    conversation_index += 1
    query = input("Your query: ").strip()
    user_message = {"role": "user", "content": query}
    if query.lower() == "quit":
         break
    messages.append(user_message)
    completion = client.chat.completions.create(
        model=os.getenv("QWEN_MODEL"),
        messages=messages,
        extra_body={
            "enable_thinking": True,
            "enable_search": True,
            "search_options": {
                "forced_search": True,
                "search_startegy": "pro",
            },
        },
        stream=True,
        # stream_options={"include_usage": True},   
    )

    print("\n" + "="*20 + "Reasoning Content" + "="*20 + "\n")
    for chunk in completion:
        # if not chunk.choices:
        #     print("\n" + "="*20 + "Usage" + "="*20 + "\n")
        #     print(chunk.usage)
        # else:
        #     # print("[Check Output] chunk: ", chunk.choices[0])
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content != None:
                print(delta.reasoning_content, end="", flush=True)
                reasoning_content+=delta.reasoning_content
            else:
                if delta.content != "" and is_answering is False:
                    print("\n" + "="*20 + "Answer" + "="*20 + "\n")
                    is_answering = True
                print(delta.content, end="", flush=True)
                answer_content+=delta.content