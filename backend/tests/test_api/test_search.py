"""
Tests for Search API endpoints — full-text and semantic search.
"""
import io
import pytest


class TestFullTextSearch:
    """Tests for GET /api/v1/search/"""

    def test_search_fulltext_found(self, client, sample_knowledge):
        """Test full-text search finds matching items."""
        response = client.get("/api/v1/search/?q=微服务")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["title"] == sample_knowledge.title

    def test_search_fulltext_not_found(self, client):
        """Test full-text search with no matches returns empty list."""
        response = client.get("/api/v1/search/?q=不存在的关键词")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_search_fulltext_with_category(self, client, sample_knowledge):
        """Test full-text search filtered by category."""
        response = client.get("/api/v1/search/?q=微服务&category=技术")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_search_fulltext_wrong_category(self, client, sample_knowledge):
        """Test search with non-matching category returns empty."""
        response = client.get("/api/v1/search/?q=微服务&category=设计")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_search_fulltext_missing_query(self, client):
        """Test search without 'q' parameter returns 422."""
        response = client.get("/api/v1/search/")
        assert response.status_code == 422

    def test_search_fulltext_limit(self, client, sample_knowledge_data):
        """Test search respects the limit parameter."""
        for i in range(5):
            data = sample_knowledge_data.copy()
            data["title"] = f"测试文档 {i}"
            client.post("/api/v1/knowledge/", json=data)

        response = client.get("/api/v1/search/?q=测试&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestSemanticSearch:
    """Tests for GET /api/v1/search/semantic"""

    def test_semantic_search_returns_valid_response(self, client):
        """Test semantic search returns valid JSON structure."""
        response = client.get("/api/v1/search/semantic?q=微服务&top_k=5")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["query"] == "微服务"
        assert isinstance(data["results"], list)
        assert isinstance(data["total"], int)

    def test_semantic_search_found(self, client, sample_knowledge_data):
        """Test semantic search finds indexed documents."""
        # First create a knowledge item (this indexes it into vector store)
        resp = client.post("/api/v1/knowledge/", json=sample_knowledge_data)
        assert resp.status_code == 201
        item_id = resp.json()["id"]

        # Now search semantically
        response = client.get("/api/v1/search/semantic?q=什么是微服务&top_k=5")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "什么是微服务"
        assert data["total"] >= 1
        # Results should contain the document we just created
        docs = [r["document"] for r in data["results"]]
        assert any("微服务" in d for d in docs)

    def test_semantic_search_chinese(self, client, sample_knowledge_data):
        """Test Chinese semantic search returns relevant results."""
        resp = client.post("/api/v1/knowledge/", json=sample_knowledge_data)
        assert resp.status_code == 201

        # Search with a different Chinese query
        response = client.get("/api/v1/search/semantic?q=微服务架构&top_k=5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_semantic_search_top_k(self, client, sample_knowledge_data):
        """Test top_k parameter limits results."""
        for i in range(3):
            data = sample_knowledge_data.copy()
            data["title"] = f"测试文档 {i}"
            client.post("/api/v1/knowledge/", json=data)

        response = client.get("/api/v1/search/semantic?q=测试&top_k=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2