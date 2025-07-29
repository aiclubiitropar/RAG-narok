import sys
import os
from dotenv import load_dotenv
from chromadb.config import Settings
from datetime import datetime
from pytz import timezone

# Set up environment and paths
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from project structure
from agents.llm import wake_llm
from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase
from langchain_core.exceptions import OutputParserException


# # Initialize vector DBs
# longdb = LongTermDatabase(persist_directory="longterm_db")
# shortdb = ShortTermDatabase(client_settings=Settings(persist_directory="shortterm_db"))


class RAGnarok:
    def __init__(self, longdb, shortdb, model="deepseek-r1-distill-llama-70b"):
        self.llm_agent = wake_llm(longdb, shortdb, model=model)

    def invoke(self, query: str) -> str:
        try:
            current_time = datetime.now(timezone('Asia/Kolkata')).strftime('%A, %Y-%m-%d %H:%M:%S')
            # Combine current_time into the input key
            response = self.llm_agent.invoke({"input": f"{query} (Current time: {current_time})"})

            # Response could be a string or a dict
            if isinstance(response, dict):
                if "output" in response:
                    return response["output"]
                return str(response)
            return str(response)

        except OutputParserException as e:
            raw_output = getattr(e, "llm_output", "Unavailable")
            return f"[❌ Parsing Error] {str(e)}\n[Raw Output]: {raw_output}"

        except Exception as e:
            return f"[❌ Error] {str(e)}"


if __name__ == "__main__":
    # CLI interface
    ragnarok = RAGnarok(longdb, shortdb)
    query = input("Enter your query: ")
    response = ragnarok.invoke(query)

    print("\n🧠 RAGnarok Response:")
    print(response)
    print("\n--- End of Response ---")
