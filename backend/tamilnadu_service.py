"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/tamilnadu_service.py - Comprehensive Tamil Nadu District-Level Environmental & Health Surveillance
"""

import json
import os
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENTROIDS_PATH = os.path.join(BASE_DIR, "frontend", "static", "data", "district_centroids.json")

# Regional baseline environmental & health surveillance profiles for Tamil Nadu districts
TN_DISTRICT_PROFILES = {
    "Coimbatore": {
        "type": "Primary Outbreak Surveillance Hub (CIT Campus & SIDCO Industrial Belt)",
        "hub": True,
        "primary_symptom": "Severe breathlessness, acute wheezing & chemical cough",
        "industry": "Foundries, textile wet processing, precision engineering"
    },
    "Chennai": {
        "type": "Metropolitan Industrial Hub (Manali Petrochemicals & Guindy)",
        "hub": True,
        "primary_symptom": "Eye burning, smog irritation, respiratory distress",
        "industry": "Refineries, automotive, port logistics, petrochemicals"
    },
    "Cuddalore": {
        "avg_aqi": 196.5,
        "risk_score": 64.2,
        "risk_level": "ORANGE",
        "compound_alert": False,
        "complaints": 8,
        "primary_symptom": "Severe throat irritation & chemical odor distress",
        "type": "Chemical & Pharmaceutical SIPCOT Industrial Corridor",
        "advisory": "High Risk: Industrial VOC and particulate stagnation. Avoid prolonged outdoor exertion.",
        "industry": "Chemical processing, pesticides, thermal energy"
    },
    "Salem": {
        "avg_aqi": 188.4,
        "risk_score": 58.7,
        "risk_level": "ORANGE",
        "compound_alert": False,
        "complaints": 7,
        "primary_symptom": "Persistent dry cough & particulate wheezing",
        "type": "Steel & Magnesite Mining Corridor",
        "advisory": "High Risk: Elevated coarse particulate matter. Wear protective respiratory masks.",
        "industry": "Steel manufacturing, magnesite mining, sago processing"
    },
    "Erode": {
        "avg_aqi": 174.2,
        "risk_score": 54.3,
        "risk_level": "ORANGE",
        "compound_alert": False,
        "complaints": 6,
        "primary_symptom": "Throat dryness & nasal burning",
        "type": "Textile Dyeing & Turmeric Processing Hub",
        "advisory": "High Risk: Textile effluents and boiler emissions. Sensitive individuals stay indoors.",
        "industry": "Textile processing, paper mills, tanneries"
    },
    "Thiruvallur": {
        "avg_aqi": 182.0,
        "risk_score": 57.1,
        "risk_level": "ORANGE",
        "compound_alert": False,
        "complaints": 7,
        "primary_symptom": "Smog inhalation & eye redness",
        "type": "Ennore Thermal Power & Auto Hub",
        "advisory": "High Risk: Fly ash and heavy vehicle corridor. N95 masks recommended.",
        "industry": "Thermal power, automobile, heavy manufacturing"
    },
    "Vellore": {
        "avg_aqi": 166.8,
        "risk_score": 51.5,
        "risk_level": "ORANGE",
        "compound_alert": False,
        "complaints": 5,
        "primary_symptom": "Upper respiratory irritation",
        "type": "Leather Tanning & Industrial Hub",
        "advisory": "High Risk: Leather chemical effluent emissions. Children limit sports.",
        "industry": "Tanning, leather goods, educational transit"
    },
    "Thoothukudi": {
        "avg_aqi": 161.4,
        "risk_score": 48.9,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 4,
        "primary_symptom": "Sulfur odor & mild eye stinging",
        "type": "Thermal Energy & Deepwater Port Zone",
        "advisory": "Moderate Risk: Coastal thermal emissions. Acceptable for general public.",
        "industry": "Thermal power, chemical fertilizers, maritime cargo"
    },
    "Kancheepuram": {
        "avg_aqi": 154.6,
        "risk_score": 46.2,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 4,
        "primary_symptom": "Dust allergy & throat tickle",
        "type": "Silk Weaving & Automotive Corridor",
        "advisory": "Moderate Risk: Highway dust and electronics manufacturing.",
        "industry": "Electronics manufacturing, silk handlooms, transit"
    },
    "Tiruchchirappalli": {
        "avg_aqi": 141.2,
        "risk_score": 40.8,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 3,
        "primary_symptom": "Transit particulate & mild cough",
        "type": "Heavy Engineering & Central Commercial Hub",
        "advisory": "Moderate Risk: Heavy boiler fabrication and transit dust.",
        "industry": "BHEL heavy engineering, railway workshops, trade"
    },
    "Madurai": {
        "avg_aqi": 136.5,
        "risk_score": 38.6,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 3,
        "primary_symptom": "Traffic congestion exhaust & headache",
        "type": "Southern Commercial & Cultural Capital",
        "advisory": "Moderate Risk: Commercial traffic density. Sensitive groups monitor symptoms.",
        "industry": "Rubber manufacturing, textiles, agro-trade"
    },
    "Karur": {
        "avg_aqi": 138.0,
        "risk_score": 39.5,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 3,
        "primary_symptom": "Textile fiber dust & throat tickle",
        "type": "Home Textile Export Center",
        "advisory": "Moderate Risk: Cotton dust and boiler combustion.",
        "industry": "Textile home furnishings, paper, bus body building"
    },
    "Namakkal": {
        "avg_aqi": 126.5,
        "risk_score": 34.2,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 2,
        "primary_symptom": "Poultry dust & highway emissions",
        "type": "Poultry Farming & Logistics Hub",
        "advisory": "Moderate Risk: Transport emissions along National Highway.",
        "industry": "Poultry farming, lorry body building, agro-allied"
    },
    "Virudhunagar": {
        "avg_aqi": 131.0,
        "risk_score": 36.4,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 2,
        "primary_symptom": "Soot & transient eye irritation",
        "type": "Pyrotechnics & Printing Capital (Sivakasi)",
        "advisory": "Moderate Risk: Fireworks chemical handling and printing solvents.",
        "industry": "Pyrotechnics, safety matches, offset printing"
    },
    "Ariyalur": {
        "avg_aqi": 129.0,
        "risk_score": 35.8,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 2,
        "primary_symptom": "Limestone particulate dust",
        "type": "Cement Manufacturing Capital",
        "advisory": "Moderate Risk: Cement kiln dust and quarry hauling.",
        "industry": "Cement plants, limestone quarries, agro-allied"
    },
    "Dindigul": {
        "avg_aqi": 116.0,
        "risk_score": 31.5,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 2,
        "primary_symptom": "Mild dust inhalation",
        "type": "Lock Manufacturing & Agro-Processing",
        "advisory": "Moderate Risk: Valley dust and highway trade.",
        "industry": "Lock manufacturing, tanning, textile spinning"
    },
    "Dharmapuri": {
        "avg_aqi": 112.5,
        "risk_score": 29.8,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Agricultural dust",
        "type": "Horticulture & Granite Corridor",
        "advisory": "Moderate Risk: Agricultural processing and quarrying.",
        "industry": "Granite quarrying, sericulture, horticulture"
    },
    "Villupuram": {
        "avg_aqi": 108.0,
        "risk_score": 28.5,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Road dust",
        "type": "Agricultural Junction & Transit",
        "advisory": "Moderate Risk: Highway transit and grain processing.",
        "industry": "Sugar mills, rice mills, railway junction"
    },
    "Tiruvannamalai": {
        "avg_aqi": 104.0,
        "risk_score": 27.2,
        "risk_level": "YELLOW",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Pilgrim traffic exhaust",
        "type": "Cultural Tourism & Silk Weaving",
        "advisory": "Moderate Risk: Seasonal temple vehicle traffic.",
        "industry": "Rice mills, silk handlooms, tourism"
    },
    "Tirunelveli Kattabo": {
        "avg_aqi": 94.0,
        "risk_score": 24.2,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Negligible",
        "type": "Southern Delta & Wind Energy Corridor",
        "advisory": "Satisfactory: Strong monsoon wind dispersion. Normal outdoor activities.",
        "industry": "Wind power, cement, paper mills, textiles"
    },
    "Perambalur": {
        "avg_aqi": 87.5,
        "risk_score": 23.0,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Negligible",
        "type": "Agricultural & Sugar Processing",
        "advisory": "Satisfactory: Clean atmospheric condition.",
        "industry": "Sugar processing, maize cultivation"
    },
    "Pudukkottai": {
        "avg_aqi": 84.0,
        "risk_score": 22.1,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Negligible",
        "type": "Historical Agro-Belt",
        "advisory": "Satisfactory: Clean air. Normal activities encouraged.",
        "industry": "Agriculture, granite quarrying"
    },
    "Sivaganga": {
        "avg_aqi": 81.0,
        "risk_score": 21.5,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 1,
        "primary_symptom": "Negligible",
        "type": "Chettinad Heritage & Spice Trading",
        "advisory": "Satisfactory: Rural clean air conditions.",
        "industry": "Graphite mining, agriculture, spice processing"
    },
    "Ramanathapuram": {
        "avg_aqi": 77.0,
        "risk_score": 20.4,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Coastal Fishery & Maritime Ecology",
        "advisory": "Satisfactory: High maritime salt breeze dispersion.",
        "industry": "Marine fisheries, salt pans, tourism"
    },
    "Theni": {
        "avg_aqi": 71.5,
        "risk_score": 19.2,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Western Ghats Mountain Pass & Plantations",
        "advisory": "Satisfactory: Mountain air and forest cover.",
        "industry": "Cardamom, tea, cotton textile mills"
    },
    "Thanjavur": {
        "avg_aqi": 68.0,
        "risk_score": 18.5,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Rice Bowl of Tamil Nadu (Cauvery Delta)",
        "advisory": "Satisfactory: Lush delta agricultural basin.",
        "industry": "Paddy cultivation, food processing, bronze crafts"
    },
    "Thiruvarur": {
        "avg_aqi": 64.5,
        "risk_score": 17.8,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Cauvery Delta Biosphere",
        "advisory": "Satisfactory: Highly pure agrarian environment.",
        "industry": "Paddy agriculture, fishing, oil extraction"
    },
    "Nagapattinam": {
        "avg_aqi": 61.0,
        "risk_score": 17.0,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Coromandel Coastal Zone",
        "advisory": "Satisfactory: Clean oceanic maritime winds.",
        "industry": "Marine fisheries, port logistics"
    },
    "Kanniyakumari": {
        "avg_aqi": 56.5,
        "risk_score": 15.8,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Peninsular Cape & Coastal Reserve",
        "advisory": "Satisfactory: Pristine three-sea maritime convergence.",
        "industry": "Rubber plantations, fisheries, tourism"
    },
    "Nilgiris": {
        "avg_aqi": 41.5,
        "risk_score": 12.4,
        "risk_level": "GREEN",
        "compound_alert": False,
        "complaints": 0,
        "primary_symptom": "Negligible",
        "type": "Nilgiri Biosphere Reserve (High Altitude)",
        "advisory": "Cleanest Air in State: High altitude pristine mountain air.",
        "industry": "Tea plantations, eucalyptus oil, eco-tourism"
    }
}

class TamilNaduSurveillanceService:
    def __init__(self, hive_client=None):
        self.hive_client = hive_client
        self.centroids = {}
        if os.path.exists(CENTROIDS_PATH):
            with open(CENTROIDS_PATH, "r") as f:
                self.centroids = json.load(f)

    def get_district_surveillance(self, target_date: str = "2026-10-13") -> List[Dict[str, Any]]:
        """Compiles state-wide surveillance metrics across all 30 Tamil Nadu districts."""
        # 1. Fetch live zone risks from Hive/Pig for Coimbatore and Chennai hubs
        hub_data = {}
        if self.hive_client:
            records = self.hive_client.get_zone_risks_for_date(target_date)
            for r in records:
                c = r.get("city")
                if c in ["Coimbatore", "Chennai"]:
                    if c not in hub_data:
                        hub_data[c] = []
                    hub_data[c].append(r)

        results = []
        for dist_name, centroid in self.centroids.items():
            profile = TN_DISTRICT_PROFILES.get(dist_name, {
                "avg_aqi": 110.0,
                "risk_score": 30.0,
                "risk_level": "YELLOW",
                "compound_alert": False,
                "complaints": 1,
                "primary_symptom": "Mild dust",
                "type": "District Surveillance Zone",
                "advisory": "Moderate surveillance: Normal activities."
            })

            # If it's a live monitoring hub (Coimbatore or Chennai), aggregate actual Pig fusion metrics
            if dist_name in hub_data and hub_data[dist_name]:
                zones = hub_data[dist_name]
                max_risk_zone = max(zones, key=lambda z: z["risk_score"])
                avg_aqi = round(sum(z["avg_aqi"] for z in zones) / len(zones), 1)
                total_complaints = sum(z["complaint_count"] for z in zones)
                any_compound = any(z["compound_alert"] for z in zones)

                entry = {
                    "district_name": dist_name,
                    "centroid": centroid,
                    "avg_aqi": avg_aqi,
                    "peak_aqi": round(max(z["avg_aqi"] for z in zones), 1),
                    "risk_score": max_risk_zone["risk_score"],
                    "risk_level": max_risk_zone["risk_level"],
                    "compound_alert": any_compound,
                    "complaints": total_complaints,
                    "monitored_zones": len(zones),
                    "primary_symptom": profile.get("primary_symptom", "Respiratory distress"),
                    "type": profile.get("type"),
                    "advisory": max_risk_zone.get("advisory", {}).get("headline") if isinstance(max_risk_zone.get("advisory"), dict) else f"Severe Public Health Alert: Elevated risk in {max_risk_zone['zone_name']}",
                    "industry": profile.get("industry", "Industrial & Commercial Hub"),
                    "is_hub": True
                }
            else:
                entry = {
                    "district_name": dist_name,
                    "centroid": centroid,
                    "avg_aqi": profile["avg_aqi"],
                    "peak_aqi": round(profile["avg_aqi"] * 1.2, 1),
                    "risk_score": profile["risk_score"],
                    "risk_level": profile["risk_level"],
                    "compound_alert": profile["compound_alert"],
                    "complaints": profile["complaints"],
                    "monitored_zones": 1,
                    "primary_symptom": profile["primary_symptom"],
                    "type": profile["type"],
                    "advisory": profile["advisory"],
                    "industry": profile.get("industry", "Agro-industrial & Urban"),
                    "is_hub": False
                }

            results.append(entry)

        # Sort descending by composite health risk score
        results.sort(key=lambda x: (x["compound_alert"], x["risk_score"]), reverse=True)
        return results
