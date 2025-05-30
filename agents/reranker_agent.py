from langchain.agents import Tool, initialize_agent
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Define the Reranker Agent
def create_reranker_agent():
    """
    Create an agent to rerank retrieved information and return the most relevant results.

    Returns:
        AgentExecutor: The initialized reranker agent.
    """
    # Initialize the LLM with system instructions
    llm = ChatGoogleGenerativeAI(
        api_key=os.getenv('GEMINI_API_KEY'),
        model="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=256,
        system_instruction=(
            "You are the Reranker agent in the RAGnarok system for IIT Ropar. "
            "Your job is to rerank the retrieved information based on the user's query and return the most relevant results. "
            "Focus on maximizing relevance to the query and clarity for the user."
            "Do not answer the query directly, but return the reranked information only."
        )
    )

    # Define the reranking prompt template
    rerank_prompt_template = PromptTemplate(
        input_variables=["retrieved_info", "input"],
        template="You are an intelligent assistant. Based on the following query: {input}, rerank the retrieved information to return the most relevant results: {retrieved_info}"
    )

    # Define the reranking tool
    def rerank_tool(inputs):
        # Accept a single dict input for LangChain compatibility
        retrieved_info = inputs.get("retrieved_info", "")
        query = inputs.get("input", "")
        prompt = rerank_prompt_template.format(retrieved_info=retrieved_info, input=query)
        response = llm.invoke([prompt])[0]
        return response

    rerank_tool_instance = Tool(
        name="rerank_tool",
        func=rerank_tool,
        description="Use this tool to rerank retrieved information and return the most relevant results."
    )

    # Initialize the agent
    agent = initialize_agent(
        tools=[rerank_tool_instance],
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True
    )

    return agent

