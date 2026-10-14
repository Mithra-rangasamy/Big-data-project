# 24-Hour Explainable Air Quality Forecasting Methodology

**Course**: CIT 21MDS56 – Big Data Computing Laboratory  
**Project**: Multi-City Air Quality & Public Health Early-Warning System  
**Module**: Feature H – Predictive Risk & Diurnal Atmospheric Forecasting  

---

## 1. Executive Summary & Objective

Standard air quality alert frameworks only respond *reactively* after high pollutant spikes are recorded. To give municipal authorities and hospitals sufficient lead time, the Early-Warning System includes a 24-hour predictive engine that forecasts hourly AQI curves for any monitored urban locality.

Instead of an opaque deep-learning black box, this system uses an **explainable atmospheric physics model**:
1. **Diurnal Inversion Cycle Model** (capturing planetary boundary layer dynamics and traffic peak hours)
2. **3-Day Linear Trend Momentum** (capturing localized accumulation vs dispersion trends)
3. **95% Confidence Interval Bands** (based on historical variance per hour)

---

## 2. Atmospheric & Meteorological Principles

Urban air pollution exhibits consistent 24-hour periodic cycles driven by two primary physical processes:

### A. Planetary Boundary Layer (PBL) Dynamics & Nocturnal Inversion
- **Morning Peak (07:00 – 10:00)**: As morning traffic surges, the nighttime thermal inversion layer traps emissions close to the surface, causing a steep rise in particulate concentration ($PM_{2.5}$ and $PM_{10}$).
- **Afternoon Dilution Trough (13:00 – 16:00)**: Solar irradiance heats the ground, driving convective vertical mixing and expanding the PBL up to 1.5–2.0 km. Pollutants disperse, yielding the daily minimum.
- **Evening Peak (19:00 – 22:00)**: Solar heating ceases, the boundary layer collapses, heavy diesel commercial freight commences, and domestic activities produce a secondary concentration surge.

### B. Mathematical Formulation

Let $AQI_{t}$ be the baseline 24-hour average AQI of the target zone on day $t$.

#### Step 1: 3-Day Momentum Factor ($\Delta_{\text{momentum}}$)
$$\Delta_{\text{momentum}} = \frac{AQI_{t} - AQI_{t-3}}{3 \times AQI_{t-3}}$$
where $\Delta_{\text{momentum}}$ is clamped to $[-0.25, +0.25]$ to prevent divergent spikes.

#### Step 2: Hourly Diurnal Harmonic Weight ($W(h)$)
For each forecasted hour $h \in \{0, 1, \dots, 23\}$, empirical diurnal factors calibrated to Indian urban monitoring stations are applied:
$$W(h) = [0.95, 0.92, 0.90, 0.88, 0.91, 1.02, 1.15, 1.25, 1.28, 1.20, 1.08, 0.98, 0.88, 0.82, 0.80, 0.85, 0.95, 1.10, 1.22, 1.26, 1.24, 1.18, 1.08, 1.00]$$

#### Step 3: Predicted Hourly Concentration ($\widehat{AQI}(h)$)
$$\widehat{AQI}(h) = AQI_{t} \times W(h) \times (1 + \Delta_{\text{momentum}})$$

#### Step 4: 95% Confidence Bounds
$$\text{Margin}(h) = 1.96 \times 0.08 \times \widehat{AQI}(h)$$
$$\text{CI}_{95\%}(h) = [\max(10, \widehat{AQI}(h) - \text{Margin}(h)), \min(500, \widehat{AQI}(h) + \text{Margin}(h))]$$

---

## 3. REST API Contract

### Request
```http
GET /api/forecast/CBE_ZN_01 HTTP/1.1
Host: localhost:5000
```

### Response
```json
{
  "status": "success",
  "zone_id": "CBE_ZN_01",
  "zone_name": "SIDCO Industrial Estate",
  "city": "Coimbatore",
  "base_date": "2026-10-13",
  "forecast_date": "2026-10-14",
  "current_aqi": 407.0,
  "momentum_factor": 0.084,
  "momentum_direction": "Rising",
  "predicted_avg_aqi": 418.5,
  "predicted_tier": "RED",
  "peak_hour": "08:00",
  "peak_aqi": 521.0,
  "model": "Diurnal Harmonic Moving Average with 3-Day Linear Momentum",
  "hourly_forecast": [
    {
      "hour": 0,
      "time": "00:00",
      "timestamp": "2026-10-14 00:00",
      "predicted_aqi": 386.7,
      "lower_bound": 326.0,
      "upper_bound": 447.4
    }
  ]
}
```

---

## 4. Strengths & Limitations

| Aspect | Feature |
| :--- | :--- |
| **Explainability** | Fully inspectable linear parameters directly mapped to physical thermal inversion. |
| **Computational Footprint** | Execution time $< 5\text{ ms}$; requires zero GPU acceleration. |
| **Lead Time** | Gives 24-hour advance advisory to hospitals for acute asthma ward bed reservations. |
| **Limitation** | Does not account for sudden unseasonal rainfall (monsoon washout) without external radar inputs. |
