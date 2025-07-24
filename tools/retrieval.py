import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def retrieval_tool_long(query, long_db):
    """
    Retrieves results by querying only the long-term database.
    Args:
        query (str): The input query.
        long_db (LongTermDatabase): The long database object to query.
    Returns:
        str: Formatted results from the long-term database.
    """
    query = query.split()[0]  # Use only the first word of the query
    long_results = long_db.smart_query(query, topk=15, top_l=10, use_late=True, doc_search=True)
    max_context_tokens = 1024
    max_context_chars = max_context_tokens * 4
    total_chars = 0
    limited = []
    for res in long_results:
        if total_chars + len(res) > max_context_chars:
            break
        limited.append(res)
        total_chars += len(res)
    output_lines = [f"This is the query by the user: '{query}' (Long-term DB)"]
    if limited:
        output_lines.extend([f"{i+1}. {res}" for i, res in enumerate(limited)])
    else:
        output_lines.append("No results found.")
    return "\n".join(output_lines)

def retrieval_tool_short(query, short_db):
    """
    Retrieves results by querying only the short-term database.
    Args:
        query (str): The input query.
        short_db (ShortTermDatabase): The short database object to query.
    Returns:
        str: Formatted results from the short-term database.
    """
    query = query.split()[0]  # Use only the first word of the query
    short_results = short_db.smart_query(query, topk=15, top_l=10, use_late=True, doc_search=True)
    max_context_tokens = 1024 
    max_context_chars = max_context_tokens * 4
    total_chars = 0
    limited = []
    for res in short_results:
        if total_chars + len(res) > max_context_chars:
            break
        limited.append(res)
        total_chars += len(res)
    output_lines = [f"This is the query by the user: '{query}' (Short-term DB)"]
    if limited:
        output_lines.extend([f"{i+1}. {res}" for i, res in enumerate(limited)])
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
