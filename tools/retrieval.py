import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.reranker_agent import create_reranker_agent

def retrieval_tool(query, long_db, short_db):
    """
    Retrieves results by querying the long database and short database, then concatenates and reranks the outputs.

    Args:
        query (str): The input query.
        long_db (LongTermDatabase): The long database object to query.
        short_db (ShortTermDatabase): The short database object to query.

    Returns:
        list: Reranked results from both databases.
    """
    # Query the long database using its smart_query method
    long_results = long_db.smart_query(query)

    # Query the short database using its smart_query method
    short_results = short_db.smart_query(query)

    # Concatenate results
    combined_results = long_results + short_results
    combined_results_str = '\n'.join(str(item) for item in combined_results)
    # Validate input format for reranker_agent
    if not isinstance(combined_results_str, str) or not isinstance(query, str):
        raise ValueError("Invalid input format: 'retrieved_info' and 'input' must be strings.")

    # Rerank the combined results using the reranker agent
    reranker_agent = create_reranker_agent()
    reranker_input = {
        "retrieved_info": combined_results_str,
        "input": query
    }

    # Debugging log to check the input structure
    print(f"Input to reranker_agent.run: {reranker_input}")

    # Invoke the reranker agent
    try:
        reranked_results = reranker_agent.invoke(reranker_input)
    except ValueError as e:
        return f"Error during reranking: {str(e)}"

    # Validate reranked_results
    if not isinstance(reranked_results, list) or len(reranked_results) == 0:
        return f"This is the query by the user '{query}'\nNo results were retrieved or reranked."

    # Return the refined query (first result from reranked results) concatenated with the original query
    return f"This is the query by the user '{query}'\nThese are the retrieved results from RAG:'{reranked_results[0]}'"