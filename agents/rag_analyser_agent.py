from langchain.agents import Tool, initialize_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
import sys
import os
import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.retrieval import retrieval_tool

# --- Google Search Tool (SerpAPI integration) ---
def google_search_tool(query):
    """
    Uses SerpAPI to perform a Google Search and return the top results as a string.
    Requires SERPAPI_API_KEY in environment variables.
    """
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        return '[Google Search Error: SERPAPI_API_KEY not set in environment]'
    url = "https://serpapi.com/search"
    params = {
        'q': query,
        'api_key': api_key,
        'engine': 'google',
        'num': 3
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get('organic_results', [])
        if not results:
            return '[Google Search: No results found]'
        out = []
        for r in results[:3]:
            title = r.get('title', '')
            link = r.get('link', '')
            snippet = r.get('snippet', '')
            out.append(f"- {title}\n{snippet}\n{link}")
        return '\n\n'.join(out)
    except Exception as e:
        return f'[Google Search Error: {str(e)}]'

# Define the RAG + Memory agent
def create_analyser_agent(long_db, short_db):
    """
    Create an agent with chat-history memory, that decides whether to use RAG, retrieves context, and generates a response.

    Args:
        long_db: The long-term database object.
        short_db: The short-term database object.

    Returns:
        AgentExecutor: The initialized agent.
    """
    # Initialize the LLM with system instructions
    llm = ChatGoogleGenerativeAI(
        api_key=os.getenv('GEMINI_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=256,
        system_instruction=(
            "You are the Analyser agent in the RAGnarok system for IIT Ropar. "
            "Your job is to take the user's prompt and decide whether to use retrieval-augmented generation (RAG) or not. "
            "If extra context is needed, use the retrieval tools or Google search tools to refine the user prompt and pass the refined prompt to RAGnarok. "
            "If RAG or extra context is not needed, strictly pass the same prompt to RAGnarok directly without modification."
            "Remember the user prompt is not for you to answer directly, but to pass to RAGnarok for final response generation. "
            "Focus on maximizing relevance to the query and clarity for the user."
        )
    )

    # Set up conversational memory to store chat history
    memory = ConversationBufferMemory(
        memory_key="chat_history",  # key in inputs for memory
        return_messages=True  # passages include full message history
    )

    # Define tools for RAG and web search
    def retrieval_tool_wrapper(query=None, input=None):
        actual_query = input or query
        return retrieval_tool(actual_query, long_db, short_db)

    def google_search_tool_wrapper(query=None, input=None):
        actual_query = input or query
        return google_search_tool(actual_query)

    tools = [
        Tool(
            name="retrieval_tool",
            func=retrieval_tool_wrapper,
            description="Retrieve context from long and short-term databases."
        ),
        Tool(
            name="google_search_tool",
            func=google_search_tool_wrapper,
            description="Perform a Google search when databases lack sufficient info."
        )
    ]

    # Initialize the agent with memory
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent="zero-shot-react-description",
        memory=memory,
        verbose=True
    )

    return agent

# Example usage
if __name__ == "__main__":
    from vector_stores.L_vecdB import LongTermDatabase
    from vector_stores.S_vecdB import ShortTermDatabase

    # Initialize databases
    long_db = LongTermDatabase()
    short_db = ShortTermDatabase()

    # Create the RAG+Memory agent
    agent = create_analyser_agent(long_db, short_db)

    while True:
        user_query = input("Enter your query (or 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break
        response = agent.run(user_query)
        print("Response:", response)
