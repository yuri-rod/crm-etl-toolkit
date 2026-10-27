"""Exercise the supported backend with synthetic files and no external services."""

import importlib.util
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
from fastapi.testclient import TestClient

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "backend"))
import api_server
from unificado import UnifiedCRMPipeline


@pytest.fixture
def api(monkeypatch, tmp_path):
    monkeypatch.setattr(api_server.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setitem(api_server.app_state, "pipelines", {})
    monkeypatch.setattr(api_server.BackgroundTasks, "add_task", Mock())
    return TestClient(api_server.app)


def test_uploads_in_same_second_keep_separate_files(api, monkeypatch, tmp_path):
    class FixedTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 1, 1)

    monkeypatch.setattr(api_server, "datetime", FixedTime)
    ids = []
    for content in [b"nome,email\nFirst,first@example.com\n", b"nome,email\nSecond,second@example.com\n"]:
        response = api.post("/pipeline/execute", data={"mode": "train"}, files={"file": ("leads.csv", content)})
        assert response.status_code == 200
        ids.append(response.json()["pipeline_id"])
    assert len(set(ids)) == 2
    uploads = list((tmp_path / "crm_etl").glob("*.csv"))
    assert len(uploads) == 2
    assert len({path.read_bytes() for path in uploads}) == 2


def test_cleanup_preserves_active_recent_and_unrelated_files(api, tmp_path):
    root = tmp_path / "crm_etl"
    root.mkdir()
    output = root / "output"
    output.mkdir()
    old = (datetime.now() - timedelta(days=3)).isoformat()
    recent = datetime.now().isoformat()
    states = {
        "pipeline_active": {"status": "processando", "start_time": old},
        "pipeline_recent": {"status": "concluida", "start_time": recent},
        "pipeline_expired": {"status": "erro", "start_time": old},
    }
    api_server.app_state["pipelines"].update(states)
    for job in states:
        (root / f"{job}_leads.csv").write_text("synthetic input")
        (output / f"{job}_result.csv").write_text("synthetic output")
    (root / "unrelated.csv").write_text("unrelated")
    response = api.delete("/admin/cleanup")
    assert response.status_code == 200
    assert response.json()["cleaned_pipelines"] == 1
    assert response.json()["cleaned_files"] == 2
    assert set(api_server.app_state["pipelines"]) == {"pipeline_active", "pipeline_recent"}
    assert (root / "pipeline_active_leads.csv").exists()
    assert (output / "pipeline_recent_result.csv").exists()
    assert (root / "unrelated.csv").exists()
    assert not (root / "pipeline_expired_leads.csv").exists()


@pytest.mark.parametrize("data,filename", [
    ({"mode": "unknown"}, "leads.csv"),
    ({"mode": "train", "output_filename": "../result.csv"}, "leads.csv"),
    ({"mode": "train"}, "../leads.csv"),
    ({"mode": "train"}, "leads.exe"),
])
def test_invalid_jobs_are_rejected_before_writing(api, tmp_path, data, filename):
    response = api.post("/pipeline/execute", data=data, files={"file": (filename, b"synthetic")})
    assert response.status_code == 400
    assert not api_server.app_state["pipelines"]
    assert not list(tmp_path.rglob("*.csv"))


def test_launcher_finds_backend_from_another_directory(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("crm_launcher", PROJECT / "start_crm_system.py")
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    monkeypatch.chdir(tmp_path)
    assert launcher.check_backend_files()
    run = Mock(return_value=subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(launcher.subprocess, "run", run)
    launcher.start_server()
    assert run.call_args.kwargs["cwd"] == PROJECT / "backend"
    assert Path.cwd() == tmp_path


def test_cli_failure_has_nonzero_exit(tmp_path):
    result = subprocess.run([
        sys.executable, str(PROJECT / "backend" / "unificado.py"), "train",
        "--data", str(tmp_path / "missing.csv"), "--model-dir", str(tmp_path / "models"),
    ], capture_output=True, text=True)
    assert result.returncode != 0


def test_csv_identifiers_keep_leading_zeroes_and_latest_record(tmp_path):
    source = tmp_path / "leads.csv"
    source.write_text(
        "cpf,nome,empresa_cargo,email,linkedin,whatsapp,data_cadastro\n"
        "00123456789,Old Example,Engineer,old@example.com,,5511000000000,2024-01-01\n"
        "00123456789,New Example,Engineer,new@example.com,,5511000000000,2024-02-01\n"
        "00987654321,Other Example,Analyst,other@example.com,,5511000000001,2024-01-15\n"
    )
    pipeline = UnifiedCRMPipeline(str(tmp_path / "models"), enable_api_calls=False)
    result = pipeline.run_etl(str(source))
    assert set(result["cpf"]) == {"00123456789", "00987654321"}
    assert result.loc[result["cpf"] == "00123456789", "email"].item() == "new@example.com"
    assert result["has_email"].tolist() == [1, 1]


def test_training_preserves_original_labels(tmp_path):
    pipeline = UnifiedCRMPipeline(str(tmp_path / "models"), enable_api_calls=False)
    data = pipeline._engineer_features(pd.DataFrame({
        "nome": ["Example One", "Example Two", "Example Three", "Example Four"],
        "email": ["one@example.com", "", "three@example.com", ""],
        "qualidade_lead": ["alta", "baixa", "alta", "baixa"],
    }))
    before = data.copy(deep=True)
    pipeline.train_model(data)
    pd.testing.assert_frame_equal(data, before)


def test_numeric_data_quality_column_is_not_a_timestamp(tmp_path):
    pipeline = UnifiedCRMPipeline(str(tmp_path / "models"), enable_api_calls=False)
    data = pd.DataFrame({
        "cpf": ["00123456789", "00123456789"],
        "email": ["first@example.com", "second@example.com"],
        "data_quality_score": [1, 3],
    })
    result = pipeline._clean_data(data)
    assert result["email"].item() == "first@example.com"


def test_api_training_and_download_with_synthetic_data(monkeypatch, tmp_path):
    monkeypatch.setattr(api_server.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setitem(api_server.app_state, "pipelines", {})
    client = TestClient(api_server.app)
    content = (
        "nome,email,qualidade_lead\n"
        "Example One,one@example.com,alta\nExample Two,,baixa\n"
        "Example Three,three@example.com,alta\nExample Four,,baixa\n"
    )
    response = client.post("/pipeline/execute", data={
        "mode": "train", "model_dir": str(tmp_path / "models"),
    }, files={"file": ("leads.csv", content)})
    assert response.status_code == 200
    pipeline_id = response.json()["pipeline_id"]
    status = client.get(f"/pipeline/status/{pipeline_id}").json()
    assert status["status"] == "concluida", status
    download = client.get(f"/download/{pipeline_id}")
    assert download.status_code == 200
    assert "data_quality_score" in download.text
    assert len(download.text.strip().splitlines()) == 5
    assert (tmp_path / "models" / "model_pipeline.joblib").is_file()


def test_offline_demo_uses_pipeline_and_preserves_existing_output(tmp_path):
    output = tmp_path / "cleaned.csv"
    command = [sys.executable, str(PROJECT / "examples" / "offline_demo.py"), "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert "Input: 3 rows; output: 2 leads" in result.stdout
    assert "00123456789,new@example.com,2" in result.stdout
    original = output.read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert output.read_bytes() == original
