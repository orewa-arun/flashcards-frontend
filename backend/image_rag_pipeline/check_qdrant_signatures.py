from qdrant_client import QdrantClient
import inspect
client = QdrantClient(":memory:")
print(f"query_points signature: {inspect.signature(client.query_points)}")
print(f"query signature: {inspect.signature(client.query)}")

