from gradio_client import Client
import uuid

# Point to your deployed Gradio app
client = Client("IotaCluster/embedding-model")


def get_dense_embedding(text: str):
    """Calls the /embed_dense endpoint (MiniLM)."""
    return _call_api(text, api_name="/embed_dense")


def get_sparse_embedding(text: str):
    """Calls the /embed_sparse endpoint (BM25)."""
    return _call_api(text, api_name="/embed_sparse")


def get_late_embedding(text: str):
    """Calls the /embed_colbert endpoint (ColBERT late-interaction)."""
    return _call_api(text, api_name="/embed_colbert")


def _call_api(text: str, api_name: str):
    try:
        result = client.predict(
            text=text,
            api_name=api_name
        )
        # Normalize response: return the first value in the dict or the list itself
        if isinstance(result, dict):
            return next(iter(result.values()))
        elif isinstance(result, list):
            return result
        else:
            print(f"Unexpected response from {api_name!r}:", result)
            return None
    except Exception as e:
        print(f"API request to {api_name!r} failed:", e)
        return None

def to_valid_qdrant_id(id_val):
    """Ensures the ID is a valid UUID (for Qdrant)."""
    try:
        return str(uuid.UUID(str(id_val)))
    except Exception:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_val)))

if __name__ == "__main__":
    text = "Hello!!"

    # dense = get_dense_embedding(text)
    # print("Dense embedding:", dense)
    # print("Length:", len(dense) if dense else None)

    # sparse = get_sparse_embedding(text)
    # print("\nSparse term-weights:", sparse)

    late = get_late_embedding(text)
    print("\nLate-interaction (ColBERT) embeddings:", late)
    print("Tokens count:", len(late) if isinstance(late, list) else None)
