import qdrant_client
import importlib.metadata
try:
    print(f"Version from metadata: {importlib.metadata.version('qdrant-client')}")
except Exception as e:
    print(f"Could not get version from metadata: {e}")

print(f"Dir qdrant_client: {dir(qdrant_client)}")

from qdrant_client import QdrantClient
try:
    client = QdrantClient(":memory:")
    print(f"Client type: {type(client)}")
    print(f"Has search? {hasattr(client, 'search')}")
    # print(f"Dir client: {dir(client)}") 
except Exception as e:
    print(f"Error creating client: {e}")
