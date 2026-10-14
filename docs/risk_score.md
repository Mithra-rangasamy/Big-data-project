# Multi-Modal Health Risk Scoring Engine Specification

**Course:** 21MDS56 – Big Data Computing Laboratory  
**Institution:** Coimbatore Institute of Technology (CIT), Coimbatore  
**Program:** M.Sc Data Science  

---

## 1. Problem Statement & Motivation

Traditional environmental monitoring relies solely on ambient **Air Quality Index (AQI)** or **particulate concentrations ($PM_{2.5}, PM_{10}$)**. While ambient AQI measures physical atmospheric particulates, it possesses critical clinical blind spots:

1. **Failure to Detect Synergistic Vulnerabilities:** High AQI during a viral respiratory wave or in a dense industrial zone with toxic VOCs causes an immediate spike in acute human morbidity, whereas identical AQI elsewhere may cause minimal acute symptoms.
2. **The "False Alarm" Problem (Coarse Particulates / Construction Dust):** Construction corridors or desert dust events can elevate $PM_{10}$ and AQI dramatically ($AQI > 250$), yet produce negligible acute bronchial morbidity in the surrounding population. Municipal authorities relying on AQI alone trigger blanket closures and disruptive economic lockdowns unnecessarily.
3. **Delayed Public Health Interventions:** Hospital admissions lag air pollution spikes by several days. Citizen symptom reports submitted via hotlines, municipal web portals, and social channels represent real-time early indicators of biological distress.

The **Multi-City Air Quality & Public Health Early-Warning System** fuses **structured telemetry** (hourly AQI, $PM_{2.5}, PM_{10}$, wind speed, humidity via Apache Hive) with **unstructured citizen health reports** (symptoms, severities, age groups via MongoDB) using **Apache Pig** to compute a **Composite Health-Risk Score (0–100)**.

---

## 2. Mathematical Formulation

For any urban zone $z$ on day $d$, the composite health risk score $R(z, d) \in [0, 100]$ is defined as:

$$R(z, d) = 100 \times \left( w_{\text{aqi}} \cdot \tilde{A} + w_{\text{trend}} \cdot \tilde{T} + w_{\text{comp}} \cdot \tilde{C} + w_{\text{sev}} \cdot \tilde{S} + w_{\text{wx}} \cdot \tilde{W} \right)$$

Subject to the convex weighting constraint:
$$\sum w_i = w_{\text{aqi}} + w_{\text{trend}} + w_{\text{comp}} + w_{\text{sev}} + w_{\text{wx}} = 0.35 + 0.15 + 0.30 + 0.15 + 0.05 = 1.00$$

### 2.1 Feature Normalization Functions

1. **Normalized Ambient AQI ($\tilde{A} \in [0, 1]$):**
   $$\tilde{A}(z, d) = \min\left( \max\left( \frac{\bar{A}(z, d)}{500}, 0 \right), 1.0 \right)$$
   Where $\bar{A}(z, d)$ is the 24-hour mean AQI computed in Hive.

2. **AQI Velocity / Trend Factor ($\tilde{T} \in [0, 1]$):**
   Captures whether pollution is accelerating into dangerous territory:
   $$\tilde{T}(z, d) = \begin{cases} 0.85 & \text{if } \bar{A}(z, d) > 250 \\ 0.50 & \text{if } 150 < \bar{A}(z, d) \le 250 \\ 0.20 & \text{if } \bar{A}(z, d) \le 150 \end{cases}$$

3. **Complaint Density Factor ($\tilde{C} \in [0, 1]$):**
   Computed in MongoDB aggregation as the volume of citizen complaints relative to the expected outbreak baseline ceiling ($C_{\max} = 15$ reports/day):
   $$\tilde{C}(z, d) = \min\left( \frac{N_{\text{complaints}}(z, d)}{C_{\max}}, 1.0 \right)$$

4. **Symptom Severity Weight ($\tilde{S} \in [0, 1]$):**
   Each reported complaint is weighted by clinically verified severity scores:
   $$\tilde{S}(z, d) = \frac{1}{N} \sum_{i=1}^{N} \frac{\sum_{s \in \text{Symptoms}_i} \omega_s}{\sum_{s \in \text{Symptoms}_i} 1} \times \lambda_{\text{severity}}$$
   Where severity multipliers $\lambda_{\text{severity}}$ are:
   - **Severe:** $1.0$ (acute dyspnea, wheezing, chest tightness)
   - **Moderate:** $0.6$ (persistent cough, throat irritation)
   - **Mild:** $0.3$ (mild eye burning, transient headache)

