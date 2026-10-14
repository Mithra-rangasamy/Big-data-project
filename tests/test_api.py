import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["services"]["mongodb"] == "UP"
    assert "UP" in data["services"]["hiveserver2"]
    assert data["services"]["hadoop_hdfs"] == "UP"
    print("✓ test_health passed")

def test_zones_risk():
    res = requests.get(f"{BASE_URL}/api/zones/risk")
    assert res.status_code == 200
    data = res.json()
    assert data["total_zones"] == 25
    top = data["data"][0]
    assert "dominant_pollutant" in top
    assert "advisory" in top
    print(f"✓ test_zones_risk passed (Top: {top['zone_name']} - Risk {top['risk_score']})")

def test_pollutants_feature_a():
    res = requests.get(f"{BASE_URL}/api/zones/CBE_ZN_01/pollutants")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["zone_id"] == "CBE_ZN_01"
    assert "dominant_pollutant" in data
    assert "pm25" in data["pollutants"]
    assert "pm10" in data["pollutants"]
    assert data["pollutants"]["pm25"]["standard"] == 60.0
    print(f"✓ test_pollutants_feature_a passed (Dominant: {data['dominant_pollutant_name']} ratio {data['dominant_ratio']}x)")

def test_vulnerable_group_advisories_feature_b_k():
    # Test Tamil pediatric advisory
    res = requests.get(f"{BASE_URL}/api/advisory?zone=CBE_ZN_01&group=children&lang=ta")
    assert res.status_code == 200
    data = res.json()
    adv = data["advisory"]
    assert adv["language"] == "ta"
    assert adv["demographic_group"] == "children"
    assert len(adv["headline"]) > 0
    assert len(adv["group_guidance"]) > 0

    # Test Hindi asthma advisory
    res_hi = requests.get(f"{BASE_URL}/api/advisory?zone=CBE_ZN_01&group=asthma_cardiac&lang=hi")
    assert res_hi.status_code == 200
    adv_hi = res_hi.json()["advisory"]
    assert adv_hi["language"] == "hi"
    assert adv_hi["demographic_group"] == "asthma_cardiac"
    print("✓ test_vulnerable_group_advisories_feature_b_k passed (Tamil & Hindi verified)")

def test_sensor_freshness_feature_f():
    res = requests.get(f"{BASE_URL}/api/freshness")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_stations"] == 25
    sample = data["data"][0]
    assert "freshness_pct" in sample
    assert "last_reading_timestamp" in sample
    print("✓ test_sensor_freshness_feature_f passed")

def test_anomalies_feature_c():
    res = requests.get(f"{BASE_URL}/api/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_anomalies"] > 0
    spike = data["data"][0]
    assert abs(spike["z_score"]) >= 2.0
    assert spike["spike"] is True
    print(f"✓ test_anomalies_feature_c passed ({data['total_anomalies']} spikes detected)")

def test_lag_correlation_feature_d():
    res = requests.get(f"{BASE_URL}/api/correlation")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "overall" in data
    assert "lag_0" in data["overall"]
    assert "lag_1" in data["overall"]
    assert "optimal_lag_days" in data["overall"]
    print(f"✓ test_lag_correlation_feature_d passed (Peak correlation r={data['overall']['peak_correlation']} at lag {data['overall']['optimal_lag_days']} days)")

