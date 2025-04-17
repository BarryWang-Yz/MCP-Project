import asyncio
import os
from openai import OpenAI
from dotenv import load_dotenv
from contextlib import AsyncExitStack

load_dotenv()

class MCPClient: 
    def __init__(self):
        # MCP client initialization
        self.exit_stack = AsyncExitStack() 
        self.openai_api_key = os.getenv("DEEPSEEK_API_KEY")
        # print(f"api key:", self.openai_api_key)
        self.base_url = os.getenv("BASE_URL")
        # print(f"base url:", self.base_url)
        self.model = os.getenv("MODEL")

        if not self.openai_api_key:
            raise ValueError("Can't find the API Key attribute, please edit it over the .env file")
        
        self.client = OpenAI(api_key=self.openai_api_key, base_url=self.base_url)

    async def process_query(self, query: str) -> str:
        messages = [{"role": "system", "content": "You are an AI chat box to help user resolve their issue."},
                    {"role": "user", "content": query}]
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            )

            # print ("response.choices[1]: ", response.choices[1])
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Got the error when call the DeepSeek API : {str(e)}"

    # async def connect_to_mock_server(self):
    #     print("MCP client has already initialized, but didn't connect to the server.")

    async def chat_loop(self):
        print(f"\n MCP client has already started, press 'quit' to exist")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print(f"\n DeepSeek R1: {response}")
            
            except Exception as e:
                print(f"\n Encounter error message: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()

async def main():
    client = MCPClient()
    try:
        # await client.connect_to_mock_server()
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())