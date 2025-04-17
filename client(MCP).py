# response.choices[0]:  Choice(finish_reason='stop', 
# index=0, logprobs=None, 
# message=ChatCompletionMessage(content='Hello! How can I assist you today? 😊', 
# refusal=None, 
# role='assistant', 
# annotations=None, audio=None, function_call=None, tool_calls=None, 
# reasoning_content='Okay, the user greeted me and said, "Hello." I need to respond in a friendly and helpful manner. Let\'s start with a greeting and ask how I can assist them today. Keep it open-ended to encourage them to share their issue. Maybe something like, "Hello! How can I assist you today?" That should work.'))

import asyncio
import os
import json
import sys
from typing import Optional
from contextlib import AsyncExitStack

from openai import OpenAI
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

class MCPClient():

    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.model = os.getenv("MODEL")
        if not self.deepseek_api_key:
            raise ValueError("Can't find the API Key attribute, please edit it over the .env file")
        self.client = OpenAI(api_key=self.deepseek_api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None

    async def connect_to_server(self, path_to_script: str):
        is_python = path_to_script.endswith('py')
        is_js = path_to_script.endswith('js')

        if not (is_python or is_js):
            raise ValueError(f"The type of the script should be exactly the .py and .js")
        
        command = "python" if is_python else "node"

        server_params = StdioServerParameters (
            command = command,
            args = [path_to_script],
            env = None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        response = await self.session.list_tools()
        tools = response.tools

        print("Successfully connecting to the server and here's the tool list", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        messages = [{"role": "user", "content": query}]

        response = await self.session.list_tools()

        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } 
        } for tool in response.tools]

        # print(f"available_tools: ", available_tools)

        response = self.client.chat.completions.create (
            model = self.model,
            messages = messages,
            tools = available_tools
        )

        content = response.choices[0]
        print (f"[Debug] content: {content}")

        if content.finish_reason == "tool_calls":
            tool_messages = []

            for tool_call in content.message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments) 
                result = await self.session.call_tool(tool_name, tool_args)
                print(f"\n\n Calling tool {tool_name} with arguments {tool_args}\n\n")

                tool_messages.append ({
                    "role": "tool",
                    "content": result.content[0].text,
                    "tool_call_id": tool_call.id,
                })

            messages.append(content.message.model_dump())
            messages.extend(tool_messages)
            
            if "location" in tool_args:
                tool_args["city"] = tool_args.pop("location")

            # result = await self.session.call_tool(tool_name, tool_args)
            

            # messages.append(content.message.model_dump())
            # messages.append({
            #     "role": "tool",
            #     "content": result.content[0].text,
            #     "tool_call_id": tool_call.id,
            # })

            response = self.client.chat.completions.create (
                model = self.model,
                messages = messages,
            )
            return response.choices[0].message.content
        
        return content.message.content

    async def chat_loop (self):
        print(f"\n MCP client has already started, press 'quit' to exist")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print ("\nDeepSeek R1: ", response)

            except Exception as e:
                print(f"Ecounter Error message: {str(e)}")

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





