# Changelog - Air Quality & Public Health Early-Warning System

All notable changes, architectural enhancements, citizen-facing tools, and administrative consoles added to the CIT 21MDS56 Early-Warning System are documented in this file.

---

## [Phase 11: Citizen Usability & Core Streamlining] - 2026-10-14

### Kept Enhancements
1. **Current Location Auto-Detection** (`frontend/templates/index.html`, `frontend/static/js/dashboard.js`, `backend/app.py`)
   - "📍 My Location" button added directly into the navigation bar actions.
   - Client-side Haversine distance calculation against `config/zones.json` with fallback server endpoint `/api/zones/nearest`.
   - Automatically focuses on the nearest zone within 50 km, pans the Leaflet map smoothly, and presents distance notification. Zero server-side storage of citizen coordinates.

2. **Share Option & Deep Linking** (`frontend/templates/index.html`, `frontend/static/js/dashboard.js`)
   - "📤 Share" button in navigation bar actions.
   - Integrates native Web Share API (`navigator.share`) with fallback to WhatsApp and one-tap clipboard copy toast notification.
   - URL parameter `?zone=<id>` deep-linking support automatically focuses and highlights the specified zone on page load.

3. **Guided Onboarding Tour** (`frontend/templates/index.html`, `frontend/static/js/dashboard.js`)
   - 4-step progressive onboarding walkthrough introducing:
     1. Geographic Surveillance Map & Tamil Nadu 30-District Choropleth (`#map`).
     2. Location Auto-Detection (`#btn-use-location`).
     3. Citizen Health Reporting Form (`#btn-report-symptom`).
     4. Share Air Quality Advisory (`#btn-share`).
   - `localStorage` flag preventing repetitive prompts, with persistent `"🧭 Take Tour"` navbar link.

### Cleaned Up & Reverted Features
- **Plain Traffic-Light Banner**: Removed `#traffic-light-banner` and `config/advice_simple.json`. Restored clean direct view of top metrics banner and Tamil Nadu map.
- **Symptom Checklist Chips**: Reverted complaint submission modal to standard symptom checkboxes and observation description.
- **Submission Confirmation Modal**: Removed `#modal-submission-confirm`, restoring standard registration notification.
- **Simple AQI Explainer**: Removed explainer modal and `config/explainer.json`.
- **Admin Summary KPI Cards**: Removed `admin-summary-grid` from `/admin`.
- **Admin Multi-Filter Toolbar**: Removed filter toolbar, restoring clean, sortable surveillance matrix table.
- **Alert Action Tracker**: Removed incident action tracking table, modal, and endpoints from `admin.html`, `app.py`, and `mongo_client.py`.
- **Printable Situation Report**: Removed `report.html`, `/admin/report`, and `/api/admin/report`.

---

### Automated Test Suite Verification
- **All 22 automated tests passing with 100% success rate (12.84s)**:
  - `tests/test_api.py` (14 tests covering Features A through O)
  - `tests/test_new_features.py` (3 tests verifying Location, Share, and Tour)
  - `tests/test_services.py` (4 tests verifying MongoDB, HiveServer2, HDFS, and Pig)
  - `tests/test_tn_api.py` (1 test verifying Tamil Nadu state-wide surveillance)
