from gradio_client import Client
import uuid

client = Client("IotaCluster/embedding-model")

def get_embedding(text):
    try:
        result = client.predict(
            text=text,
            api_name="/predict"
        )
        # Expecting result to be a dict with 'embedding' key or a list
        if isinstance(result, dict) and 'embedding' in result:
            return result['embedding']
        elif isinstance(result, list):
            return result[0] if result and isinstance(result[0], list) else result
        else:
            print("Embedding API error or unexpected response:", result)
            return [0.0] * 384
    except Exception as e:
        print("Embedding API request failed:", e)
        return [0.0] * 384

def to_valid_qdrant_id(id_val):
    try:
        # If already a valid UUID string, return as is
        return str(uuid.UUID(str(id_val)))
    except Exception:
        # Otherwise, generate a UUID based on the string
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(id_val)))

if __name__ == "__main__":
    text = "ZenoVerse by Iota Cluster"
    embedding = get_embedding(text)
    print("Embedding:", embedding)
    if embedding:
        print("Embedding Length:", len(embedding))
    else:
        print("Failed to fetch embedding.")
