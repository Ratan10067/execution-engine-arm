import base64
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_base64_encoded_submission(client):
    # Base64 encode code and stdin
    code = "name = input()\nprint('Encoded Hello, ' + name)"
    b64_code = base64.b64encode(code.encode("utf-8")).decode("utf-8")
    stdin_str = "ARM64User"
    b64_stdin = base64.b64encode(stdin_str.encode("utf-8")).decode("utf-8")

    payload = {
        "source_code": b64_code,
        "language_id": 71,
        "stdin": b64_stdin,
    }

    # Submit with base64_encoded=true and wait=true
    res = client.post("/submissions?wait=true&base64_encoded=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 3

    # Output should be base64 encoded because base64_encoded=true
    raw_stdout = data["stdout"]
    decoded_stdout = base64.b64decode(raw_stdout.encode("utf-8")).decode("utf-8")
    assert "Encoded Hello, ARM64User" in decoded_stdout
