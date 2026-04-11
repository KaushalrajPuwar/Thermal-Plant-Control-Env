from __future__ import annotations

from pathlib import Path

import uvicorn

import server.app as server_app
from graders.registry import grader_registry
from tasks.registry import task_registry


ROOT = Path(__file__).resolve().parents[2]


def test_launch_contract_and_registries(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)

    captured: dict[str, object] = {}

    def fake_run(app, host, port):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setattr(uvicorn, "run", fake_run)

    server_app.main()

    assert captured["app"] is server_app.app
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 7860

    dockerfile = (ROOT / "Dockerfile").read_text()
    run_local = (ROOT / "scripts" / "run_local.sh").read_text()
    smoke_test = (ROOT / "scripts" / "smoke_test.sh").read_text()
    readme = (ROOT / "README.md").read_text()
    openenv_yaml = (ROOT / "openenv.yaml").read_text()

    assert 'CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]' in dockerfile
    assert 'IMAGE_NAME="${IMAGE_NAME:-thermal-plant-control:latest}"' in run_local
    assert 'PORT="${PORT:-7860}"' in run_local
    assert 'docker run --rm -p "${PORT}:7860" "$IMAGE_NAME"' in run_local
    assert 'http://127.0.0.1:7860' in smoke_test
    assert '--port 7860' in smoke_test
    assert 'docker run -p 7860:7860 thermal-plant-control:latest' in readme
    assert 'app_port: 7860' in readme
    assert 'tasks: tasks.registry:task_registry' in openenv_yaml
    assert 'graders: graders.registry:grader_registry' in openenv_yaml
    assert sorted(task_registry().keys()) == ["task1", "task2", "task3", "task4"]
    assert sorted(grader_registry().keys()) == ["task1", "task2", "task3", "task4"]
