from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

class MainLLM:
    def __init__(self, api_key=os.getenv('GEMINI_API_KEY'), model="gemini-2.0-flash", temperature=0.7, max_tokens=256, system_instructions="You are RAGnarok, an AI assistant that helps students of IIT Ropar to know about IIT Ropar. Answer queries about campus life, academics, events, and more in a helpful, concise, and friendly manner."):
        """
        Initialize the MainLLM with chat history and memory capabilities.
        :param api_key: API key for authentication.
        :param model: Name of the Gemini model.
        :param temperature: Sampling temperature for randomness.
        :param max_tokens: Maximum number of tokens to generate.
        :param system_instructions: Instructions for the assistant's behavior.
        """
        self.llm = ChatGoogleGenerativeAI(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)
        self.prompt_template = PromptTemplate(
            input_variables=["history", "query"],
            template=f"{system_instructions} Here is the conversation history: {{history}}. Answer the following query: {{query}}"
        )
        self.memory = ConversationBufferMemory(memory_key="history")

    def generate_response(self, query):
        """
        Generate a response using the MainLLM with memory.
        :param query: The input query.
        :return: The generated response.
        """
        history = self.memory.load_memory_variables({}).get("history", "")
        prompt = self.prompt_template.format(history=history, query=query)
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        # If response is a dict with 'content', extract it
        if isinstance(response, dict) and 'content' in response:
            response_content = response['content']
        # If response is a list of dicts, join their 'content'
        elif isinstance(response, list):
            response_content = " ".join([r['content'] if isinstance(r, dict) and 'content' in r else str(r) for r in response])
        else:
            response_content = str(response)
        self.memory.save_context({"query": query}, {"response": response_content})
        return response_content
