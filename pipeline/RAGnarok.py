import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))  # Add the RAG-narok directory to the Python path

from agents.llm import wake_llm
from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
from dotenv import load_dotenv  # Load environment variables from .env file 
load_dotenv()
from chromadb.config import Settings

longdb = LongTermDatabase(persist_directory="longterm_db")
shortdb = ShortTermDatabase(client_settings=Settings(persist_directory="shortterm_db"))

class RAGnarok:
    def __init__(self,longdb, shortdb):
        self.llm_agent = wake_llm(longdb, shortdb)
        self.system_ins = (
            "You are RAGnarok, a chatbot for IIT Ropar. Introduce yourself as RAGnarok, the official AI assistant of IIT Ropar, when asked about your identity. "
            "If the user greets you, asks who you are, or asks about yourself, respond directly as RAGnarok without using any tools. "
            "You have access to the full chat history and your system instructions at all times. Use them to provide context-aware, helpful, and consistent responses. "
            "Always refer to the provided chat history to inform your answers and maintain context. "
            "Always respond with a valid JSON object containing a single action and its parameters. "
            "If you need to respond directly without using tools, include a 'response' key in the JSON object with your reply. "
            "Use the following tools when necessary: retrieval_tool, google_search_tool. "
            "Never reformulate or change the user's query. Always use the exact user input as the tool input. "
            "If you cannot perform the action, respond with a JSON object containing an 'error' key and a message explaining why the action could not be performed. "
            "Never respond with incomplete or ambiguous information. Ensure your responses are clear, concise, and actionable. "
        )
        self.last_response = None  # Store the last response
        self.history = []  # Initialize history

    def invoke(self, query):
        try:
            # Prepare chat history string
            history_str = f"This is the chat history, refer to this if you feel the question is incomplete: '{self.history}'\n"
            response = self.llm_agent.invoke({"input": f"These are your System instructions: '{self.system_ins}'\n{history_str}Now answer the user query: '{query}'"})
            print(f"Raw response from LLM: {response['output']}")
            # Try to parse as JSON first, but handle multiple JSON objects or extra text
            try:
                import re
                matches = re.findall(r'\{[^\{\}]*"response"[^\{\}]*\}', response['output'])
                if matches:
                    output = json.loads(matches[-1])
                    print(f"Parsed output: {output.get('response', 'No response key found')}")
                    self.last_response = response
                    self.history.append({"query": query, "response": output.get("response", "No response key found in the output.")})
                    return output.get("response", "No response key found in the output.")
                # Fallback: try to load the whole output
                output = json.loads(response['output'])
                print(f"Parsed output: {output.get('response', 'No response key found')}")
                self.last_response = response
                self.history.append({"query": query, "response": output.get("response", "No response key found in the output.")})
                return output.get("response", "No response key found in the output.")
            except Exception:
                # If not JSON, return the raw output as a direct response
                self.last_response = response
                self.history.append({"query": query, "response": response['output']})
                return response['output']
        except Exception as e:
            print(f"Error during invocation: {e}")
            if self.last_response and 'output' in self.last_response:
                try:
                    print(f"Using last valid response: {self.last_response['output']}")
                    prev_output = json.loads(self.last_response['output'])
                    self.history.append({"query": query, "response": prev_output.get("response", "No response key found in the output.")})
                    return prev_output.get("response", "No response key found in the output.")
                except Exception:
                    self.history.append({"query": query, "response": self.last_response['output']})
                    return self.last_response['output']
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage
    ragnarok = RAGnarok(longdb, shortdb)
    query = input("Enter your query: ")
    response = ragnarok.invoke(query)
    print(response)  # Print the response from the RAGnarok agent