# response.choices[0]:  Choice(finish_reason='stop', 
# index=0, logprobs=None, 
# message=ChatCompletionMessage(content='Hello! How can I assist you today? 😊', 
# refusal=None, 
# role='assistant', 
# annotations=None, audio=None, function_call=None, tool_calls=None, 
# reasoning_content='Okay, the user greeted me and said, "Hello." I need to respond in a friendly and helpful manner. Let\'s start with a greeting and ask how I can assist them today. Keep it open-ended to encourage them to share their issue. Maybe something like, "Hello! How can I assist you today?" That should work.'))

import asyncio, os, json, sys, re
from contextlib import AsyncExitStack
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


load_dotenv()

SYS_PROMPT = (
    "You have three tools available to use: [list_tables], [describe_table], [query_table]. \n"
    "If the query requires you to use multiple tools, for instance, if the user wants to know the email of a specific user, \n"
    "you can use the [list_tables] tool to get the table name, then use the [describe_table] tool to get the column names, \n"
    "Then, use the [query_table] tool to grab the information you need. \n" 
    "Note: Only generate read-only SQL queries such as SELECT, SHOW, DESCRIBE, or EXPLAIN. \n"
    "Do not generate queries that modify the database, such as INSERT, UPDATE, DELETE, DROP, etc."
)

class MCPClient():

    def __init__(self) -> None:
        self.exit_stack = AsyncExitStack()
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")
        if not self.deepseek_api_key:
            raise ValueError("Can't find the API Key attribute, please edit it over the .env file")
        self.client = OpenAI(api_key=self.deepseek_api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None

    async def connect_to_server(self, path_to_script: str):
        cmd = "python" if path_to_script.endswith(".py") else "node"
        server_params = StdioServerParameters(command=cmd, args=[path_to_script])
        self.stdio, self.write = await self.exit_stack.enter_async_context(
            stdio_client(server_params))
        self.session: ClientSession = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write))
        await self.session.initialize()
        tools = (await self.session.list_tools()).tools
        self.tool_specs = [{
            "type":"function",
            "function":{
                "name":t.name,
                "description":t.description,
                "input_schema":t.inputSchema}}
            for t in tools]
        print("Successfully connected to the server and here's the tool list:", [t["function"]["name"] for t in self.tool_specs])
    
    async def process_query(self, query: str) -> str:
        messages = [{"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": query}]

        while True:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                tools = self.tool_specs,
            )

            choice = response.choices[0]
            if choice.finish_reason != "tool_calls":
                stream = self.client.chat.completions.create(
                    model = self.model,
                    messages = messages,
                    stream = True
                )
                print ("\nAI Model: ", end="", flush=True)                
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content is not None:
                        print (delta.content, end="", flush=True)
                print ()
                return 
            
            tool_messages = []
            for c in choice.message.tool_calls:
                args = json.loads(c.function.arguments)
                result = await self.session.call_tool(c.function.name, args)
                if not args:
                    print (f"\n Calling tool {c.function.name} with the arguments {args}\n")
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": c.id,
                    "content": result.content[0].text,
                })

                print (f"[Debug] Tool messages: {tool_messages}")
            messages.extend([choice.message.model_dump(), *tool_messages])

    async def chat_loop (self):
        print("Type 'quit' to exit: ")
        while True:
            q = input("\nUser: ").strip()
            if q.lower() == "quit":
                break
            await self.process_query(q)

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





