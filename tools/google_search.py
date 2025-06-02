import requests
import os
from dotenv import load_dotenv

load_dotenv()

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