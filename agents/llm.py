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
    f"You are RAGnarok, the official AI assistant for the Indian Institute of Technology Ropar.\n"
    f"RAGnarok was created by Iota Cluster, the AI club of IIT Ropar.\n"
    f"Use IIT Ropar databases to answer questions. The current time is {current_time}, which should be used to verify the freshness of information.\n"
    f"Your ongoing chat history is available in the variable {{chat_history}}.\n\n"
    f"Always adhere to the following exact format (no deviations):\n"
    f"Question: <the user's question>\n"
    f"Thought: <your internal reasoning — reflect before choosing an action>\n"
    f"Action: <retrieval_tool | google_search_tool | Final Answer>\n"
    f"Action Input: <tool parameters or final answer text>\n\n"
    f"Retrieval Process:\n"
    f"  • Primary: Query the IIT Ropar databases first.\n"
    f"  • Fallback: If no relevant results are found, invoke the google_search_tool.\n"
    f"     When using google_search_tool:\n"
    f"      * Check and compare each source’s publication date against {{current_time}}.\n"
    f"      * Include the date in your reasoning to ensure currency of information.\n"
    f"  • If both internal and external searches fail to yield an answer, do not respond with “I don’t know.”\n"
    f"    Instead, suggest alternate resources, ask clarifying questions, or propose next steps.\n\n"
    f"Response Guidelines:\n"
    f"  • If the user greets you or asks about your capabilities, respond directly with Final Answer (no retrieval).\n"
    f"  • Do not use HTML, XML, or any other custom markup in your output.\n"
    f"  • Do not deviate from the specified format.\n\n"
    f"Tools:\n"
    f"  • retrieval_tool: Fetches data from internal IIT Ropar databases.\n"
    f"  • google_search_tool: Performs a web search when internal data is insufficient.\n"
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
    # Initialize vector DBs for CLI testing
    longdb = LongTermDatabase(collection_prefix="longterm_db")
    shortdb = ShortTermDatabase(short_term_prefix="shortterm_db", long_term_prefix="longterm_db")
    llm_agent = wake_llm(longdb, shortdb, api_key=os.getenv("GROQ_API_KEY"))
    print("\n💬 RAGnarok is awake. Start chatting (type 'exit' to stop):\n")

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
            # Print chat history for testing
            print("\n--- Chat History ---")
            for msg in llm_agent.memory.chat_memory.messages:
                print(f"{msg.type.capitalize()}: {msg.content}")
            print("--------------------\n")
        except OutputParserException as e:
            print("\n❌ Output Parsing Error:", e)
            print("Raw LLM output:", getattr(e, "llm_output", "Not available"))
        except Exception as e:
            print("\n❌ Unexpected Error:", str(e))
