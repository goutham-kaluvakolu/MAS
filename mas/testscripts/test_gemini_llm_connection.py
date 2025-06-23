import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables from .env file (must be at the very top)
load_dotenv()

# Ensure the GOOGLE_API_KEY environment variable is set
if "GOOGLE_API_KEY" not in os.environ:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    print("Please set it before running this script.")
    print("You can add it to your system's environment variables or set it directly in the script (temporarily for testing).")
    exit()

try:
    # Initialize your LLM
    # Use the model you intend to use in your LangGraph agent
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

    print(f"Successfully initialized LLM using model: gemini-2.5-flash")


    # Test a simple invocation
    print("\n--- Testing LLM invocation ---")
    messages = [
        SystemMessage("You are a helpful AI assistant."),
        HumanMessage("What is the capital of France?"),
    ]

    response = llm.invoke(messages)
    print("LLM Response:")
    print(response.content)

    # You can also try streaming
    print("\n--- Testing LLM streaming (optional) ---")
    stream_messages = [
        HumanMessage("Tell me a short story about a brave knight."),
    ]
    print("Streaming Response:")
    for chunk in llm.stream(stream_messages):
        print(chunk.content, end="", flush=True)
    print("\n")

    print("\nLLM connection test successful!")

except Exception as e:
    print(f"\nError connecting to or invoking LLM: {e}")
    print("Please check your GOOGLE_API_KEY, network connection, and model availability.")