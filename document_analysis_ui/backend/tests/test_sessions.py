"""Tests for session management."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestSessionEndpoints:
    """Tests for session API endpoints."""

    def test_create_session(self, client):
        """Test creating a new session."""
        response = client.post("/api/sessions", json={"financial_threshold": 20000})
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"
        assert "upload_url" in data

    def test_create_session_default_threshold(self, client):
        """Test creating a session with default threshold."""
        response = client.post("/api/sessions", json={})
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data

    def test_get_session(self, client):
        """Test getting a session."""
        # Create a session first
        create_response = client.post("/api/sessions", json={})
        session_id = create_response.json()["session_id"]

        # Get the session
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["status"] == "created"

    def test_get_nonexistent_session(self, client):
        """Test getting a session that doesn't exist."""
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_delete_session(self, client):
        """Test deleting a session."""
        # Create a session first
        create_response = client.post("/api/sessions", json={})
        session_id = create_response.json()["session_id"]

        # Delete the session
        response = client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404

    def test_list_sessions(self, client):
        """Test listing sessions."""
        # Create a few sessions
        client.post("/api/sessions", json={})
        client.post("/api/sessions", json={})

        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
