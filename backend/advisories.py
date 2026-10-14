"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/advisories.py - Rule-based Plain-Language Multilingual and Demographic Health Advisory Generator
Supports Vulnerable Groups (children, elderly, asthmatics, pregnant women, outdoor workers)
and Languages (English, Tamil, Hindi)
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger("AdvisoryEngine")

class AdvisoryEngine:
    def __init__(self, config_path: str = None, advisories_path: str = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not advisories_path:
            advisories_path = os.path.join(base_dir, "config", "advisories.json")
        if not config_path:
            config_path = os.path.join(base_dir, "config", "risk_config.json")

        self.advisories_data = {}
        if os.path.exists(advisories_path):
            try:
                with open(advisories_path, "r", encoding="utf-8") as f:
                    self.advisories_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading advisories.json: {e}")

        self.risk_config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.risk_config = json.load(f)
            except Exception as e:
                logger.error(f"Error loading risk_config.json: {e}")

    def generate_advisory(
        self,
        zone_record: Any = None,
        dominant_pollutant: Optional[str] = None,
        compound_alert: Optional[bool] = None,
        group: str = "general_public",
        lang: str = "en",
        risk_level: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generates structured plain-language advisory tailored to demographic group and language.
        Flexible signature accepting a zone dictionary or discrete parameters.
        """
        if isinstance(zone_record, dict):
            r_level = zone_record.get("risk_level", risk_level or "GREEN")
            r_score = float(zone_record.get("risk_score", kwargs.get("risk_score", 0.0)))
            avg_aqi = float(zone_record.get("avg_aqi", kwargs.get("avg_aqi", 0.0)))
            complaints = int(zone_record.get("complaint_count", kwargs.get("complaint_count", 0)))
            c_alert = zone_record.get("compound_alert", compound_alert if compound_alert is not None else False)
            zone_name = zone_record.get("zone_name", kwargs.get("zone_name", "Zone"))
            city = zone_record.get("city", kwargs.get("city", "City"))
            dom_p = zone_record.get("dominant_pollutant", dominant_pollutant or kwargs.get("dominant_pollutant", "pm25"))
            zid = zone_record.get("zone_id", kwargs.get("zone_id", "ZN_01"))
        elif isinstance(zone_record, str):
            r_level = zone_record
            r_score = float(kwargs.get("risk_score", 0.0))
            avg_aqi = float(kwargs.get("avg_aqi", 0.0))
            complaints = int(kwargs.get("complaint_count", 0))
            c_alert = compound_alert if compound_alert is not None else kwargs.get("compound_alert", False)
            zone_name = kwargs.get("zone_name", "Zone")
            city = kwargs.get("city", "City")
            dom_p = dominant_pollutant or kwargs.get("dominant_pollutant", "pm25")
            zid = kwargs.get("zone_id", "ZN_01")
        else:
            r_level = risk_level or "GREEN"
            r_score = float(kwargs.get("risk_score", 0.0))
            avg_aqi = float(kwargs.get("avg_aqi", 0.0))
            complaints = int(kwargs.get("complaint_count", 0))
            c_alert = compound_alert if compound_alert is not None else kwargs.get("compound_alert", False)
            zone_name = kwargs.get("zone_name", "Zone")
            city = kwargs.get("city", "City")
            dom_p = dominant_pollutant or kwargs.get("dominant_pollutant", "pm25")
            zid = kwargs.get("zone_id", "ZN_01")

        # Normalize group and language
        group = kwargs.get("group", group)
        lang = kwargs.get("lang", lang)

        valid_groups = ["general_public", "children", "elderly", "asthma_cardiac", "pregnant_women", "outdoor_workers"]
        if group not in valid_groups:
            group = "general_public"
        valid_langs = ["en", "ta", "hi"]
        if lang not in valid_langs:
            lang = "en"

        dom_p_clean = str(dom_p).lower().replace(".", "")

        # Tier for advisory lookup
        tier_key = "COMPOUND_ALERT" if c_alert else r_level
        tier_data = self.advisories_data.get("tiers", {}).get(tier_key, {})

        # Fetch localized headline
        headlines = tier_data.get("headline", {})
        headline = headlines.get(lang, headlines.get("en", f"Health Advisory - {zone_name}"))

        # Fetch demographic group specific guidance
        groups_data = tier_data.get("groups", {})
        group_advice_dict = groups_data.get(group, groups_data.get("general_public", {}))
        group_guidance = group_advice_dict.get(lang, group_advice_dict.get("en", ""))

        # Dominant pollutant notice
        pollutant_notices = self.advisories_data.get("dominant_pollutant_notices", {}).get(dom_p_clean, {})
        if not pollutant_notices and dom_p_clean == "pm25":
            pollutant_notices = self.advisories_data.get("dominant_pollutant_notices", {}).get("pm2.5", {})
        pollutant_notice = pollutant_notices.get(lang, pollutant_notices.get("en", ""))

        # Detailed actions based on tier
        if c_alert:
            urgency = "EMERGENCY"
            badge_class = "danger-compound"
            actions_en = [
                "Issue mandatory N95 / FFP2 mask advisory for all residents going outdoors.",
                "Suspend all outdoor school activities, sports events, and non-essential construction.",
                "Deploy mobile oxygenation clinics and put primary health centers on acute respiratory alert.",
                "Elderly, children, and individuals with asthma / COPD should remain strictly indoors with air filtration."
            ]
            health_department_action = "IMMEDIATE INTERVENTION: Trigger Emergency Medical Services and municipal mist-cannon trucks."
        elif r_level == "RED":
            urgency = "SEVERE"
            badge_class = "danger"
            actions_en = [
                "Avoid prolonged outdoor exertion; wear respiratory protective masks.",
                "Vulnerable groups (asthmatics, heart patients, elderly) should stay indoors.",
                "Run HEPA indoor purifiers where accessible."
            ]
            health_department_action = "Intensify ambient air monitoring and enforce industrial emission caps."
        elif r_level == "ORANGE":
            urgency = "HIGH"
            badge_class = "warning"
            actions_en = [
                "Sensitive individuals should limit strenuous outdoor activity.",
                "Keep windows closed during early morning peak stagnation hours.",
                "Drink adequate water and report new persistent coughs to local health centers."
            ]
            health_department_action = "Targeted street vacuuming and traffic diversion away from school zones."
        elif r_level == "YELLOW":
            urgency = "MODERATE"
            badge_class = "info"
            actions_en = [
                "Sensitive individuals experiencing throat dryness should limit long workouts outdoors.",
                "Monitor daily local forecasts before planning high-intensity sports."
            ]
            health_department_action = "Routine surveillance; verify sensor calibration and dust control compliance."
        else:
            urgency = "LOW"
            badge_class = "success"
            actions_en = [
                "Normal outdoor physical activity and recreation encouraged.",
                "Ideal conditions for ventilation."
            ]
            health_department_action = "Maintain regular surveillance and green cover maintenance."

        # Summary combining pollutant notice and situation
        if lang == "ta":
            summary = f"{zone_name} பகுதியில் அபாய நிலை: {r_level} (AQI: {avg_aqi:.1f}, புகார்கள்: {complaints}). {pollutant_notice} {group_guidance}"
        elif lang == "hi":
            summary = f"{zone_name} में जोखिम स्तर: {r_level} (AQI: {avg_aqi:.1f}, शिकायतें: {complaints})। {pollutant_notice} {group_guidance}"
        else:
            summary = (
                f"Conditions in {zone_name}: {r_level} (AQI: {avg_aqi:.1f}, Risk Score: {r_score:.1f}, "
                f"{complaints} complaints). {pollutant_notice} Group Guidance: {group_guidance}"
            )

        return {
            "zone_id": zid,
            "zone_name": zone_name,
            "city": city,
            "risk_level": r_level,
            "risk_score": r_score,
            "compound_alert": c_alert,
            "headline": headline,
            "urgency": urgency,
            "badge_class": badge_class,
            "demographic_group": group,
            "language": lang,
            "dominant_pollutant": dom_p_clean,
            "dominant_pollutant_notice": pollutant_notice,
            "group_guidance": group_guidance,
            "summary": summary,
            "actions": actions_en,
            "health_department_action": health_department_action
        }

    # Method alias for backward and forward compatibility
    get_advisory = generate_advisory
