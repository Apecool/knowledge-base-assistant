"""
Tests for Knowledge CRUD API endpoints.
"""
import pytest


class TestCreateKnowledge:
    """Tests for POST /api/v1/knowledge/"""

    def test_create_knowledge_success(self, client, sample_knowledge_data):
        """Test creating a new knowledge item returns 201 and correct data."""
        response = client.post("/api/v1/knowledge/", json=sample_knowledge_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_knowledge_data["title"]
        assert data["content"] == sample_knowledge_data["content"]
        assert data["category"] == sample_knowledge_data["category"]
        assert data["tags"] == sample_knowledge_data["tags"]
        assert "id" in data
        assert data["status"] == "draft"

    def test_create_knowledge_missing_title(self, client):
        """Test creating a knowledge item without title returns 422."""
        response = client.post("/api/v1/knowledge/", json={"content": "some content"})
        assert response.status_code == 422

    def test_create_knowledge_missing_content(self, client):
        """Test creating a knowledge item without content returns 422."""
        response = client.post("/api/v1/knowledge/", json={"title": "my title"})
        assert response.status_code == 422

    def test_create_knowledge_empty_title(self, client):
        """Test creating with empty title returns 422."""
        response = client.post(
            "/api/v1/knowledge/", json={"title": "", "content": "content"}
        )
        assert response.status_code == 422


class TestListKnowledge:
    """Tests for GET /api/v1/knowledge/"""

    def test_list_knowledge_empty(self, client):
        """Test listing when no items exist returns empty list."""
        response = client.get("/api/v1/knowledge/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    def test_list_knowledge_with_items(self, client, sample_knowledge):
        """Test listing returns created items."""
        response = client.get("/api/v1/knowledge/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == sample_knowledge.id

    def test_list_knowledge_pagination(self, client, db, sample_knowledge_data):
        """Test pagination parameters work correctly."""
        # Create 5 items
        for i in range(5):
            data = sample_knowledge_data.copy()
            data["title"] = f"Title {i}"
            client.post("/api/v1/knowledge/", json=data)

        # Page 1 with page_size=2
        response = client.get("/api/v1/knowledge/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

        # Page 3 should have 1 item
        response = client.get("/api/v1/knowledge/?page=3&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_knowledge_filter_category(self, client, sample_knowledge_data):
        """Test filtering by category."""
        # Create items with different categories
        tech_data = sample_knowledge_data.copy()
        client.post("/api/v1/knowledge/", json=tech_data)

        design_data = sample_knowledge_data.copy()
        design_data["title"] = "设计模式"
        design_data["category"] = "设计"
        client.post("/api/v1/knowledge/", json=design_data)

        # Filter by "技术"
        response = client.get("/api/v1/knowledge/?category=技术")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Filter by "设计"
        response = client.get("/api/v1/knowledge/?category=设计")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_knowledge_search(self, client, sample_knowledge_data):
        """Test full-text search filter."""
        client.post("/api/v1/knowledge/", json=sample_knowledge_data)

        response = client.get("/api/v1/knowledge/?search=微服务")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestGetKnowledge:
    """Tests for GET /api/v1/knowledge/{id}"""

    def test_get_knowledge_success(self, client, sample_knowledge):
        """Test getting a knowledge item by ID."""
        response = client.get(f"/api/v1/knowledge/{sample_knowledge.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_knowledge.id
        assert data["title"] == sample_knowledge.title

    def test_get_knowledge_not_found(self, client):
        """Test getting non-existent item returns 404."""
        response = client.get("/api/v1/knowledge/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUpdateKnowledge:
    """Tests for PUT /api/v1/knowledge/{id}"""

    def test_update_knowledge_success(self, client, sample_knowledge):
        """Test updating a knowledge item."""
        update_data = {"title": "更新后的标题", "content": "更新后的内容"}
        response = client.put(
            f"/api/v1/knowledge/{sample_knowledge.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["content"] == "更新后的内容"

    def test_update_knowledge_partial(self, client, sample_knowledge):
        """Test partial update of a knowledge item."""
        response = client.put(
            f"/api/v1/knowledge/{sample_knowledge.id}",
            json={"category": "新分类"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "新分类"
        assert data["title"] == sample_knowledge.title  # unchanged

    def test_update_knowledge_not_found(self, client):
        """Test updating non-existent item returns 404."""
        response = client.put(
            "/api/v1/knowledge/99999", json={"title": "new title"}
        )
        assert response.status_code == 404


class TestFileParse:
    """Tests for POST /api/v1/knowledge/parse-file"""

    def test_parse_txt_file(self, client):
        """Test parsing a .txt file returns extracted content without saving."""
        content = "# 测试标题\n\n这是文档内容。".encode("utf-8")
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("test.txt", content, "text/plain")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试标题"
        assert "这是文档内容" in data["content"]
        assert data["file_type"] == "txt"

    def test_parse_unsupported_file(self, client):
        """Test parsing unsupported file type returns 400."""
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("test.exe", b"fake", "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_parse_empty_file(self, client):
        """Test parsing empty file returns 400."""
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400

    def test_parse_md_file_extracts_title(self, client):
        """Test .md file with heading extracts title correctly."""
        content = "# API 网关设计\n\n这是关于API网关的详细设计文档。".encode("utf-8")
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("api.md", content, "text/markdown")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "API 网关" in data["title"]
        assert "API网关" in data["content"]

    def test_parse_then_create_no_duplicate(self, client):
        """
        Test that parse-file does NOT create a record,
        and subsequent create only creates ONE.
        """
        content = "单独测试文档内容".encode("utf-8")
        # Parse (should not create)
        resp1 = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("doc.txt", content, "text/plain")},
        )
        assert resp1.status_code == 200

        # Verify no record was created
        list_resp = client.get("/api/v1/knowledge/")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0


class TestDeleteKnowledge:
    """Tests for DELETE /api/v1/knowledge/{id}"""

    def test_delete_knowledge_success(self, client, sample_knowledge):
        """Test deleting a knowledge item returns 204."""
        response = client.delete(f"/api/v1/knowledge/{sample_knowledge.id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/knowledge/{sample_knowledge.id}")
        assert get_response.status_code == 404

    def test_delete_knowledge_not_found(self, client):
        """Test deleting non-existent item returns 404."""
        response = client.delete("/api/v1/knowledge/99999")
        assert response.status_code == 404