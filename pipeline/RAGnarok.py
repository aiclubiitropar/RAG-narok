import sys
import os
from dotenv import load_dotenv
# from chromadb.config import Settings

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
    def __init__(self, longdb, shortdb):
        self.llm_agent = wake_llm(longdb, shortdb)

    def invoke(self, query: str) -> str:
        try:
            response = self.llm_agent.invoke({"input": query})

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
