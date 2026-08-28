import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "arch" in data
    assert "workers" in data


def test_statuses_endpoint(client):
    res = client.get("/statuses")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 14
    status_map = {s["id"]: s["description"] for s in data}
    assert status_map[1] == "In Queue"
    assert status_map[2] == "Processing"
    assert status_map[3] == "Accepted"
    assert status_map[4] == "Wrong Answer"
    assert status_map[5] == "Time Limit Exceeded"
    assert status_map[6] == "Compilation Error"
    assert status_map[7] == "Runtime Error (SIGSEGV)"
    assert status_map[11] == "Runtime Error (NZEC)"


def test_languages_endpoint(client):
    res = client.get("/languages")
    assert res.status_code == 200
    langs = res.json()
    assert isinstance(langs, list)
    assert len(langs) > 0

    # Check Python 3 (71), C++ (54), Bash (46)
    lang_ids = [l["id"] for l in langs]
    assert 71 in lang_ids
    assert 54 in lang_ids
    assert 46 in lang_ids

    # Test single language lookup
    res_single = client.get("/languages/71")
    assert res_single.status_code == 200
    assert "Python" in res_single.json()["name"]


def test_system_and_config_info(client):
    res_sys = client.get("/system_info")
    assert res_sys.status_code == 200
    sys_data = res_sys.json()
    assert "architecture" in sys_data
    assert "total_memory_kb" in sys_data

    res_conf = client.get("/config_info")
    assert res_conf.status_code == 200
    conf_data = res_conf.json()
    assert conf_data["max_memory_limit"] == 10485760  # 10 GB
    assert conf_data["count"] == 8  # 8 workers


def test_about_version_license(client):
    res_about = client.get("/about")
    assert res_about.status_code == 200

    res_ver = client.get("/version")
    assert res_ver.status_code == 200
    assert "1.13.0" in res_ver.text

    res_lic = client.get("/license")
    assert res_lic.status_code == 200


def test_workers_endpoint(client):
    res = client.get("/workers")
    assert res.status_code == 200
    workers = res.json()
    assert isinstance(workers, list)
    assert workers[0]["available_workers"] == 8
