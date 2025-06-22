import os
import sys
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from chromadb.config import Settings
from langchain_core.exceptions import OutputParserException
import time

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.retrieval import retrieval_tool
from tools.google_search import google_search_tool
from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
# Load environment variables
load_dotenv()

# Note: Embedding logic is now handled internally in LongTermDatabase and ShortTermDatabase using get_embedding API.
# Do not pass or set any model/embedding function when initializing these classes.

# Initialize vector DBs
# longdb = LongTermDatabase(persist_directory="longterm_db")
# shortdb = ShortTermDatabase(client_settings=Settings(persist_directory="shortterm_db"))

# Inject current day, date, and time into instructions
current_time = time.strftime('%A, %Y-%m-%d %H:%M:%S')
INSTRUCTIONS = (
    f"You are RAGnarok, the official AI assistant of IIT Ropar.\n"
    f"Answer questions using the IIT Ropar databases and also this is the current time {current_time} for latest information.\n"
    "Here is the chat history so far:\n{chat_history}\n"
    "Use this exact format:\n"
    "Question: <user's question>\n"
    "Thought: <your internal reasoning>, after thinking only only return final answer\n"
    "Action: <retrieval_tool | google_search_tool | Final Answer>\n"
    "Action Input: <input to the tool OR response if using Final Answer>\n"
    "Never use HTML, XML, or other tags. Never invent new formats.\n"
    "If asked about yourself or greeted, respond directly with Final Answer.\n"
)

# Initialize the LLM Agent with Tools, Memory, and Instructions
def wake_llm(longdb, shortdb, model = "deepseek-r1-distill-llama-70b", api_key=os.getenv("GROQ_API_KEY")):
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
            description="Use this tool to Google search if IIT Ropar database has no relevant information."
        )
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )

    llm = ChatGroq(
        groq_api_key=api_key,
        model_name=model,
        temperature=0.6,
        max_tokens=4096,
        top_p=0.95,
    )

    llm_agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        agent_kwargs={"prefix": INSTRUCTIONS},
        handle_parsing_errors=True,
        early_stopping_method="generate",
        max_iterations=2,
        max_time=10,
    )
    
    return llm_agent


# Optional CLI Usage with Chat Loop
if __name__ == "__main__":
    llm_agent = wake_llm(longdb, shortdb, api_key=os.getenv("GROQ_API_KEY"))
    print("💬 RAGnarok is awake. Start chatting (type 'exit' to stop):\n")

    while True:
        query = input("👤 You: ")
        if query.strip().lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break
        try:
            response = llm_agent.invoke({"input": query})
            if isinstance(response, dict) and "output" in response:
                print(f"🤖 RAGnarok: {response['output']}")
            else:
                print(f"🤖 RAGnarok: {response}")
        except OutputParserException as e:
            print("\n❌ Output Parsing Error:", e)
            print("Raw LLM output:", getattr(e, "llm_output", "Not available"))
        except Exception as e:
            print("\n❌ Unexpected Error:", str(e))