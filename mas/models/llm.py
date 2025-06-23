from langchain_openai import ChatOpenAI
import os # Good practice to get API key from environment variables
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define the LLM instance directly in the module
# It will be initialized only once when the module is first imported
llm_instance = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_APIKEY") # Better: get from environment
)

def get_llm():
    """Provides access to the shared LLM instance."""
    return llm_instance

# You could also add other functions related to LLM interaction here
