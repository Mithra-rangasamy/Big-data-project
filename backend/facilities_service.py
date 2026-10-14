"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/facilities_service.py - Emergency Facilities Proximity & Response Coordinator
"""

import json
import math
import os
from typing import Dict, List, Any

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

class FacilitiesService:
    def __init__(self, config_path: str = None):
        if not config_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "facilities.json")
            if not os.path.exists(config_path):
                config_path = os.path.expanduser("~/air-quality-ews/config/facilities.json")
        self.facilities = []
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.facilities = data.get("facilities", [])

    def get_nearby_facilities(self, zone_lat: float, zone_lon: float, max_distance_km: float = 8.0, facility_type: str = None) -> List[Dict[str, Any]]:
        """Returns facilities within radius sorted by distance."""
        results = []
        for fac in self.facilities:
            if facility_type and fac.get("type") != facility_type:
                continue
            flat = fac.get("latitude")
            flon = fac.get("longitude")
            if flat is None or flon is None:
                continue
            dist = haversine_km(zone_lat, zone_lon, flat, flon)
            if dist <= max_distance_km:
                item = dict(fac)
                item["distance_km"] = dist
                results.append(item)

        results.sort(key=lambda x: x["distance_km"])
        return results

    def get_nearest_hospital(self, zone_lat: float, zone_lon: float) -> Dict[str, Any]:
        """Finds the single nearest emergency hospital to a given location."""
        hospitals = self.get_nearby_facilities(zone_lat, zone_lon, max_distance_km=25.0, facility_type="hospital")
        return hospitals[0] if hospitals else None

    def get_facilities_for_zone(self, zone_id: str = None, lat: float = None, lon: float = None, city: str = None, max_distance_km: float = 12.0) -> Dict[str, Any]:
        """Returns structured nearby hospitals, schools, and nearest emergency hospital for a zone."""
        hospitals = self.get_nearby_facilities(lat, lon, max_distance_km=max_distance_km, facility_type="hospital")
        schools = self.get_nearby_facilities(lat, lon, max_distance_km=max_distance_km, facility_type="school")
        nearest_hosp = self.get_nearest_hospital(lat, lon)
        return {
            "status": "success",
            "zone_id": zone_id,
            "city": city,
            "facilities": hospitals + schools,
            "hospitals": hospitals,
            "schools": schools,
            "nearest_emergency_hospital": nearest_hosp
        }
