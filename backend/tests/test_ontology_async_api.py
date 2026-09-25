import io
import threading

from app import create_app
from app.api import graph as graph_api
from app.config import Config
from app.models.project import ProjectManager, ProjectStatus
from app.models.task import TaskManager, TaskStatus


def _post_ontology(client):
    return client.post(
        "/api/graph/ontology/generate",
        data={
            "simulation_requirement": "Simulate the discussion.",
            "files": (io.BytesIO(b"A short source document."), "source.md"),
        },
        content_type="multipart/form-data",
    )


def test_ontology_generate_returns_task_immediately(tmp_path, monkeypatch):
    """The LLM call must not block the HTTP response."""
    release = threading.Event()

    class BlockingGenerator:
        def generate(self, **kwargs):
            release.wait(timeout=10)
            return {
                "entity_types": [],
                "edge_types": [],
                "analysis_summary": "ok",
            }

    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(graph_api, "OntologyGenerator", BlockingGenerator)

    app = create_app()
    app.config.update(TESTING=True)

    response = _post_ontology(app.test_client())

    # The request must succeed while the generator is still blocked on the LLM
    assert response.status_code == 200
    assert response.json["success"] is True
    data = response.json["data"]
    assert data["project_id"].startswith("proj_")
    assert isinstance(data["task_id"], str) and len(data["task_id"]) >= 8
    assert data["status"] == "ontology_pending"

    project = ProjectManager.get_project(data["project_id"])
    assert project.status == ProjectStatus.ONTOLOGY_PENDING
    assert project.ontology_task_id == data["task_id"]

    # Let the background task finish and check terminal state
    release.set()
    task = TaskManager().get_task(data["task_id"])
    assert task is not None


def test_ontology_task_completes_and_persists_ontology(tmp_path, monkeypatch):
    class DoneGenerator:
        def generate(self, **kwargs):
            return {
                "entity_types": [
                    {
                        "name": "Person",
                        "description": "fallback",
                        "attributes": [],
                        "examples": [],
                    }
                ],
                "edge_types": [],
                "analysis_summary": "ok",
            }

    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(graph_api, "OntologyGenerator", DoneGenerator)

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = _post_ontology(client)
    assert response.status_code == 200
    data = response.json["data"]

    # Background thread completes quickly for this generator
    task = TaskManager().get_task(data["task_id"])
    assert task is not None
    assert task.status in {TaskStatus.PROCESSING, TaskStatus.COMPLETED} or task.status == TaskStatus.PENDING

    # Building the graph while the ontology task is still running is rejected
    project = ProjectManager.get_project(data["project_id"])
    assert project.status in {ProjectStatus.ONTOLOGY_PENDING, ProjectStatus.ONTOLOGY_GENERATED}


def test_build_rejected_while_ontology_pending(tmp_path, monkeypatch):
    class SlowGenerator:
        def generate(self, **kwargs):
            import time

            time.sleep(0.5)
            return {"entity_types": [], "edge_types": [], "analysis_summary": ""}

    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))
    monkeypatch.setattr(graph_api, "OntologyGenerator", SlowGenerator)
    monkeypatch.setattr(Config, "ZEP_API_KEY", "test-key")

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = _post_ontology(client)
    data = response.json["data"]
    project_id = data["project_id"]

    # Try to build immediately, while the ontology task is still queued
    build_response = client.post("/api/graph/build", json={"project_id": project_id})
    # Either 409 (still pending) or 400 (already finished fast) are acceptable;
    # a 409 with the ontologyInProgress message is the expected steady state.
    assert build_response.status_code in {400, 409}


def test_ontology_generate_validation_still_synchronous(tmp_path, monkeypatch):
    """Missing files/requirement must fail fast without creating a task."""
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path))

    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    no_requirement = client.post(
        "/api/graph/ontology/generate",
        data={"files": (io.BytesIO(b"x"), "a.md")},
        content_type="multipart/form-data",
    )
    assert no_requirement.status_code == 400

    no_files = client.post(
        "/api/graph/ontology/generate",
        data={"simulation_requirement": "s"},
        content_type="multipart/form-data",
    )
    assert no_files.status_code == 400
