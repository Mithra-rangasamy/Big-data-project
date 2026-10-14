"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
tests/test_new_features.py - Verification for Kept Features:
1. Current Location (Geolocation & Haversine resolver)
2. Share Option & Deep Linking (?zone=<id>)
3. Guided Onboarding Tour
"""

import requests
import json

BASE_URL = "http://localhost:5000"


def test_nearest_zone_geolocation():
    """Kept Feature 1: Proximity resolver returns nearest monitored zone within 50 km."""
    # Test coordinates near Coimbatore CIT Campus (11.02, 77.03)
    res = requests.get(f"{BASE_URL}/api/zones/nearest?lat=11.02&lon=77.03")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    nearest = data["nearest_zone"]
    assert nearest["city"] == "Coimbatore"
    assert nearest["distance_km"] < 25.0
    assert data["is_within_50km"] is True

    # Test coordinate far away (e.g., Kanyakumari ~380 km away from monitored hubs)
    res_far = requests.get(f"{BASE_URL}/api/zones/nearest?lat=8.0883&lon=77.5385")
    assert res_far.status_code == 200
    assert res_far.json()["is_within_50km"] is False
    print(f"✓ test_nearest_zone_geolocation passed (Resolved {nearest['zone_name']}, {nearest['distance_km']} km)")


def test_share_deep_link():
    """Kept Feature 2: Dashboard supports ?zone=<id> deep linking and share button."""
    res = requests.get(f"{BASE_URL}/?zone=CBE_ZN_01")
    assert res.status_code == 200
    html = res.text
    assert 'id="btn-share"' in html
    assert 'id="toast-notice"' in html
    print("✓ test_share_deep_link passed")


def test_guided_tour():
    """Kept Feature 3: Guided Tour elements present in dashboard."""
    res = requests.get(f"{BASE_URL}/")
    assert res.status_code == 200
    html = res.text
    assert 'id="btn-start-tour"' in html
    assert 'id="tour-popover"' in html
    assert 'id="tour-btn-next"' in html
    print("✓ test_guided_tour passed")


if __name__ == "__main__":
    test_nearest_zone_geolocation()
    test_share_deep_link()
    test_guided_tour()
    print("\nALL 3 KEPT FEATURE TESTS PASSED SUCCESSFULLY!")
