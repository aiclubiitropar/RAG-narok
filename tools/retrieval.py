import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

    # Return the combined results directly without reranking
    if not combined_results:
        return f"This is the query by the user '{query}'\nNo results were retrieved."

    return f"This is the query by the user '{query}'\nThese are the retrieved results from RAG: '{combined_results[0]}'"