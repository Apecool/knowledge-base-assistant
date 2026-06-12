"""
Tests for Knowledge CRUD API endpoints — with visibility (private/shared) support.
All CRUD endpoints require a Bearer token; tests use the auth_headers fixture.
"""
import pytest


# ---------------------------------------------------------------------------
# Helper: create a knowledge item via API and return the response JSON
# ---------------------------------------------------------------------------
def _create_item(client, headers, data):
    resp = client.post("/api/v1/knowledge/", json=data, headers=headers)
    assert resp.status_code == 201
    return resp.json()


# ===========================================================================
# CREATE
# ===========================================================================
class TestCreateKnowledge:
    """Tests for POST /api/v1/knowledge/"""

    def test_create_knowledge_success(self, client, auth_headers, sample_knowledge_data):
        """Creating a new knowledge item returns 201 and correct data."""
        response = client.post("/api/v1/knowledge/", json=sample_knowledge_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_knowledge_data["title"]
        assert data["content"] == sample_knowledge_data["content"]
        assert data["category"] == sample_knowledge_data["category"]
        assert data["tags"] == sample_knowledge_data["tags"]
        assert data["status"] == "draft"
        assert data["visibility"] == "private"  # default

    def test_create_knowledge_shared(self, client, auth_headers, sample_knowledge_data):
        """Creating a shared knowledge item sets visibility correctly."""
        data = sample_knowledge_data.copy()
        data["visibility"] = "shared"
        response = client.post("/api/v1/knowledge/", json=data, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["visibility"] == "shared"

    def test_create_knowledge_missing_title(self, client, auth_headers):
        """Creating without title returns 422."""
        response = client.post("/api/v1/knowledge/", json={"content": "some content"}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_knowledge_missing_content(self, client, auth_headers):
        """Creating without content returns 422."""
        response = client.post("/api/v1/knowledge/", json={"title": "my title"}, headers=auth_headers)
        assert response.status_code == 422

    def test_create_knowledge_empty_title(self, client, auth_headers):
        """Creating with empty title returns 422."""
        response = client.post(
            "/api/v1/knowledge/", json={"title": "", "content": "content"}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_knowledge_no_auth(self, client, sample_knowledge_data):
        """Creating without Bearer token returns 401."""
        response = client.post("/api/v1/knowledge/", json=sample_knowledge_data)
        assert response.status_code == 401


# ===========================================================================
# LIST
# ===========================================================================
class TestListKnowledge:
    """Tests for GET /api/v1/knowledge/"""

    def test_list_knowledge_empty(self, client, auth_headers):
        """Listing when no items exist returns empty list."""
        response = client.get("/api/v1/knowledge/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    def test_list_knowledge_with_items(self, client, auth_headers, sample_knowledge_data):
        """Listing returns created items."""
        client.post("/api/v1/knowledge/", json=sample_knowledge_data, headers=auth_headers)
        response = client.get("/api/v1/knowledge/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_list_knowledge_pagination(self, client, auth_headers, sample_knowledge_data):
        """Pagination parameters work correctly."""
        for i in range(5):
            data = sample_knowledge_data.copy()
            data["title"] = f"Title {i}"
            client.post("/api/v1/knowledge/", json=data, headers=auth_headers)

        response = client.get("/api/v1/knowledge/?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

        response = client.get("/api/v1/knowledge/?page=3&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    def test_list_knowledge_filter_category(self, client, auth_headers, sample_knowledge_data):
        """Filtering by category works."""
        client.post("/api/v1/knowledge/", json=sample_knowledge_data, headers=auth_headers)

        design_data = sample_knowledge_data.copy()
        design_data["title"] = "设计模式"
        design_data["category"] = "设计"
        client.post("/api/v1/knowledge/", json=design_data, headers=auth_headers)

        response = client.get("/api/v1/knowledge/?category=技术", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

        response = client.get("/api/v1/knowledge/?category=设计", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_list_knowledge_search(self, client, auth_headers, sample_knowledge_data):
        """Full-text search filter works."""
        client.post("/api/v1/knowledge/", json=sample_knowledge_data, headers=auth_headers)

        response = client.get("/api/v1/knowledge/?search=微服务", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    def test_list_knowledge_no_auth(self, client):
        """Listing without Bearer token returns 401."""
        response = client.get("/api/v1/knowledge/")
        assert response.status_code == 401


# ===========================================================================
# GET
# ===========================================================================
class TestGetKnowledge:
    """Tests for GET /api/v1/knowledge/{id}"""

    def test_get_knowledge_success(self, client, auth_headers, sample_knowledge_data):
        """Getting a knowledge item by ID works."""
        item = _create_item(client, auth_headers, sample_knowledge_data)
        response = client.get(f"/api/v1/knowledge/{item['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item["id"]
        assert data["title"] == sample_knowledge_data["title"]

    def test_get_knowledge_not_found(self, client, auth_headers):
        """Getting non-existent item returns 404."""
        response = client.get("/api/v1/knowledge/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ===========================================================================
# UPDATE
# ===========================================================================
class TestUpdateKnowledge:
    """Tests for PUT /api/v1/knowledge/{id}"""

    def test_update_knowledge_success(self, client, auth_headers, sample_knowledge_data):
        """Updating a knowledge item works."""
        item = _create_item(client, auth_headers, sample_knowledge_data)
        update_data = {"title": "更新后的标题", "content": "更新后的内容"}
        response = client.put(f"/api/v1/knowledge/{item['id']}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["content"] == "更新后的内容"

    def test_update_knowledge_partial(self, client, auth_headers, sample_knowledge_data):
        """Partial update of a knowledge item works."""
        item = _create_item(client, auth_headers, sample_knowledge_data)
        response = client.put(
            f"/api/v1/knowledge/{item['id']}", json={"category": "新分类"}, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "新分类"
        assert data["title"] == sample_knowledge_data["title"]  # unchanged

    def test_update_knowledge_not_found(self, client, auth_headers):
        """Updating non-existent item returns 404."""
        response = client.put("/api/v1/knowledge/99999", json={"title": "new"}, headers=auth_headers)
        assert response.status_code == 404

    def test_update_knowledge_change_visibility(self, client, auth_headers, sample_knowledge_data):
        """Changing visibility of own item works."""
        item = _create_item(client, auth_headers, sample_knowledge_data)
        response = client.put(
            f"/api/v1/knowledge/{item['id']}", json={"visibility": "shared"}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["visibility"] == "shared"


# ===========================================================================
# VISIBILITY RULES
# ===========================================================================
class TestVisibility:
    """Tests for private/shared visibility rules."""

    def test_private_item_not_visible_to_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """A private item is NOT visible to another user."""
        item = _create_item(client, auth_headers, sample_knowledge_data)

        # User 2 cannot see it
        response = client.get(f"/api/v1/knowledge/{item['id']}", headers=auth_headers_2)
        assert response.status_code == 404

    def test_shared_item_visible_to_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """A shared item IS visible to another user."""
        data = sample_knowledge_data.copy()
        data["visibility"] = "shared"
        item = _create_item(client, auth_headers, data)

        # User 2 can see it
        response = client.get(f"/api/v1/knowledge/{item['id']}", headers=auth_headers_2)
        assert response.status_code == 200
        assert response.json()["visibility"] == "shared"

    def test_shared_item_editable_by_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """A shared item CAN be edited by another user."""
        data = sample_knowledge_data.copy()
        data["visibility"] = "shared"
        item = _create_item(client, auth_headers, data)

        response = client.put(
            f"/api/v1/knowledge/{item['id']}",
            json={"title": "被其他用户修改"},
            headers=auth_headers_2,
        )
        assert response.status_code == 200
        assert response.json()["title"] == "被其他用户修改"

    def test_shared_item_visibility_not_changeable_by_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """A shared item's visibility CANNOT be changed by a non-owner."""
        data = sample_knowledge_data.copy()
        data["visibility"] = "shared"
        item = _create_item(client, auth_headers, data)

        response = client.put(
            f"/api/v1/knowledge/{item['id']}",
            json={"visibility": "private"},
            headers=auth_headers_2,
        )
        assert response.status_code == 403

    def test_shared_item_not_deletable_by_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """A shared item CANNOT be deleted by a non-owner."""
        data = sample_knowledge_data.copy()
        data["visibility"] = "shared"
        item = _create_item(client, auth_headers, data)

        response = client.delete(f"/api/v1/knowledge/{item['id']}", headers=auth_headers_2)
        assert response.status_code == 404

    def test_list_shows_own_and_shared_items(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """List shows own items + shared items from other users, but NOT other users' private items."""
        # User 1 creates private + shared
        client.post("/api/v1/knowledge/", json=sample_knowledge_data, headers=auth_headers)
        shared_data = sample_knowledge_data.copy()
        shared_data["title"] = "共享条目"
        shared_data["visibility"] = "shared"
        client.post("/api/v1/knowledge/", json=shared_data, headers=auth_headers)

        # User 2 creates private
        user2_data = sample_knowledge_data.copy()
        user2_data["title"] = "User2私有"
        client.post("/api/v1/knowledge/", json=user2_data, headers=auth_headers_2)

        # User 2 sees: own private + user1's shared = 2 items
        response = client.get("/api/v1/knowledge/", headers=auth_headers_2)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = [item["title"] for item in data["items"]]
        assert "共享条目" in titles
        assert "User2私有" in titles
        assert "什么是微服务架构" not in titles  # user1's private


# ===========================================================================
# FILE PARSE
# ===========================================================================
class TestFileParse:
    """Tests for POST /api/v1/knowledge/parse-file"""

    def test_parse_txt_file(self, client):
        """Parsing a .txt file returns extracted content without saving."""
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
        """Parsing unsupported file type returns 400."""
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("test.exe", b"fake", "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_parse_empty_file(self, client):
        """Parsing empty file returns 400."""
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400

    def test_parse_md_file_extracts_title(self, client):
        """.md file with heading extracts title correctly."""
        content = "# API 网关设计\n\n这是关于API网关的详细设计文档。".encode("utf-8")
        response = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("api.md", content, "text/markdown")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "API 网关" in data["title"]
        assert "API网关" in data["content"]

    def test_parse_then_create_no_duplicate(self, client, auth_headers):
        """parse-file does NOT create a record; subsequent create creates ONE."""
        content = "单独测试文档内容".encode("utf-8")
        resp1 = client.post(
            "/api/v1/knowledge/parse-file",
            files={"file": ("doc.txt", content, "text/plain")},
        )
        assert resp1.status_code == 200

        list_resp = client.get("/api/v1/knowledge/", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0


# ===========================================================================
# DELETE
# ===========================================================================
class TestDeleteKnowledge:
    """Tests for DELETE /api/v1/knowledge/{id}"""

    def test_delete_knowledge_success(self, client, auth_headers, sample_knowledge_data):
        """Deleting a knowledge item returns 204."""
        item = _create_item(client, auth_headers, sample_knowledge_data)
        response = client.delete(f"/api/v1/knowledge/{item['id']}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/knowledge/{item['id']}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_knowledge_not_found(self, client, auth_headers):
        """Deleting non-existent item returns 404."""
        response = client.delete("/api/v1/knowledge/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_knowledge_not_owned_by_other_user(
        self, client, auth_headers, auth_headers_2, sample_knowledge_data
    ):
        """User cannot delete another user's private item."""
        item = _create_item(client, auth_headers, sample_knowledge_data)

        # User 2 tries to delete user 1's item
        response = client.delete(f"/api/v1/knowledge/{item['id']}", headers=auth_headers_2)
        assert response.status_code == 404  # not found (not owned)