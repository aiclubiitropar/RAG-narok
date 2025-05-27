import os
import re
import sys
# Ensure project root is in sys.path for module imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END, START
from agents.rag_analyser_agent import create_analyser_agent
from agents.llm import MainLLM
from vector_stores.L_vecdB import LongTermDatabase
from vector_stores.S_vecdB import ShortTermDatabase

# Initialize databases
long_db = LongTermDatabase()
short_db = ShortTermDatabase()

# Create the analyser agent
analyser_agent = create_analyser_agent(long_db, short_db)

# Initialize the main LLM
main_llm = MainLLM()

# Define the graph state
class RAGState(TypedDict):
    query: str
    refined_query: str
    final_output: str

class RAGGraph(StateGraph):
    def __init__(self):
        super().__init__(RAGState)
        self.final_response = None

        # 1) Analyzer node
        self.add_node(
            "Analyser",
            lambda state: {"refined_query": analyser_agent.run(input=state["query"])}
        )

        # 2) MainLLM node → returns raw response (object or string)
        def llm_node(state):
            return {"final_output": main_llm.generate_response(state["refined_query"])}
        self.add_node("MainLLM", llm_node)

        # 3) Extractor node → unwraps into final_output as string
        def extractor_node(state):
            resp = state["final_output"]
            text = getattr(resp, "content", resp)
            self.final_response = text  # Store final response for custom invoke
            return {"final_output": text}
        self.add_node("Extractor", extractor_node)

        # Wire up the edges
        self.add_edge(START, "Analyser")
        self.add_edge("Analyser", "MainLLM")
        self.add_edge("MainLLM", "Extractor")
        self.add_edge("Extractor", END)

    # Custom invoke to pull just the string out of the final state dict
    def invoke(self, state):
        result = super().invoke(state)
        # result is now {'query':…, 'refined_query':…, 'final_output': '…'}
        return result["final_output"]

    def final_invoked_response(self) -> str:
        """
        Extracts and returns the content inside the `content='...'` field 
        from a response string. If no content field is found, returns the original string.
        """
        response_str = self.final_response
        match = re.search(r"content=['\"](.*?)['\"]", response_str)
        return match.group(1) if match else response_str

# Example usage
if __name__ == "__main__":
    graph = RAGGraph()
    compiled = graph.compile()
    q = input("Enter your query: ")
    compiled.invoke({"query": q})
    print("Final Response:", graph.final_invoked_response())  # Should match the final_output
