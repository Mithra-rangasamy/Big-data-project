"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
tests/test_fusion_formula.py - Unit Tests for Composite Risk Formula and Escalation Logic
"""

import pytest

def calculate_risk(avg_aqi: float, complaint_density: float, aqi_trend: float) -> tuple[float, str, str, bool]:
    """Calculates risk score (0-100), base level, final level, and escalation flag.
    Formula:
      aqi_score = min(avg_aqi / 500.0, 1.0) * 100.0
      complaint_score = min(complaint_density, 1.0) * 100.0
      trend_score = min(aqi_trend, 1.0) * 100.0
      risk = 0.50 * aqi_score + 0.35 * complaint_score + 0.15 * trend_score
    """
    aqi_score = min(max(avg_aqi, 0.0) / 500.0, 1.0) * 100.0
    complaint_score = min(max(complaint_density, 0.0), 1.0) * 100.0
    trend_score = min(max(aqi_trend, 0.0), 1.0) * 100.0

    raw_risk = 0.50 * aqi_score + 0.35 * complaint_score + 0.15 * trend_score

    # Base level
    if raw_risk < 25.0:
        base_level = "GREEN"
    elif raw_risk < 50.0:
        base_level = "YELLOW"
    elif raw_risk < 75.0:
        base_level = "ORANGE"
    else:
        base_level = "RED"

    # Escalation condition: rising AQI (aqi_score >= 50.0) AND rising complaints (complaint_score >= 40.0)
    escalated = (aqi_score >= 50.0 and complaint_score >= 40.0)

    # Tier escalation
    if escalated:
        escalation_map = {
            "GREEN": "YELLOW",
            "YELLOW": "ORANGE",
            "ORANGE": "RED",
            "RED": "RED"
        }
        final_level = escalation_map[base_level]
    else:
        final_level = base_level

    return round(raw_risk, 2), base_level, final_level, escalated

def test_clean_baseline_risk():
    """Clean air zone should remain GREEN with low score."""
    risk, base, final, esc = calculate_risk(avg_aqi=45.0, complaint_density=0.05, aqi_trend=0.10)
    assert risk < 25.0
    assert base == "GREEN"
    assert final == "GREEN"
    assert esc is False

def test_outbreak_escalation():
    """High AQI + High complaints must trigger alert level promotion to ORANGE or RED."""
    risk, base, final, esc = calculate_risk(avg_aqi=320.0, complaint_density=0.85, aqi_trend=0.75)
    # aqi_score = 64.0, complaint_score = 85.0, trend_score = 75.0
    # risk = 0.50*64 + 0.35*85 + 0.15*75 = 32.0 + 29.75 + 11.25 = 73.0 (Base: ORANGE)
    assert esc is True
    assert base == "ORANGE"
    assert final == "RED" # Escalated from ORANGE to RED!

def test_decoy_case_high_aqi_low_complaints():
    """Decoy 1: High AQI but zero complaints should stay lower than outbreak and NOT escalate."""
    risk_decoy, base_decoy, final_decoy, esc_decoy = calculate_risk(avg_aqi=320.0, complaint_density=0.05, aqi_trend=0.20)
    risk_outbreak, _, final_outbreak, _ = calculate_risk(avg_aqi=320.0, complaint_density=0.85, aqi_trend=0.75)
    
    assert esc_decoy is False
    assert risk_decoy < risk_outbreak
    assert final_decoy != "RED"

def test_decoy_case_low_aqi_complaint_spike():
    """Decoy 2: Low AQI with brief complaint spike should NOT trigger outbreak escalation."""
    risk, base, final, esc = calculate_risk(avg_aqi=60.0, complaint_density=0.70, aqi_trend=0.10)
    # aqi_score = 12.0 (< 50.0) -> Escalation requires BOTH rising AQI and complaints
    assert esc is False
    assert final in ["GREEN", "YELLOW"]
