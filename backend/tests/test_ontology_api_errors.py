import io
import time

from app import create_app
from app.api import graph as graph_api
from app.config import Config
from app.models.project import ProjectManager, ProjectStatus
from app.models.task import TaskManager, TaskStatus
from app.utils.llm_client import LLMResponseError


def _post_ontology(client):
    return client.post(
        "/api/graph/ontology/generate",
        data={
            "simulation_requirement": "Simulate the discussion.",
            "files": (io.BytesIO(b"A short source document."), "source.md"),
        },
        content_type="multipart/form-data",
    )


def _wait_for_task_terminal(task_id, timeout=10.0):
    deadline = time.time() + timeout
    task = TaskManager().get_task(task_id)
    while time.time() < deadline:
        task = TaskManager().get_task(task_id)
        if task and task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED}:
            return task
        time.sleep(0.05)
    return task


def test_ontology_failure_is_persisted_with_safe_error(tmp_path, monkeypatch):
    class FailingGenerator:
        def generate(self, **kwargs):
            raise LLMResponseError(
                "LLM JSON output was truncated at the token limit",
                finish_reason="length",
            )

    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(graph_api, "OntologyGenerator", FailingGenerator)

    app = create_app()
    app.config.update(TESTING=True)
    response = _post_ontology(app.test_client())

    # Upload/queueing succeeds; the LLM failure surfaces on the task/project
    assert response.status_code == 200
    assert response.json["success"] is True
    data = response.json["data"]

    task = _wait_for_task_terminal(data["task_id"])
    assert task is not None and task.status == TaskStatus.FAILED
    assert "token limit" in task.error
    assert "traceback" not in (task.error or "")

    project = ProjectManager.get_project(data["project_id"])
    assert project.status == ProjectStatus.FAILED
    assert project.error == task.error


def test_ontology_provider_error_does_not_expose_provider_body(tmp_path, monkeypatch):
    class ProviderError(RuntimeError):
        status_code = 401
        request_id = "request-safe-id"
        body = {"error": {"message": "SECRET-PROVIDER-BODY"}}

    class FailingGenerator:
        def generate(self, **kwargs):
            raise ProviderError("SECRET-PROVIDER-BODY")

    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(graph_api, "OntologyGenerator", FailingGenerator)

    app = create_app()
    app.config.update(TESTING=True)
    response = _post_ontology(app.test_client())

    assert response.status_code == 200
    data = response.json["data"]

    task = _wait_for_task_terminal(data["task_id"])
    assert task is not None and task.status == TaskStatus.FAILED
    assert "HTTP 401" in task.error
    assert "request-safe-id" in task.error
    assert "SECRET-PROVIDER-BODY" not in task.error

    project = ProjectManager.get_project(data["project_id"])
    assert project.status == ProjectStatus.FAILED
    assert "SECRET-PROVIDER-BODY" not in (project.error or "")
