from pathlib import Path
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from src.main.app import app
from src.main.utils import fleet_generator


def test_auto_generate_fleet_assets_creates_pngs_and_pdf(
    tmp_path: Path, 
    monkeypatch: pytest.MonkeyPatch
):
    """
    Unit Test:
    1. Redirects ASSETS_OUTPUT_DIR to a temporary test directory.
    2. Runs auto_generate_fleet_assets for a 4-seat test taxi.
    3. Verifies all 4 PNG files and 1 multi-page PDF manifest exist and are valid.
    """
    # Redirect file output to pytest's temporary directory
    monkeypatch.setattr(fleet_generator, "ASSETS_OUTPUT_DIR", tmp_path)

    vehicle_id = "TAXI-GP-TEST"
    seat_count = 4

    result = fleet_generator.auto_generate_fleet_assets(
        vehicle_id=vehicle_id, 
        seat_count=seat_count
    )

    expected_dir = tmp_path / vehicle_id
    assert expected_dir.exists()
    assert result["vehicle_id"] == vehicle_id
    assert result["stickers_generated"] == seat_count

    # 1. Verify each individual seat PNG exists and is a valid image
    for seat_num in range(1, seat_count + 1):
        png_file = expected_dir / f"seat_{seat_num:02d}_qr.png"
        assert png_file.exists(), f"Missing QR PNG for seat {seat_num}"
        assert png_file.stat().st_size > 0

        with Image.open(png_file) as img:
            assert img.format == "PNG"
            assert img.size[0] > 0 and img.size[1] > 0

    # 2. Verify the combined printable PDF manifest exists and has valid PDF header bytes
    pdf_file = expected_dir / f"{vehicle_id}_printable_stickers.pdf"
    assert pdf_file.exists(), "Printable PDF manifest was not created"
    assert pdf_file.stat().st_size > 0
    assert pdf_file.read_bytes().startswith(b"%PDF")


def test_fleet_register_endpoint_triggers_asset_generation(
    tmp_path: Path, 
    monkeypatch: pytest.MonkeyPatch
):
    """
    Integration Test:
    Verifies POST /fleet/register queues and executes auto_generate_fleet_assets.
    """
    monkeypatch.setattr(fleet_generator, "ASSETS_OUTPUT_DIR", tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/fleet/register",
            json={"vehicle_id": "BREE-QUANTUM-01", "seat_count": 3}
        )

    assert response.status_code == 201
    assert response.json()["status"] == "registration_initiated"

    # FastAPI TestClient executes BackgroundTasks synchronously before returning
    vehicle_dir = tmp_path / "BREE-QUANTUM-01"
    assert (vehicle_dir / "seat_01_qr.png").exists()
    assert (vehicle_dir / "seat_02_qr.png").exists()
    assert (vehicle_dir / "seat_03_qr.png").exists()
    assert (vehicle_dir / "BREE-QUANTUM-01_printable_stickers.pdf").exists()
    