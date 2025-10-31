import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api import app
import uuid
from app.db import get_session
from app.documents.router import router as documents_router

# Fixtures
@pytest.fixture
def client(settings, override_get_session):
    """Test client fixture with overridden dependencies"""
    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)

@pytest.fixture
def document_title():
    return f"Test Document {uuid.uuid4()}"

@pytest.fixture
def document_content():
    return "This is a test document about artificial intelligence and machine learning."

@pytest.fixture
def search_query():
    return "artificial intelligence"

@pytest.fixture
def user_id():
    return f"test-user-{uuid.uuid4()}"

@pytest.fixture
def api_key_header(settings):
    return {settings.api_key_name: settings.api_key}

# Test cases
@pytest.mark.asyncio
async def test_document_creation_and_search(client, document_title, document_content, user_id, api_key_header):
    """Test the full flow: create a document and then search for it"""
    
    # 1. Create document
    create_payload = {
        "title": document_title,
        "content": document_content
    }
    create_response = client.post("/documents", json=create_payload, headers=api_key_header)
    assert create_response.status_code == 200
    created_doc = create_response.json()
    assert created_doc["title"] == document_title
    assert created_doc["content"] == document_content
    assert "id" in created_doc
    doc_id = created_doc["id"]

    # Give time for async embedding generation
    import asyncio
    await asyncio.sleep(1)

    # 2. Search for the document
    search_payload = {
        "query": "artificial intelligence",
        "user_id": user_id
    }
    search_response = client.post("/documents/search", json=search_payload, headers=api_key_header)
    assert search_response.status_code == 200
    search_results = search_response.json()
    
    # Verify search results
    assert isinstance(search_results, list)
    matching_docs = [doc for doc in search_results if doc["id"] == doc_id]
    assert len(matching_docs) > 0, "Created document should appear in search results"

@pytest.mark.asyncio
async def test_document_search_empty_query(client, user_id, api_key_header):
    """Test search with empty query"""
    search_payload = {
        "query": "",
        "user_id": user_id
    }
    response = client.post("/documents/search", json=search_payload, headers=api_key_header)
    assert response.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_document_creation_invalid(client, api_key_header):
    """Test document creation with invalid data"""
    # Test missing content
    payload = {
        "title": "Test Document"
    }
    response = client.post("/documents", json=payload, headers=api_key_header)
    assert response.status_code == 422

    # Test empty title
    payload = {
        "title": "",
        "content": "Some content"
    }
    response = client.post("/documents", json=payload, headers=api_key_header)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_search_without_user_id(client, api_key_header):
    """Test search without user_id"""
    search_payload = {
        "query": "test query"
    }
    response = client.post("/documents/search", json=search_payload, headers=api_key_header)
    assert response.status_code == 422  # Should fail validation

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test access without API key"""
    payload = {
        "title": "Test Document",
        "content": "Test content"
    }
    response = client.post("/documents", json=payload)
    assert response.status_code == 401  # Unauthorized

    search_payload = {
        "query": "test",
        "user_id": "test-user"
    }
    response = client.post("/documents/search", json=search_payload)
    assert response.status_code == 401  # Unauthorized