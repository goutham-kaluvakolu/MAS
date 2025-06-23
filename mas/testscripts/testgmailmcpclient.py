import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from mcp_use import MCPAgent, MCPClient
import json

async def main():
    # Load environment variables
    load_dotenv()

    # Create configuration dictionary
    config = json.load(open("config.json"))

    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)

    # api_key = os.getenv("OPENAI_API_KEY")
    # print(api_key)

    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=30)

    # Run the query
    result = await agent.run(
        "get me the latest unread email from my gmail max of 3 , dont show me links",
    )
    print(f"\nResult: {result}")

if __name__ == "__main__":
    asyncio.run(main())