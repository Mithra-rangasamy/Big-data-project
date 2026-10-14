"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
tests/test_generators.py - Unit Tests for Deterministic Generators and Synthetic Data
"""

import os
import sys
import json
import csv
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from generators.generate_synthetic import generate_all

def test_deterministic_generator_reproducibility(tmp_path):
    """Seed should ensure identical generation across repeated executions."""
    out_dir_1 = tmp_path / "run1"
    out_dir_2 = tmp_path / "run2"

    generate_all(seed=123, days=3, synthetic_dir=str(out_dir_1 / "synthetic"), sample_dir=str(out_dir_1 / "sample"))
    generate_all(seed=123, days=3, synthetic_dir=str(out_dir_2 / "synthetic"), sample_dir=str(out_dir_2 / "sample"))

    with open(out_dir_1 / "synthetic" / "zones.csv") as f1, open(out_dir_2 / "synthetic" / "zones.csv") as f2:
        assert f1.read() == f2.read()

    with open(out_dir_1 / "synthetic" / "weather.csv") as f1, open(out_dir_2 / "synthetic" / "weather.csv") as f2:
        assert f1.read() == f2.read()

def test_synthetic_data_schema_compliance():
    """Verify synthetic dataset schemas and labeling."""
    zones_path = "data/synthetic/zones.csv"
    weather_path = "data/synthetic/weather.csv"
    symptoms_path = "data/synthetic/symptom_reports.json"

    assert os.path.exists(zones_path)
    assert os.path.exists(weather_path)
    assert os.path.exists(symptoms_path)

    # Check zones
    with open(zones_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert "zone_id" in row
            assert "latitude" in row
            assert "longitude" in row
            assert row["source"] == "synthetic"
            break

    # Check symptom reports
    with open(symptoms_path, mode="r", encoding="utf-8") as f:
        reports = json.load(f)
        assert len(reports) > 100
        first = reports[0]
        assert "report_id" in first
        assert "zone_id" in first
        assert "symptoms" in first
        assert isinstance(first["symptoms"], list)
        assert first["source"] == "synthetic"
