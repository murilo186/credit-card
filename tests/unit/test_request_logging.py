import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_request_id_and_structured_log_are_emitted(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="app.requests"):
        response = TestClient(app).get("/health")

    payload = json.loads(caplog.records[-1].message)
    assert response.headers["X-Request-ID"] == payload["request_id"]
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["error_code"] is None
