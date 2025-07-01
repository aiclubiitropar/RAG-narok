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

    # Use correct argument name for both DBs
    long_results = long_db.smart_query(query, topk=10)
    short_results = short_db.smart_query(query, topk=10)

    # Combine and deduplicate results from both DBs
    combined = []
    seen = set()
    for res in long_results + short_results:
        if res not in seen:
            combined.append(res)
            seen.add(res)
    output_lines = [f"This is the query by the user: '{query}'"]
    if combined:
        output_lines.extend([f"{i+1}. {res}" for i, res in enumerate(combined)])
    else:
        output_lines.append("No results found.")
    return "\n".join(output_lines)


if __name__ == "__main__":
    # Import from vector_stores submodule for direct script execution
    from vector_stores.L_vecdB import LongTermDatabase
    from vector_stores.S_vecdB import ShortTermDatabase
    query = input("Enter your query: ")
    long_db = LongTermDatabase()
    short_db = ShortTermDatabase()
    results = retrieval_tool(query, long_db, short_db)
    print(results)