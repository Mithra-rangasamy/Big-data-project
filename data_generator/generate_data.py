#!/usr/bin/env python3
"""
CIT 21MDS56: Air Quality & Public Health Early-Warning System
data_generator/generate_data.py
Generates 30 days of multi-modal, hourly synthetic environmental telemetry
and citizen health complaint records across 5 cities and 25 zones.
"""

import os
import json
import random
import uuid
from datetime import datetime, timedelta

# Seed for reproducibility while allowing dynamic expansion
random.seed(42)

COMPLAINT_TEMPLATES = [
    ("breathing difficulty", "Struggling to catch my breath since morning. The air feels so heavy and toxic near the main road."),
    ("chest pain", "Severe chest tightness and persistent burning sensation in my lungs while walking outside."),
    ("eye irritation", "Extreme eye stinging and redness. Can barely keep my eyes open due to thick haze."),
    ("cough", "Uncontrollable dry cough and scratching throat for the past 4 hours."),
    ("headache", "Splitting headache and nausea from the foul chemical smell hanging in the air."),
    ("smog", "Visibility is under 100 meters, thick acrid smog engulfing the entire neighbourhood."),
    ("breathing difficulty,cough", "Both my elderly parents and I are experiencing acute wheezing and coughing fits."),
    ("eye irritation,headache", "Burning sensation in eyes accompanied by terrible sinus headache after stepping outdoors.")
]

CITIZEN_NAMES = ["Ramesh K", "Priya S", "Anand M", "Deepa V", "Karthik R", "Sneha B", "Arun Kumar", "Meera N", "Vijay P", "Divya T"]

def load_zones(config_path):
    with open(config_path, "r") as f:
        return json.load(f)

