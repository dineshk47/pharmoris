import requests
import json

def test_document_creation():
    url = "http://localhost:8000/documents"
    payload = {
        "title": "Test Document",
        "content": "This is a test document about artificial intelligence and machine learning."
    }
    response = requests.post(url, json=payload)
    print("Create Document Response:", response.status_code)
    print("Response Headers:", dict(response.headers))
    
    try:
        if response.content:
            print("Response Content:", response.text)
            return response.json()
        else:
            print("No content in response")
            return None
    except Exception as e:
        print("Error parsing response:", str(e))
        print("Raw response:", response.text)
        return None

def test_document_search():
    url = "http://localhost:8000/documents/search"
    payload = {
        "query": "artificial intelligence",
        "user_id": "test-user-123"
    }
    response = requests.post(url, json=payload)
    print("\nSearch Response:", response.status_code)
    print("Response Headers:", dict(response.headers))
    
    try:
        if response.content:
            print("Response Content:", response.text)
            return response.json()
        else:
            print("No content in response")
            return None
    except Exception as e:
        print("Error parsing response:", str(e))
        print("Raw response:", response.text)
        return None

if __name__ == "__main__":
    print("Creating test document...")
    doc = test_document_creation()
    
    print("\nWaiting for embedding to be computed...")
    import time
    time.sleep(5)
    
    print("\nSearching documents...")
    test_document_search()