def test_complaint_quality_filter_feature_e():
    # 1. Test spam rejection (< 4 chars)
    spam_payload = {
        "zone_id": "CBE_ZN_01",
        "citizen_name": "Spammer",
        "symptoms": ["cough"],
        "severity": "mild",
        "description": "bad"
    }
    res_spam = requests.post(f"{BASE_URL}/api/complaints", json=spam_payload)
    assert res_spam.status_code == 422
    data_spam = res_spam.json()
    assert data_spam["status"] == "rejected"
    assert "SPAM" in data_spam["rejection_reason"]

    # 2. Test valid submission
    valid_payload = {
        "zone_id": "CBE_ZN_01",
        "citizen_name": "Valid Citizen Test",
        "symptoms": ["cough", "shortness_of_breath"],
        "severity": "severe",
        "description": "Legitimate symptom report with high fever and respiratory distress."
    }
    res_valid = requests.post(f"{BASE_URL}/api/complaints", json=valid_payload)
    assert res_valid.status_code == 201
    data_valid = res_valid.json()
    assert data_valid["status"] == "success"

    # Clean up test complaint
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://localhost:27017/")
        client["air_quality_ews"]["symptom_reports"].delete_one({"report_id": data_valid["report_id"]})
        client["air_quality_ews"]["rejected_reports"].delete_one({"report_id": data_spam["report_id"]})
        client.close()
    except Exception:
        pass

    print("✓ test_complaint_quality_filter_feature_e passed (Spam rejection & clean routing verified)")

def test_pipeline_status_feature_g():
    res = requests.get(f"{BASE_URL}/api/pipeline/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["total_runs"] > 0
    latest = data["latest_run"]
    assert latest["status"] == "SUCCESS"
    assert len(latest["stages"]) == 3
    print("✓ test_pipeline_status_feature_g passed")

def test_forecast_feature_h():
    res = requests.get(f"{BASE_URL}/api/forecast/CBE_ZN_01")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["hourly_forecast"]) == 24
    assert "predicted_avg_aqi" in data
    assert "momentum_direction" in data
    print(f"✓ test_forecast_feature_h passed (Predicted 24h average AQI: {data['predicted_avg_aqi']})")

def test_alerts_history_feature_i():
    res = requests.get(f"{BASE_URL}/api/alerts")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    print(f"✓ test_alerts_history_feature_i passed ({data['total_alerts']} alerts logged)")

def test_nearby_facilities_feature_j():
    res = requests.get(f"{BASE_URL}/api/facilities/nearby?zone=CBE_ZN_01")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["nearest_emergency_hospital"] is not None
    assert data["nearest_emergency_hospital"]["emergency_available"] is True
    print(f"✓ test_nearby_facilities_feature_j passed (Nearest: {data['nearest_emergency_hospital']['name']}, {data['nearest_emergency_hospital']['distance_km']} km)")

def test_csv_export_feature_l():
    res = requests.get(f"{BASE_URL}/api/export/ranking.csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]
    lines = res.text.strip().split("\n")
    assert len(lines) >= 26  # Header + 25 zones
    assert "Rank,Zone_ID,Zone_Name" in lines[0]
    print(f"✓ test_csv_export_feature_l passed ({len(lines)} CSV lines generated)")

def test_html_pages_feature_m_g_i_o():
    for page in ["/", "/check", "/status", "/alerts", "/login"]:
        res = requests.get(f"{BASE_URL}{page}")
        assert res.status_code == 200, f"Page {page} returned {res.status_code}"
    print("✓ test_html_pages_feature_m_g_i_o passed (All web templates active)")

if __name__ == "__main__":
    print("======================================================================")
    print("RUNNING COMPREHENSIVE EWS TEST SUITE (FEATURES A THROUGH O)")
    print("======================================================================")
    test_health()
    test_zones_risk()
    test_pollutants_feature_a()
    test_vulnerable_group_advisories_feature_b_k()
    test_sensor_freshness_feature_f()
    test_anomalies_feature_c()
    test_lag_correlation_feature_d()
    test_complaint_quality_filter_feature_e()
    test_pipeline_status_feature_g()
    test_forecast_feature_h()
    test_alerts_history_feature_i()
    test_nearby_facilities_feature_j()
    test_csv_export_feature_l()
    test_html_pages_feature_m_g_i_o()
    print("======================================================================")
    print("ALL 14 TEST SUITES PASSED CLEANLY! ALL FEATURES A-O VERIFIED!")
    print("======================================================================")
