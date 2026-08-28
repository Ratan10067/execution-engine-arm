import time
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_batch_submissions(client):
    batch_payload = {
        "submissions": [
            {"source_code": "print('Task 1')", "language_id": 71},
            {"source_code": "print('Task 2')", "language_id": 71},
            {"source_code": "print('Task 3')", "language_id": 71},
        ]
    }

    # 1. Create batch
    res_create = client.post("/submissions/batch", json=batch_payload)
    assert res_create.status_code == 201
    tokens_list = res_create.json()
    assert len(tokens_list) == 3
    tokens = [t["token"] for t in tokens_list]

    # 2. Give workers brief time to process
    time.sleep(0.5)

    # 3. Retrieve batch
    tokens_param = ",".join(tokens)
    res_get = client.get(f"/submissions/batch?tokens={tokens_param}")
    assert res_get.status_code == 200
    batch_data = res_get.json()
    assert "submissions" in batch_data
    assert len(batch_data["submissions"]) == 3
    for sub in batch_data["submissions"]:
        assert sub["token"] in tokens
        assert sub["status"]["id"] in [1, 2, 3]  # In queue, Processing, or Accepted
