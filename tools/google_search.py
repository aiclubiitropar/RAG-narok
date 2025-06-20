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

def google_search_tool(query):
    """
    Uses SerpAPI to perform a Google Search and return the top results as a string.
    Requires SERPAPI_API_KEY in environment variables.
    Falls back to Zenserp if not available.
    """
    api_key = os.getenv('SERPAPI_API_KEY')
    if not api_key:
        # Fallback to Zenserp
        return google_search2(query)
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
        return google_search2(query)