from qdrant_client import QdrantClient
client = QdrantClient(":memory:")
print(f"Dir client: {dir(client)}")

