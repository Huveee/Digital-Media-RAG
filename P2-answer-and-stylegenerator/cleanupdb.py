import chromadb

client = chromadb.Client()
collection_name = "knowledge_base"

# Drop collection if it exists
if collection_name in [c.name for c in client.list_collections()]:
    client.delete_collection(name=collection_name)
    print(f"Collection '{collection_name}' deleted.")
