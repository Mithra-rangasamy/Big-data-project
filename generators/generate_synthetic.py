#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
generators/generate_synthetic.py - Reproducible Synthetic Data Generator

Generates:
1. data/synthetic/zones.csv (Station-to-Zone mapping with realistic coordinates)
2. data/synthetic/weather.csv (Synthetic weather matching OpenWeatherMap flattened shape)
3. data/synthetic/symptom_reports.json (Citizen health complaints with lag-correlated volume, outbreak episodes, decoy cases)
4. data/synthetic/social_posts.json (Curated pollution-related social telemetry)
5. data/sample/* (Small sample files for quick inspection)
"""

import os
import sys
import csv
import json
import random
import uuid
from datetime import datetime, timedelta

# Reference city centroids for deterministic jitter
CITY_CENTROIDS = {
    "Coimbatore": (11.0168, 76.9558),
    "Chennai": (13.0827, 80.2707),
    "Bengaluru": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777)
}

SYMPTOM_CHOICES = [
    "breathing difficulty",
    "cough",
    "eye irritation",
    "throat irritation",
    "headache",
    "chest tightness",
    "skin irritation"
]

AGE_GROUPS = ["children", "young_adult", "adult", "elderly"]

COMPLAINT_TEXTS = {
    "breathing difficulty": "Extremely difficult to catch my breath outdoors today. The smog is choking.",
    "cough": "Persistent hacking cough since morning. Throat feels like sandpaper.",
    "eye irritation": "Severe eye stinging and burning sensation after walking to the metro station.",
    "throat irritation": "Scratchy and painful throat. The air smells acrid and full of particulate dust.",
    "headache": "Throbbing headache and dizziness from the dense traffic haze.",
    "chest tightness": "Heavy pressure on my chest and shallow breathing. Cannot stay outside.",
    "skin irritation": "Itchy skin rashes and facial irritation after exposure to industrial fumes."
}

SOCIAL_KEYWORDS = ["smog", "toxic_air", "cpcb", "aqi_spike", "respiratory", "wear_mask", "inversion"]

def generate_all(seed=42, days=30, raw_dir="data/raw", synthetic_dir="data/synthetic", sample_dir="data/sample"):
    random.seed(seed)
    os.makedirs(synthetic_dir, exist_ok=True)
    os.makedirs(sample_dir, exist_ok=True)

    print(f"Generating synthetic datasets (seed={seed}, days={days})...")

    # 1. Generate Zones from stations.csv or fallback to default metropolitan zones
    stations_file = os.path.join(raw_dir, "stations.csv")
    zones = []
    
    if os.path.exists(stations_file):
        with open(stations_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row.get("City", "").strip()
                if city in CITY_CENTROIDS:
                    lat_c, lon_c = CITY_CENTROIDS[city]
                    lat = round(lat_c + random.uniform(-0.06, 0.06), 4)
                    lon = round(lon_c + random.uniform(-0.06, 0.06), 4)
                    st_id = row.get("StationId", "").strip()
                    st_name = row.get("StationName", "").strip()
                    
                    # Scenario assignment: outbreak, decoy, or normal
                    if "01" in st_id or len(zones) % 7 == 0:
                        scenario = "outbreak_sensitive"
                    elif len(zones) % 5 == 0:
                        scenario = "decoy_high_aqi_low_complaint"
                    elif len(zones) % 6 == 0:
                        scenario = "decoy_low_aqi_spike_complaint"
                    else:
                        scenario = "normal"

                    zones.append({
                        "zone_id": st_id,
                        "zone_name": st_name,
                        "city": city,
                        "state": row.get("State", "").strip(),
                        "latitude": lat,
                        "longitude": lon,
                        "scenario": scenario,
                        "baseline_complaints_per_day": round(random.uniform(1.5, 3.5), 1),
                        "source": "synthetic"
                    })

    # If stations.csv yielded fewer than expected, ensure our core 25 zones are represented
    if len(zones) < 5:
        # Fallback to configured 25 zones
        config_zones = os.path.join("config", "zones.json")
        if os.path.exists(config_zones):
            with open(config_zones, "r") as f:
                cdata = json.load(f)
                for c in cdata:
                    city = c["city"]
                    for z in c["zones"]:
                        zones.append({
                            "zone_id": z["zone_id"],
                            "zone_name": z["zone_name"],
                            "city": city,
                            "state": "Tamil Nadu" if city in ["Coimbatore", "Chennai"] else "State",
                            "latitude": z["latitude"],
                            "longitude": z["longitude"],
                            "scenario": z.get("scenario", "normal"),
                            "baseline_complaints_per_day": z.get("baseline_complaints_per_day", 2.5),
                            "source": "synthetic"
                        })

    # Write data/synthetic/zones.csv
    zones_csv = os.path.join(synthetic_dir, "zones.csv")
    with open(zones_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["zone_id", "zone_name", "city", "state", "latitude", "longitude", "scenario", "baseline_complaints_per_day", "source"])
        writer.writeheader()
        writer.writerows(zones)
    print(f"  -> Written {len(zones)} zones to {zones_csv}")

    # 2. Generate Weather Telemetry (OpenWeatherMap flattened format)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    total_hours = days * 24

    weather_records = []
    symptom_records = []
    social_records = []

    for zone in zones:
        zid = zone["zone_id"]
        city = zone["city"]
        scenario = zone["scenario"]
        baseline_comp = zone["baseline_complaints_per_day"]

        for h in range(total_hours):
            cur_time = start_date + timedelta(hours=h)
            date_str = cur_time.strftime("%Y-%m-%d")
            ts_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
            hour = cur_time.hour
            day_offset = (cur_time - start_date).days

            # Stagnation & temperature seasonality
            # Low wind speed (stagnation) raises PM levels
            if scenario == "outbreak_sensitive" and day_offset >= 20:
                wind_speed = round(random.uniform(1.2, 3.8), 1)  # Atmospheric inversion / stagnation
                ambient_aqi = int(min(490, 240 + (day_offset - 20) * 20 + random.uniform(-15, 25)))
            elif scenario == "decoy_high_aqi_low_complaint":
                wind_speed = round(random.uniform(2.0, 5.0), 1)
                ambient_aqi = int(min(450, 310 + random.uniform(-20, 30)))  # High AQI
            elif scenario == "decoy_low_aqi_spike_complaint":
                wind_speed = round(random.uniform(8.0, 16.0), 1)
                ambient_aqi = int(max(35, 65 + random.uniform(-10, 15)))   # Low AQI
            else:
                wind_speed = round(random.uniform(4.0, 14.0), 1)
                ambient_aqi = int(max(40, 120 + random.uniform(-25, 40)))

            temp = round(28.0 + 5.0 * random.uniform(-1, 1) - (4.0 if hour < 6 else 0), 1)
            humidity = round(max(30.0, min(95.0, 65.0 + random.uniform(-20, 20))), 1)
            wind_dir = round(random.uniform(0, 360), 1)
            pressure = round(1013.25 + random.uniform(-8, 8), 1)

            weather_records.append({
                "record_id": f"WX_{zid}_{cur_time.strftime('%Y%m%d%H')}",
                "city": city,
                "zone_id": zid,
                "timestamp": ts_str,
                "date_str": date_str,
                "hour": hour,
                "temp": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "wind_direction": wind_dir,
                "pressure": pressure,
                "source": "synthetic"
            })

            # Complaint probability based on scenario
            if scenario == "outbreak_sensitive" and day_offset >= 20:
                prob_comp = 0.50   # ~12/day (High complaints + High AQI -> OUTBREAK)
                prob_soc = 0.35
            elif scenario == "decoy_high_aqi_low_complaint":
                prob_comp = 0.04   # ~1/day (High AQI but Low complaints -> DECOY 1)
                prob_soc = 0.03
            elif scenario == "decoy_low_aqi_spike_complaint":
                prob_comp = 0.45 if day_offset >= 25 else 0.05  # Spike with Low AQI -> DECOY 2
                prob_soc = 0.30 if day_offset >= 25 else 0.04
            else:
                prob_comp = (baseline_comp / 24.0) * (ambient_aqi / 150.0)
                prob_soc = prob_comp * 0.7

            if random.random() < prob_comp:
                k_symp = random.randint(1, 3)
                symps = random.sample(SYMPTOM_CHOICES, k_symp)
                primary_symp = symps[0]
                sev = random.randint(3, 5) if (scenario == "outbreak_sensitive" and day_offset >= 20) else random.randint(1, 3)
                symptom_records.append({
                    "report_id": f"REP_{uuid.uuid4().hex[:10]}",
                    "city": city,
                    "zone_id": zid,
                    "timestamp": ts_str,
                    "date": date_str,
                    "symptoms": symps,
                    "severity": sev,
                    "free_text": COMPLAINT_TEXTS.get(primary_symp, "Uncomfortable air quality outside."),
                    "age_group": random.choice(AGE_GROUPS),
                    "source": "synthetic"
                })

            if random.random() < prob_soc:
                k_symp = random.randint(1, 2)
                symps = random.sample(SYMPTOM_CHOICES, k_symp)
                kw = random.sample(SOCIAL_KEYWORDS, 2)
                social_records.append({
                    "post_id": f"SOC_{uuid.uuid4().hex[:10]}",
                    "city": city,
                    "zone_id": zid,
                    "timestamp": ts_str,
                    "date": date_str,
                    "symptoms": symps,
                    "keywords": kw,
                    "text": f"#{city} #{zone['zone_name']}: {COMPLAINT_TEXTS.get(symps[0], 'Smoggy air!')} #{kw[0]} #{kw[1]}",
                    "source": "synthetic"
                })

    # Write weather to synthetic CSV
    weather_csv = os.path.join(synthetic_dir, "weather.csv")
    with open(weather_csv, "w", newline="", encoding="utf-8") as f:
        fields = ["record_id", "city", "zone_id", "timestamp", "date_str", "hour", "temp", "humidity", "wind_speed", "wind_direction", "pressure", "source"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(weather_records)
    print(f"  -> Written {len(weather_records)} weather records to {weather_csv}")

    # Write symptom reports to synthetic JSON
    symptoms_json = os.path.join(synthetic_dir, "symptom_reports.json")
    with open(symptoms_json, "w", encoding="utf-8") as f:
        json.dump(symptom_records, f, indent=2)
    print(f"  -> Written {len(symptom_records)} symptom reports to {symptoms_json}")

    # Write social posts to synthetic JSON
    social_json = os.path.join(synthetic_dir, "social_posts.json")
    with open(social_json, "w", encoding="utf-8") as f:
        json.dump(social_records, f, indent=2)
    print(f"  -> Written {len(social_records)} social posts to {social_json}")

    # Create Samples for sample/ directory (15 rows each)
    def write_sample_csv(src_csv, dst_csv, n=15):
        if os.path.exists(src_csv):
            with open(src_csv, "r", encoding="utf-8") as fi, open(dst_csv, "w", newline="", encoding="utf-8") as fo:
                for idx, line in enumerate(fi):
                    fo.write(line)
                    if idx >= n:
                        break

    write_sample_csv(zones_csv, os.path.join(sample_dir, "zones_sample.csv"))
    write_sample_csv(weather_csv, os.path.join(sample_dir, "weather_sample.csv"))

    with open(os.path.join(sample_dir, "symptoms_sample.json"), "w", encoding="utf-8") as f:
        json.dump(symptom_records[:15], f, indent=2)

    with open(os.path.join(sample_dir, "social_sample.json"), "w", encoding="utf-8") as f:
        json.dump(social_records[:15], f, indent=2)

    # Sample of raw station_hour.csv if available
    raw_station_hour = os.path.join(raw_dir, "station_hour.csv")
    if os.path.exists(raw_station_hour):
        write_sample_csv(raw_station_hour, os.path.join(sample_dir, "aqi_raw_sample.csv"))

    print("Sample datasets committed under data/sample/ successfully.")

if __name__ == "__main__":
    seed_val = 42
    if len(sys.argv) > 1:
        try:
            seed_val = int(sys.argv[1])
        except ValueError:
            pass
    generate_all(seed=seed_val, days=30)
