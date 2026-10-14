"""CIT 21MDS56: Air Quality & Public Health Early-Warning System
backend/forecast_service.py - 24-Hour Explainable AQI Diurnal Forecasting Engine
"""

import datetime
from typing import Dict, List, Any

# Diurnal multipliers reflecting atmospheric boundary layer inversion and traffic cycles
# Hour 0 to 23: Higher at 08:00 and 20:00-22:00, lower at 14:00-16:00
HOURLY_DIURNAL_WEIGHTS = [
    0.95, 0.92, 0.90, 0.88, 0.91, 1.02, 1.15, 1.25, 1.28, 1.20,
    1.08, 0.98, 0.88, 0.82, 0.80, 0.85, 0.95, 1.10, 1.22, 1.26,
    1.24, 1.18, 1.08, 1.00
]

class ForecastEngine:
    def __init__(self, hive_client=None):
        self.hive_client = hive_client

    def generate_24h_forecast(self, zone_id: str, base_date: str = None) -> Dict[str, Any]:
        """Generates hourly forecast for the next 24 hours based on recent history and diurnal pattern."""
        trend_records = self.hive_client.get_zone_trend(zone_id) if self.hive_client else []
        
        if not trend_records:
            return {
                "status": "error",
                "message": f"Insufficient historical data to compute forecast for zone {zone_id}"
            }

        # Last record
        last_rec = trend_records[-1]
        zone_name = last_rec.get("zone_name", "Unknown Zone")
        city = last_rec.get("city", "Unknown City")
        current_aqi = last_rec.get("avg_aqi", 150.0)
        risk_level = last_rec.get("risk_level", "YELLOW")

        # Compute 3-day trend momentum
        momentum = 0.0
        if len(trend_records) >= 3:
            recent_3 = [r["avg_aqi"] for r in trend_records[-3:]]
            if recent_3[0] > 0:
                momentum = (recent_3[-1] - recent_3[0]) / (3.0 * recent_3[0])
                # Cap momentum between -0.25 and +0.25
                momentum = max(-0.25, min(0.25, momentum))

        # Base forecasted day
        target_day = base_date or last_rec.get("date", "2026-10-13")
        try:
            base_dt = datetime.datetime.strptime(target_day, "%Y-%m-%d")
        except Exception:
            base_dt = datetime.datetime(2026, 10, 13)
        next_dt = base_dt + datetime.timedelta(days=1)
        next_date_str = next_dt.strftime("%Y-%m-%d")

        hourly_forecast = []
        for hour in range(24):
            factor = HOURLY_DIURNAL_WEIGHTS[hour] * (1.0 + momentum)
            predicted_aqi = round(current_aqi * factor, 1)
            # Standard error estimation ~ 8% of predicted AQI
            ci_margin = round(predicted_aqi * 0.08 * 1.96, 1)
            lower_ci = max(10.0, round(predicted_aqi - ci_margin, 1))
            upper_ci = min(500.0, round(predicted_aqi + ci_margin, 1))

            time_label = f"{hour:02d}:00"
            hourly_forecast.append({
                "hour": hour,
                "time": time_label,
                "timestamp": f"{next_date_str} {time_label}",
                "predicted_aqi": predicted_aqi,
                "lower_bound": lower_ci,
                "upper_bound": upper_ci
            })

        avg_predicted = round(sum(h["predicted_aqi"] for h in hourly_forecast) / 24.0, 1)
        peak_forecast = max(hourly_forecast, key=lambda x: x["predicted_aqi"])

        if avg_predicted >= 250:
            forecast_tier = "RED"
        elif avg_predicted >= 150:
            forecast_tier = "ORANGE"
        elif avg_predicted >= 80:
            forecast_tier = "YELLOW"
        else:
            forecast_tier = "GREEN"

        return {
            "status": "success",
            "zone_id": zone_id,
            "zone_name": zone_name,
            "city": city,
            "base_date": target_day,
            "forecast_date": next_date_str,
            "current_aqi": round(current_aqi, 1),
            "momentum_factor": round(momentum, 3),
            "momentum_direction": "Rising" if momentum > 0.03 else ("Falling" if momentum < -0.03 else "Stable"),
            "predicted_avg_aqi": avg_predicted,
            "predicted_tier": forecast_tier,
            "peak_hour": peak_forecast["time"],
            "peak_aqi": peak_forecast["predicted_aqi"],
            "model": "Diurnal Harmonic Moving Average with 3-Day Linear Momentum",
            "hourly_forecast": hourly_forecast
        }

    def generate_forecast(self, zone_id: str, target_date: str = None, base_date: str = None) -> Dict[str, Any]:
        """Alias for generate_24h_forecast supporting target_date parameter."""
        return self.generate_24h_forecast(zone_id, base_date=target_date or base_date)
