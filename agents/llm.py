from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiLLM:
    def __init__(self, api_key=os.getenv('GEMINI_API_KEY'), model="gemini-2.0-flash", temperature=0.7, max_tokens=256, system_instructions="You are a helpful assistant."):
        """
        Initialize the Gemini 2.0 Flash model using LangChain.
        :param api_key: API key for authentication.
        :param model: Name of the Gemini model.
        :param temperature: Sampling temperature for randomness.
        :param max_tokens: Maximum number of tokens to generate.
        :param system_instructions: Instructions for the assistant's behavior.
        """
        self.llm = ChatGoogleGenerativeAI(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)
        self.prompt_template = PromptTemplate(
            input_variables=["query"],
            template=f"{system_instructions} Answer the following query: {{query}}"
        )

    def generate_response(self, query):
        """
        Generate a response using the Gemini 2.0 Flash model.
        :param query: The input query.
        :return: The generated response.
        """
        prompt = self.prompt_template.format(query=query)
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)
        return response

class MainLLM:
    def __init__(self, api_key=os.getenv('GEMINI_API_KEY'), model="gemini-2.0-flash", temperature=0.7, max_tokens=256, system_instructions="You are a helpful assistant."):
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
        self.memory.save_context({"query": query}, {"response": response})
        return response

# Example usage
if __name__ == "__main__":
    gemini_llm = GeminiLLM()

    query = "hi"
    response = gemini_llm.generate_response(query)
    print("Gemini 2.0 Flash Model Response:", response)
    print((response['content'] if isinstance(response, dict) else response).strip())