from gradio_client import Client

def summarize_text(text):
    """
    Summarizes the given text using the IotaCluster/Summarizer Gradio API (new endpoint).
    Args:
        text (str): The text to summarize.
    Returns:
        str: The summarized text from the API.
    """
    client = Client("IotaCluster/Summarizer")
    result = client.predict(
        text=text,
        api_name="/predict"
    )
    return result

# Example usage
if __name__ == "__main__":
    summary = summarize_text("Hello!!")
    print(summary)
    