5. **Weather Stagnation Factor ($\tilde{W} \in [0, 1]$):**
   Inversions and calm winds trap particulate matter close to breathing zones:
   $$\tilde{W}(z, d) = \begin{cases} 1.00 & \text{if } \bar{V}_{\text{wind}} < 5.0 \text{ km/h (Atmospheric Stagnation)} \\ 0.20 & \text{if } \bar{V}_{\text{wind}} \ge 5.0 \text{ km/h (Active Dispersion)} \end{cases}$$

---

## 3. Compound Escalation Rule

To prioritize public health emergencies where rising environmental hazard triggers an immediate biological reaction, the engine applies an **autonomous tier escalation rule**:

$$\text{Compound Alert} = \begin{cases} \mathbf{TRUE} & \text{if } \tilde{A} \ge 0.50 \text{ and } \tilde{C} \ge 0.40 \\ \mathbf{FALSE} & \text{otherwise} \end{cases}$$

When $\text{Compound Alert} = \mathbf{TRUE}$, the zone is automatically escalated by one full tier:
- A score that would ordinarily be classified as **YELLOW** is promoted to **ORANGE**.
- A score that would ordinarily be classified as **ORANGE** is promoted to **RED** (Critical Public Health Emergency).

### 3.1 Classification Thresholds

| Risk Level | Composite Score Range | Compound Alert Status | Public Health Designation |
| :--- | :--- | :--- | :--- |
| **GREEN** | $0.0 \le R < 25.0$ | False | Satisfactory (Normal outdoor activity) |
| **YELLOW** | $25.0 \le R < 50.0$ | False | Moderate (Sensitive groups monitor activity) |
| **ORANGE** | $50.0 \le R < 75.0$ | Escalated or Natural | Unhealthy / High Alert (N95 masks advised) |
| **RED** | $R \ge 75.0$ or Esc. | True or False | **CRITICAL EMERGENCY** (Outbreak containment) |

---

## 4. Empirical Evaluation: Outbreak vs. False Alarm

The following actual data points captured from the Apache Pig MapReduce execution demonstrate the system's discrimination capability:

| Metric | Outbreak Zone 1 (`CBE_ZN_01`) | Outbreak Zone 2 (`DEL_ZN_01`) | False Alarm Zone (`BOM_ZN_01`) |
| :--- | :--- | :--- | :--- |
| **City** | Coimbatore (SIDCO Industrial) | Delhi (Anand Vihar) | Mumbai (Bandra-Kurla Complex) |
| **Date** | 2026-10-13 | 2026-10-13 | 2026-10-13 |
| **Ambient AQI** | **407.0** (Severe) | **406.85** (Severe) | **246.46** (Unhealthy / Elevated) |
| **Normalized AQI ($\tilde{A}$)** | 0.814 | 0.814 | 0.493 |
| **Citizen Complaints** | **12 reports** | **8 reports** | **0 reports** |
| **Complaint Density ($\tilde{C}$)**| **1.000** | **0.410** | **0.000** |
| **Symptom Severity ($\tilde{S}$)** | **0.625** | **0.797** | **0.000** |
| **Compound Alert Triggered** | **TRUE** 🚨 | **TRUE** 🚨 | **FALSE** 🟢 |
| **Composite Health Risk** | **81.61** | **66.48** | **25.75** |
| **Final Classification** | **RED** | **RED** (Escalated) | **YELLOW** |
| **System Conclusion** | **Immediate Intervention** | **Emergency Outbreak** | **No Public Panic / Monitor** |

---

## 5. Summary of Benefits for Municipal Decision Making

1. **Avoids False Lockdowns:** `BOM_ZN_01` has high AQI due to local construction dust, but zero complaints. The system classifies it as **YELLOW**, avoiding expensive school closures or transport bans.
2. **Instant Outbreak Detection:** `CBE_ZN_01` exhibits both high AQI and surging citizen reports. It is flagged as **RED** with a **Compound Alert**, prompting immediate mobile clinics and mist cannon trucks.
3. **Defensible Laboratory Proof:** Fully reproducible using standard Big Data primitives: Hive tables on HDFS, MongoDB aggregations, and Apache Pig relational joins.
