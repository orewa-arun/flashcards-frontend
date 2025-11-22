from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
client = QdrantClient(":memory:")
client.recreate_collection("test", vectors_config=VectorParams(size=4, distance=Distance.COSINE))
client.upsert("test", points=[PointStruct(id=1, vector=[0.1, 0.1, 0.1, 0.1], payload={"a": 1})])
res = client.query_points("test", query=[0.1, 0.1, 0.1, 0.1], limit=1)
print(f"Result type: {type(res)}")
print(f"Result dir: {dir(res)}")
print(f"Result points: {res.points}")

