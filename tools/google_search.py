import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- Google Search Tool (SerpAPI integration) ---
def google_search2(query):
    """
    Uses Zenserp API to perform a Google Search and return the top results as a string.
    This is a fallback if SerpAPI is not available.
    """
    headers = {
        "apikey": os.getenv('ZEN_API_KEY')
    }
    params = {
        "q": query,
        "num": 3
    }
    try:
        response = requests.get('https://app.zenserp.com/api/v2/search', headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('organic', [])
        if not results:
            return '[Zenserp Search: No results found]'
        out = []
        for r in results[:3]:
            title = r.get('title', '')
            link = r.get('url', '')
            snippet = r.get('description', '')
            out.append(f"- {title}\n{snippet}\n{link}")
        return '\n\n'.join(out)
    except Exception as e:
        return f'[Zenserp Search Error: {str(e)}]'

def google_search3(query):
    """
    Uses Google Custom Search API to perform a Google Search and return the top results as a string.
    Requires GOOGLE_SEARCH_ENGINE_API_KEY and GOOGLE_SEARCH_ENGINE_ID in environment variables.
    """
    api_key = os.getenv('GOOGLE_SEARCH_ENGINE_API_KEY')
    search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    if not api_key or not search_engine_id:
        return '[Google Custom Search API: Missing API key or Search Engine ID]'

    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get('items', [])
        if not results:
            return '[Google Custom Search API: No results found]'
        out = []
        for item in results[:3]:
            title = item.get('title', '')
            link = item.get('link', '')
            snippet = item.get('snippet', '')
            out.append(f"- {title}\n{snippet}\n{link}")
        return '\n\n'.join(out)
    except Exception as e:
        return f'[Google Custom Search API Error: {str(e)}]'

def google_search_tool(query):
    """
    Uses SerpAPI to perform a Google Search and return the top results as a string.
    Falls back to Zenserp and then Google Custom Search API if not available.
    """
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        # Fallback to Zenserp
        zenserp_result = google_search2(query)
        if "Zenserp Search Error" in zenserp_result or "No results found" in zenserp_result:
            # Fallback to Google Custom Search API
            return google_search3(query)
        return zenserp_result

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
        # Fallback to Zenserp on error
        zenserp_result = google_search2(query)
        if "Zenserp Search Error" in zenserp_result or "No results found" in zenserp_result:
            # Fallback to Google Custom Search API
            return google_search3(query)
        return zenserp_result

if __name__ == "__main__":
    query = input("Enter your search query: ")
    print("\nZenserp Results:\n")
    print(google_search_tool(query))

