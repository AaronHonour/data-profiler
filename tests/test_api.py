"""Tests for FastAPI endpoints."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from data_profiler.api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "operational"

    def test_health_check(self) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestProfileEndpoints:
    """Tests for profiling endpoints."""

    def test_profile_upload_csv(self) -> None:
        """Test profiling uploaded CSV file."""
        # Create sample CSV
        df = pd.DataFrame(
            {
                "id": range(100),
                "value": range(100, 200),
                "category": ["A", "B", "C"] * 33 + ["A"],
            }
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            csv_path = f.name
            df.to_csv(f, index=False)

        try:
            with open(csv_path, "rb") as f:
                response = client.post(
                    "/api/v1/profile/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["row_count"] == 100
            assert data["column_count"] == 3
            assert len(data["columns"]) == 3
        finally:
            Path(csv_path).unlink()

    def test_profile_upload_invalid_file(self) -> None:
        """Test uploading invalid file type."""
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            f.write(b"test content")
            f.seek(0)

            response = client.post(
                "/api/v1/profile/upload",
                files={"file": ("test.txt", f, "text/plain")},
            )

            assert response.status_code == 400

    def test_profile_with_config(self) -> None:
        """Test profiling with custom configuration."""
        df = pd.DataFrame({"value": range(1000)})

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        ) as f:
            csv_path = f.name
            df.to_csv(f, index=False)

        try:
            with open(csv_path, "rb") as f:
                response = client.post(
                    "/api/v1/profile/upload",
                    files={"file": ("test.csv", f, "text/csv")},
                    params={
                        "sample_size": 100,
                        "compute_correlations": False,
                        "parallel": False,
                    },
                )

            assert response.status_code == 200
            data = response.json()
            assert data["row_count"] == 1000
        finally:
            Path(csv_path).unlink()