def generate_hourly_telemetry(days=30, end_date=None):
    if end_date is None:
        end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "zones.json")
    if not os.path.exists(config_path):
        config_path = os.path.expanduser("~/air-quality-ews/config/zones.json")
    cities_data = load_zones(config_path)
    
    aqi_records = []
    weather_records = []
    complaints = []
    social_posts = []

    total_hours = days * 24
    
    for city_obj in cities_data:
        city = city_obj["city"]
        for zone in city_obj["zones"]:
            zone_id = zone["zone_id"]
            zone_name = zone["zone_name"]
            scenario = zone.get("scenario", "moderate")
            baseline_comp = zone.get("baseline_complaints_per_day", 2.0)

            # Generate hour by hour
            for h in range(total_hours):
                current_time = start_date + timedelta(hours=h)
                date_str = current_time.strftime("%Y-%m-%d")
                timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
                hour = current_time.hour
                day_offset = (current_time - start_date).days

                # Diurnal traffic variation (peaks at 8-10 AM and 6-9 PM)
                if hour in [8, 9, 10, 18, 19, 20]:
                    diurnal_factor = 1.35
                elif hour in [1, 2, 3, 4]:
                    diurnal_factor = 0.70
                else:
                    diurnal_factor = 1.0

                # Base values by scenario
                if scenario == "outbreak_sensitive":
                    # Spikes dramatically in last 10 days
                    if day_offset >= 20:
                        base_aqi = 280 + (day_offset - 20) * 16 + random.uniform(-20, 35)
                        wind_speed = random.uniform(1.5, 4.5) # Stagnation
                    else:
                        base_aqi = 130 + random.uniform(-15, 25)
                        wind_speed = random.uniform(5.0, 12.0)
                elif scenario == "false_alarm":
                    # Elevated AQI throughout, but good ventilation / no health panic
                    base_aqi = 240 + random.uniform(-25, 45)
                    wind_speed = random.uniform(7.0, 15.0)
                elif scenario == "clean_baseline":
                    base_aqi = 45 + random.uniform(-10, 20)
                    wind_speed = random.uniform(8.0, 18.0)
                elif scenario == "traffic_congestion":
                    base_aqi = 160 + random.uniform(-20, 40)
                    wind_speed = random.uniform(4.0, 10.0)
                else: # moderate
                    base_aqi = 100 + random.uniform(-15, 30)
                    wind_speed = random.uniform(6.0, 14.0)

                aqi = int(max(15, min(500, base_aqi * diurnal_factor)))
                pm25 = round(aqi * 0.65 + random.uniform(-5, 10), 2)
                pm10 = round(aqi * 1.15 + random.uniform(-10, 15), 2)
                no2 = round(aqi * 0.28 + random.uniform(-3, 6), 2)
                so2 = round(aqi * 0.12 + random.uniform(-2, 4), 2)
                co = round(aqi * 0.015 + random.uniform(-0.2, 0.4), 2)
                o3 = round(max(5, 50 - (aqi * 0.05) + random.uniform(-5, 5)), 2)

                temp = round(26.0 + 6.0 * random.uniform(-1, 1) - (3.0 if hour < 6 else 0), 1)
                humidity = round(max(30.0, min(95.0, 65.0 + random.uniform(-20, 20))), 1)
                wind_dir = round(random.uniform(0, 360), 1)

                rec_id = f"AQI_{zone_id}_{current_time.strftime('%Y%m%d%H')}"
                aqi_records.append({
                    "record_id": rec_id,
                    "city": city,
                    "zone_id": zone_id,
                    "zone_name": zone_name,
                    "timestamp": timestamp_str,
                    "aqi": aqi,
                    "pm25": pm25,
                    "pm10": pm10,
                    "no2": no2,
                    "so2": so2,
                    "co": co,
                    "o3": o3,
                    "date_str": date_str,
                    "hour": hour
                })

                w_id = f"WX_{zone_id}_{current_time.strftime('%Y%m%d%H')}"
                weather_records.append({
                    "record_id": w_id,
                    "city": city,
                    "zone_id": zone_id,
                    "timestamp": timestamp_str,
                    "temp": temp,
                    "humidity": humidity,
                    "wind_speed": round(wind_speed, 1),
                    "wind_direction": wind_dir,
                    "date_str": date_str,
                    "hour": hour
                })

                # Complaint Generation Probability per hour
                if scenario == "outbreak_sensitive" and day_offset >= 20:
                    prob_comp = 0.55 # ~13 complaints / day
                    prob_social = 0.40 # ~10 social posts / day
                elif scenario == "false_alarm":
                    prob_comp = 0.05 # Low despite high AQI (~1.2 / day)
                    prob_social = 0.06
                elif scenario == "clean_baseline":
                    prob_comp = 0.02 # Minimal (~0.5 / day)
                    prob_social = 0.02
                else:
                    prob_comp = baseline_comp / 24.0
                    prob_social = (baseline_comp * 0.8) / 24.0

                if random.random() < prob_comp:
                    symp, text = random.choice(COMPLAINT_TEMPLATES)
                    sev = random.randint(3, 5) if (scenario == "outbreak_sensitive" and day_offset >= 20) else random.randint(1, 3)
                    complaints.append({
                        "report_id": f"CMP_{uuid.uuid4().hex[:10]}",
                        "city": city,
                        "zone_id": zone_id,
                        "zone_name": zone_name,
                        "timestamp": timestamp_str,
                        "date_str": date_str,
                        "symptoms": [s.strip() for s in symp.split(",")],
                        "severity": sev,
                        "text": text,
                        "source": "citizen_form",
                        "reported_by": random.choice(CITIZEN_NAMES),
                        "latitude": zone["latitude"] + random.uniform(-0.005, 0.005),
                        "longitude": zone["longitude"] + random.uniform(-0.005, 0.005)
                    })

                if random.random() < prob_social:
                    symp, text = random.choice(COMPLAINT_TEMPLATES)
                    social_posts.append({
                        "post_id": f"SOC_{uuid.uuid4().hex[:10]}",
                        "city": city,
                        "zone_id": zone_id,
                        "zone_name": zone_name,
                        "timestamp": timestamp_str,
                        "date_str": date_str,
                        "symptoms": [s.strip() for s in symp.split(",")],
                        "sentiment_score": -0.8 if "breathing" in symp else -0.4,
                        "text": f"#{city}AirQuality #{zone_name}: {text}",
                        "source": "social_feed",
                        "user_handle": f"@{random.choice(CITIZEN_NAMES).replace(' ', '').lower()}{random.randint(10,99)}"
                    })

    return aqi_records, weather_records, complaints, social_posts

if __name__ == "__main__":
    print("Generating 30 days of synthetic data...")
    aqi_recs, wx_recs, comps, socs = generate_hourly_telemetry(days=30)
    print(f"Generated: {len(aqi_recs)} AQI records, {len(wx_recs)} Weather records, {len(comps)} Citizen complaints, {len(socs)} Social posts.")
