import requests
import json
import time

def test_create_document(title, content):
    url = "http://localhost:8000/documents"
    payload = {
        "title": title,
        "content": content
    }
    response = requests.post(url, json=payload)
    print(f"\nCreate Document Response ({title}):", response.status_code)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error:", response.text)
    return response.json() if response.status_code == 200 else None

def test_search_documents(query):
    url = "http://localhost:8000/documents/search"
    payload = {
        "query": query,
        "user_id": "test-user-123"
    }
    response = requests.post(url, json=payload)
    print(f"\nSearch Response for '{query}':", response.status_code)
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error:", response.text)
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    # Create test documents
    docs = [
        ("AI Introduction", "Artificial Intelligence is transforming how we work and live. Machine learning models can now perform complex tasks."),
        ("Database Systems", "Modern databases use advanced indexing and storage techniques for efficient data retrieval."),
        ("Web Development", "Modern web applications use frameworks like FastAPI and React for better developer experience."),
        ("Data Science", "Data scientists use machine learning and AI to extract insights from large datasets.")
    ]
    
    print("Creating test documents...")
    for title, content in docs:
        doc = test_create_document(title, content)
        time.sleep(1)  # Give some time for potential background processing
    
    print("\nTesting searches...")
    # Test different search queries
    searches = [
        "artificial intelligence and machine learning",
        "database systems",
        "web development frameworks",
        "unrelated topic that shouldn't match well"
    ]
    
    for query in searches:
        results = test_search_documents(query)
        time.sleep(1)  # Space out the requests