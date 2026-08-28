import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_python_simple_execution(client):
    payload = {
        "source_code": "print('Hello from ARM64 Engine')",
        "language_id": 71,  # Python 3
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 3
    assert data["status"]["description"] == "Accepted"
    assert "Hello from ARM64 Engine" in data["stdout"]
    assert data["time"] is not None
    assert data["memory"] is not None


def test_python_stdin_and_expected_output(client):
    # Test matching expected output (Accepted)
    payload = {
        "source_code": "name = input()\nprint(f'Welcome, {name}!')",
        "language_id": 71,
        "stdin": "NexusBrain",
        "expected_output": "Welcome, NexusBrain!\n",
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 3
    assert data["status"]["description"] == "Accepted"
    assert data["stdout"].strip() == "Welcome, NexusBrain!"

    # Test mismatched expected output (Wrong Answer)
    payload_wa = {
        "source_code": "print('actual answer')",
        "language_id": 71,
        "expected_output": "different answer expected",
    }
    res_wa = client.post("/submissions?wait=true", json=payload_wa)
    assert res_wa.status_code == 201
    data_wa = res_wa.json()
    assert data_wa["status"]["id"] == 4
    assert data_wa["status"]["description"] == "Wrong Answer"


def test_time_limit_exceeded(client):
    payload = {
        "source_code": "import time\nwhile True:\n    pass",
        "language_id": 71,
        "cpu_time_limit": 1.0,
        "wall_time_limit": 1.0,
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 5
    assert data["status"]["description"] == "Time Limit Exceeded"


def test_runtime_error_nzec(client):
    payload = {
        "source_code": "import sys\nprint('starting')\nsys.exit(42)",
        "language_id": 71,
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 11
    assert data["status"]["description"] == "Runtime Error (NZEC)"
    assert data["exit_code"] == 42


def test_c_compilation_error(client):
    # Invalid C syntax
    payload = {
        "source_code": "int main() { INVALID_SYNTAX_HERE; return 0; }",
        "language_id": 50,  # C (GCC 9.2.0)
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 6
    assert data["status"]["description"] == "Compilation Error"
    assert data["compile_output"] is not None


def test_field_filtering(client):
    payload = {
        "source_code": "print('filtered field test')",
        "language_id": 71,
    }
    res = client.post("/submissions?wait=true&fields=stdout,time,status", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "stdout" in data
    assert "time" in data
    assert "status" in data
    assert "compile_output" not in data
    assert "additional_files" not in data


def test_bash_execution(client):
    payload = {
        "source_code": "echo 'Bash Execution Test'\nexpr 20 + 22",
        "language_id": 46,  # Bash
    }
    res = client.post("/submissions?wait=true", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"]["id"] == 3
    assert "Bash Execution Test" in data["stdout"]
    assert "42" in data["stdout"]
