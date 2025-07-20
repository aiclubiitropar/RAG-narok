import os
import sys
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain_core.exceptions import OutputParserException
import time

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tools.retrieval import retrieval_tool_long, retrieval_tool_short
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
current_time = time.strftime('%A, %Y-%m-%d %H:%M:%S')

INSTRUCTIONS = (
        f"You are RAGnarok, IIT Ropar's AI assistant. Current time is: {current_time}.\n"
        "You were created by Iota Cluster 2025-26 (AI Club, IIT Ropar).\n"
        "Chat history: {chat_history}\n"
        "Use retrieval tools to verify facts before answering.\n"
        "Tools: retrieval_tool_long (archival), retrieval_tool_short (recent updates), google_search_tool (realtime info or fallback web search).\n"
        "When using retrieval tools, choose the minimal one-word query for best results.\n"
        "Always use retrieval_tool_long first, and if it does not provide sufficient information, then use retrieval_tool_short.\n"
)


# Initialize the LLM Agent with Tools, Memory, and Instructions
def wake_llm(longdb, shortdb, model = "deepseek-r1-distill-llama-70b", api_key=os.getenv("GROQ_API_KEY")):
    def retrieve_long(query):
        return retrieval_tool_long(query, longdb)
    def retrieve_short(query):
        return retrieval_tool_short(query, shortdb)

    tools = [
        Tool(
            name="retrieval_tool_long",
            func=retrieve_long,
            description="Use this tool to retrieve information from the IIT Ropar long-term (archival/static) database."
        ),
        Tool(
            name="retrieval_tool_short",
            func=retrieve_short,
            description="Use this tool to retrieve information from the IIT Ropar short-term (recent/emails) database."
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
        temperature=0.7,
        max_tokens=8192,
        top_p=0.95,
    )

    llm_agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        agent_kwargs = {
            "prefix": INSTRUCTIONS,
            "examples": [
                {
                    "input": "Who is the director of IIT Ropar?",
                    "thought": "Static fact → use retrieval_tool_long.",
                    "action": "retrieval_tool_long",
                    "action_input": "director IIT Ropar"
                },
                {
                    "input": "Any holidays this month?",
                    "thought": "Recent schedule → retrieval_tool_short.",
                    "action": "retrieval_tool_short",
                    "action_input": "holiday calendar"
                },
                {
                    "input": "What happened recently in IIT Ropar?",
                    "thought": "Real Time info & Fallback for retrieval tools → use google_search_tool.",
                    "action": "google_search_tool",
                    "action_input": "What happened recently in IIT Ropar?"
                },
                {
                    "input": "Hello!",
                    "thought": "Greeting → no tool needed.",
                    "action": "Final Answer",
                    "action_input": "Hi there! I'm RAGnarok—how can I help you today?"
                }
            ]
        },
        handle_parsing_errors=True,
        early_stopping_method="generate",
        max_iterations=3,
        max_time=3,
    )
    
    return llm_agent


# # Optional CLI Usage with Chat Loop
# if __name__ == "__main__":
#     # Initialize vector DBs for CLI testing
#     longdb = LongTermDatabase(collection_prefix="longterm_db")
#     shortdb = ShortTermDatabase(short_term_prefix="shortterm_db", long_term_prefix="longterm_db")
#     llm_agent = wake_llm(longdb, shortdb, api_key=os.getenv("GROQ_API_KEY"))
#     print("\n💬 RAGnarok is awake. Start chatting (type 'exit' to stop):\n")

#     while True:
#         query = input("\U0001F464 You: ")
#         if query.strip().lower() in {"exit", "quit"}:
#             print("\U0001F44B Goodbye!")
#             break
#         try:
#             response = llm_agent.invoke({
#                 "input": query,
#                 "current_time": time.strftime('%A, %Y-%m-%d %H:%M:%S')
#             })
#             if isinstance(response, dict) and "output" in response:
#                 print(f"\U0001F916 RAGnarok: {response['output']}")
#             else:
#                 print(f"\U0001F916 RAGnarok: {response}")
#             # Print chat history for testing
#             print("\n--- Chat History ---")
#             for msg in llm_agent.memory.chat_memory.messages:
#                 print(f"{msg.type.capitalize()}: {msg.content}")
#             print("--------------------\n")
#         except OutputParserException as e:
#             print("\n❌ Output Parsing Error:", e)
#             print("Raw LLM output:", getattr(e, "llm_output", "Not available"))
#         except Exception as e:
#             print("\n❌ Unexpected Error:", str(e))
