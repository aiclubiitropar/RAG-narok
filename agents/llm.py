import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferMemory
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # Add the RAG-narok directory to the Python path
from tools.retrieval import retrieval_tool
from tools.google_search import google_search_tool
from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
from dotenv import load_dotenv
from chromadb.config import Settings
# Load environment variables from .env file
load_dotenv()

longdb = LongTermDatabase(persist_directory="longterm_db")
shortdb = ShortTermDatabase(client_settings=Settings(persist_directory="shortterm_db"))

def wake_llm(longdb, shortdb, api_key = os.getenv("GEMINI_API_KEY")):
    
    system_ins = (
        "You are RAGnarok, a chatbot for IIT Ropar. Introduce yourself as RAGnarok, the official AI assistant of IIT Ropar, when asked about your identity. "
        "If the user greets you, asks who you are, or asks about yourself, respond directly as RAGnarok without using any tools. "
        "You have access to the full chat history and your system instructions at all times. Use them to provide context-aware, helpful, and consistent responses. "
        "Always respond with a valid JSON object containing a single action and its parameters. "
        "If you need to respond directly without using tools, include a 'response' key in the JSON object with your reply. "
        "Use the following tools when necessary: retrieval_tool, google_search_tool. "
        "Never reformulate or change the user's query. Always use the exact user input as the tool input. "
        "If you cannot perform the action, respond with a JSON object containing an 'error' key and a message explaining why the action could not be performed. "
        "Never respond with incomplete or ambiguous information. Ensure your responses are clear, concise, and actionable. "
    )
    gemini_llm = ChatGoogleGenerativeAI(api_key=api_key, model="gemini-2.0-flash")
    
    def retrieve_rag(query):
        return retrieval_tool(query, longdb, shortdb)
    
    tools = [
        Tool(
            name="retrieval_tool",
            func=retrieve_rag,
            description="Use this tool to retrieve information from the IIT Ropar databases."
        ),
        Tool(
            name="google_search_tool",
            func=google_search_tool,
            description="Use this tool to google search only if you don't find relevant information in the IIT Ropar databases."
        )
    ]
    
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    llm_agent = initialize_agent(
        tools=tools,
        llm=gemini_llm,
        agent_type="chat-zero-shot-react-description",
        verbose=True,
        system_instructions=system_ins,
        handle_parsing_errors=True,
        early_stopping_method="generate",
        max_iterations=2,
        max_time=10,
        memory=memory
    )
    
    return llm_agent


if __name__ == "__main__":
    # Example usage
    api_key = os.getenv("GEMINI_API_KEY")
    llm_agent = wake_llm(longdb, shortdb, api_key)
    query = input("Enter your query: ")
    response = llm_agent.invoke({"input": query})
    if response:
        try:
            if isinstance(response, dict) and "response" in response:
                print(response["response"])
            else:
                print("No valid response found.")
        except Exception as e:
            print(f"Error processing response: {e}")
    else:
        print("Empty response received from the LLM agent.")