// CIT 21MDS56: Air Quality & Public Health Early-Warning System - dashboard.js
// Focused on Tamil Nadu State and all 30 Districts

let map;
let markersLayer;
let tnGeoJsonLayer = null;
let currentDate = null;
let trendChartInstance = null;
let cachedZones = [];
let cachedTnDistricts = [];
let districtDataMap = {};

// City & Regional coordinates mapping - Focused on Tamil Nadu
const CITY_COORDS = {
    tn: { center: [11.0500, 78.4500], zoom: 7.2 }, // Full Tamil Nadu state overview
    coimbatore: { center: [10.9800, 76.9600], zoom: 11 }, // Coimbatore CIT & Industrial Belt
    chennai: { center: [13.0827, 80.2707], zoom: 11 }, // Chennai Metro & Port Corridors
    madurai: { center: [9.9252, 78.1198], zoom: 11 }, // Madurai Cultural & Agro-Trade Hub
    trichy_salem: { center: [11.2000, 78.4000], zoom: 9 }, // Central Engineering & Steel Corridor
    all: { center: [19.0760, 78.5000], zoom: 5 } // All India comparison
};

document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initEventListeners();
    loadDates();
    loadDashboardData();
    loadTamilNaduDistricts();
    loadComplaintsSummary();
    loadAdminRanking();
});

// Initialize Leaflet Map focused on Tamil Nadu
function initMap() {
    map = L.map("map", {
        zoomControl: true,
        attributionControl: false
    }).setView(CITY_COORDS.tn.center, CITY_COORDS.tn.zoom);

    // Free Esri Dark Gray Canvas layer (No API key required)
    const darkCanvas = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
        maxZoom: 16,
        attribution: "Tiles &copy; Esri"
    }).addTo(map);

    const osmStandard = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    });

    markersLayer = L.layerGroup().addTo(map);

    // Layer switcher control (bottom right)
    L.control.layers({
        "🌙 Dark Canvas (Clean)": darkCanvas,
        "🗺️ OpenStreetMap": osmStandard
    }, {
        "📍 Monitoring Stations": markersLayer
    }, { position: "bottomright" }).addTo(map);
}

// Setup Event Listeners
function initEventListeners() {
    // City & Region zoom buttons
    document.querySelectorAll(".city-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".city-btn").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            const cityKey = e.target.getAttribute("data-city");
            const target = CITY_COORDS[cityKey] || CITY_COORDS.tn;
            map.flyTo(target.center, target.zoom, { duration: 1.2 });
        });
    });

    // Tamil Nadu District Quick-Jump Dropdown
    const distSelect = document.getElementById("select-tn-district");
    if (distSelect) {
        distSelect.addEventListener("change", (e) => {
            const distName = e.target.value;
            if (!distName) return;
            focusOnDistrict(distName);
        });
    }

    // Date selector change
    const dateSelect = document.getElementById("date-select");
    if (dateSelect) {
        dateSelect.addEventListener("change", (e) => {
            currentDate = e.target.value;
            loadDashboardData(currentDate);
            loadTamilNaduDistricts(currentDate);
            loadAdminRanking(currentDate);
        });
    }

    // Side panel tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
            e.target.classList.add("active");
            const tabId = e.target.getAttribute("data-tab");
            const pane = document.getElementById(tabId);
            if (pane) pane.classList.add("active");
        });
    });

    // Modals close
    document.querySelectorAll(".modal-close").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
        });
    });

    // Citizen Complaint Button
    const reportBtn = document.getElementById("btn-report-symptom");
    if (reportBtn) {
        reportBtn.addEventListener("click", () => {
            populateZoneDropdown();
            document.getElementById("modal-complaint").classList.add("active");
        });
    }

    // Complaint Form Submit
    const complaintForm = document.getElementById("complaint-form");
    if (complaintForm) {
        complaintForm.addEventListener("submit", handleComplaintSubmit);
    }

    // Trigger Pipeline Recalculation Button
    const triggerBtn = document.getElementById("btn-trigger-pipeline");
    if (triggerBtn) {
        triggerBtn.addEventListener("click", triggerPipelineRecalculation);
    }
}

// Load Available Dates
async function loadDates() {
    try {
        const res = await fetch("/api/dates");
        const data = await res.json();
        const select = document.getElementById("date-select");
        if (select && data.dates) {
            select.innerHTML = "";
            data.dates.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d;
                opt.textContent = `Date: ${d}`;
                if (d === data.latest) opt.selected = true;
                select.appendChild(opt);
            });
            currentDate = data.latest;
        }
    } catch (err) {
        console.error("Failed to load dates:", err);
    }
}

// Load Tamil Nadu District Boundaries & State-Wide Surveillance
async function loadTamilNaduDistricts(targetDate = null) {
    try {
        const url = targetDate ? `/api/tamilnadu/districts?date=${targetDate}` : "/api/tamilnadu/districts";
        const [apiRes, geoRes] = await Promise.all([
            fetch(url),
            fetch("/static/data/tamilnadu_districts.geojson")
        ]);

        const apiJson = await apiRes.json();
        const geoJson = await geoRes.json();

        if (apiJson.status !== "success" || !geoJson.features) return;

        cachedTnDistricts = apiJson.districts;
        districtDataMap = {};
        cachedTnDistricts.forEach(d => {
            districtDataMap[d.district_name.toLowerCase()] = d;
        });

        // Populate Tamil Nadu district dropdown in toolbar
        populateDistrictDropdown(cachedTnDistricts);

        // Render Tamil Nadu districts list in side panel tab
        renderTamilNaduDistrictsList(cachedTnDistricts);

        // Render Leaflet GeoJSON layer for all Tamil Nadu districts
        if (tnGeoJsonLayer) {
            map.removeLayer(tnGeoJsonLayer);
        }

        tnGeoJsonLayer = L.geoJSON(geoJson, {
            style: styleDistrictFeature,
            onEachFeature: onEachDistrictFeature
        }).addTo(map);

        // Ensure markers are on top of district polygons
        markersLayer.bringToFront();

    } catch (err) {
        console.error("Failed to load Tamil Nadu district surveillance:", err);
    }
}

// Style Tamil Nadu District Polygons
function styleDistrictFeature(feature) {
    const rawName = feature.properties.NAME_2 || "";
    const info = districtDataMap[rawName.toLowerCase()] || {};
    const riskLevel = info.risk_level || "YELLOW";
    const compoundAlert = info.compound_alert || false;

    const color = getRiskColor(riskLevel, compoundAlert);
    const fillOpacity = compoundAlert ? 0.45 : (riskLevel === "RED" ? 0.38 : (riskLevel === "ORANGE" ? 0.30 : (riskLevel === "YELLOW" ? 0.22 : 0.16)));

    return {
        fillColor: color,
        weight: 1.5,
        opacity: 0.8,
        color: "#38bdf8",
        dashArray: "2",
        fillOpacity: fillOpacity
    };
}

// Interactive Behaviors for Tamil Nadu District Polygons
function onEachDistrictFeature(feature, layer) {
    const rawName = feature.properties.NAME_2 || "District";
    const info = districtDataMap[rawName.toLowerCase()] || {
        district_name: rawName,
        risk_score: 30,
        risk_level: "YELLOW",
        avg_aqi: 110,
        complaints: 1,
        type: "District Surveillance Zone",
        advisory: "Routine air quality surveillance."
    };

    const color = getRiskColor(info.risk_level, info.compound_alert);

    // Hover tooltip
    const tooltipContent = `
        <div style="font-family: sans-serif; font-size: 12px; min-width: 170px;">
            <div style="font-weight: bold; font-size: 13px; color: #fff; margin-bottom: 2px;">
                ${rawName} District
            </div>
            <div style="margin-bottom: 4px;">
                <span style="background:${color}; color:#fff; padding:1px 5px; border-radius:3px; font-size:10px; font-weight:bold;">
                    ${info.risk_level} ${info.compound_alert ? '(COMPOUND ALERT)' : ''}
                </span>
                <span style="color:#38bdf8; font-weight:bold; margin-left:4px;">Risk: ${info.risk_score}</span>
            </div>
            <div style="color: #cbd5e1; font-size: 11px;">
                AQI: <strong>${info.avg_aqi}</strong> | Reports: <strong>${info.complaints}</strong>
            </div>
            <div style="color: #94a3b8; font-size: 10px; margin-top: 3px; line-height: 1.2;">
                ${info.type}
            </div>
        </div>
    `;

    layer.bindTooltip(tooltipContent, {
        sticky: true,
        className: "custom-district-tooltip"
    });

    layer.on({
        mouseover: (e) => {
            const l = e.target;
            l.setStyle({
                weight: 3,
                color: "#ffffff",
                dashArray: "",
                fillOpacity: 0.60
            });
            l.bringToFront();
            markersLayer.bringToFront();
        },
        mouseout: (e) => {
            tnGeoJsonLayer.resetStyle(e.target);
        },
        click: (e) => {
            map.fitBounds(e.target.getBounds(), { padding: [30, 30] });
            showDistrictDetailsModal(rawName, info);
        }
    });
}

// Populate Tamil Nadu District Dropdown
function populateDistrictDropdown(districts) {
    const sel = document.getElementById("select-tn-district");
    if (!sel) return;

    sel.innerHTML = '<option value="">📍 Focus on Tamil Nadu District (30)...</option>';
    const sorted = [...districts].sort((a, b) => a.district_name.localeCompare(b.district_name));
    sorted.forEach(d => {
        const opt = document.createElement("option");
        opt.value = d.district_name;
        opt.textContent = `${d.district_name} [${d.risk_level}]`;
        sel.appendChild(opt);
    });
}

// Focus Map on Specific District
function focusOnDistrict(distName) {
    const info = districtDataMap[distName.toLowerCase()];
    if (!info) return;

    if (info.centroid) {
        map.flyTo(info.centroid, 10.5, { duration: 1.2 });
    }

    // If layer exists, flash highlight
    if (tnGeoJsonLayer) {
        tnGeoJsonLayer.eachLayer(l => {
            const name = l.feature?.properties?.NAME_2;
            if (name && name.toLowerCase() === distName.toLowerCase()) {
                l.setStyle({ weight: 4, color: "#ffffff", fillOpacity: 0.7 });
                setTimeout(() => tnGeoJsonLayer.resetStyle(l), 2500);
            }
        });
    }

    showDistrictDetailsModal(distName, info);
}

// Render Tamil Nadu Districts List in Side Panel
function renderTamilNaduDistrictsList(districts) {
    const container = document.getElementById("tn-districts-list");
    if (!container) return;

    container.innerHTML = "";
    districts.forEach(d => {
        const color = getRiskColor(d.risk_level, d.compound_alert);
        const card = document.createElement("div");
        card.style.cssText = `
            background: #1e293b;
            border: 1px solid #334155;
            border-left: 4px solid ${color};
            border-radius: 6px;
            padding: 8px 10px;
            margin-bottom: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        `;

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
                <strong style="color:#fff; font-size:13px;">${d.district_name}</strong>
                <span style="background:${color}; color:#fff; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:bold;">
                    ${d.risk_level}
                </span>
            </div>
            <div style="font-size:11px; color:#cbd5e1; display:flex; justify-content:space-between;">
                <span>AQI: <strong>${d.avg_aqi}</strong></span>
                <span>Risk Score: <strong style="color:#38bdf8;">${d.risk_score}</strong></span>
                <span>Reports: <strong>${d.complaints}</strong></span>
            </div>
            <div style="font-size:10px; color:#94a3b8; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                ${d.type}
            </div>
        `;

        card.addEventListener("click", () => focusOnDistrict(d.district_name));
        card.addEventListener("mouseenter", () => card.style.background = "#334155");
        card.addEventListener("mouseleave", () => card.style.background = "#1e293b");

        container.appendChild(card);
    });
}

// Show District Details Modal
function showDistrictDetailsModal(distName, info) {
    const modal = document.getElementById("modal-district-details");
    if (!modal) return;

    document.getElementById("modal-district-title").textContent = `${distName} District - Environmental Surveillance`;
    document.getElementById("modal-district-type").textContent = info.type || "Urban & Industrial Zone";
    document.getElementById("modal-district-aqi").textContent = info.avg_aqi;
    document.getElementById("modal-district-risk").textContent = `${info.risk_score} / 100 (${info.risk_level})`;
    document.getElementById("modal-district-complaints").textContent = `${info.complaints} Citizen Reports`;
    document.getElementById("modal-district-symptom").textContent = info.primary_symptom || "Respiratory monitoring";
    document.getElementById("modal-district-advisory").textContent = info.advisory || "Routine public health surveillance.";
    document.getElementById("modal-district-industry").textContent = info.industry || "Commercial & Manufacturing";

    const alertBanner = document.getElementById("modal-district-alert-banner");
    if (info.compound_alert) {
        alertBanner.style.display = "block";
        alertBanner.innerHTML = "🚨 <strong>COMPOUND HEALTH ALERT:</strong> Significant convergence of hazardous particulate pollution and surging citizen illness in this district!";
    } else {
        alertBanner.style.display = "none";
    }

    modal.classList.add("active");
}

// Load Risk Scores & Map Markers
async function loadDashboardData(targetDate = null) {
    try {
        const url = targetDate ? `/api/zones/risk?date=${targetDate}` : "/api/zones/risk";
        const res = await fetch(url);
        const result = await res.json();
        if (result.status !== "success") return;

        cachedZones = result.data;
        updateMetrics(result.data);
        renderMapMarkers(result.data);
        renderAdvisories(result.data);
    } catch (err) {
        console.error("Failed to load dashboard data:", err);
    }
}

// Update Top Metrics Banner
function updateMetrics(zones) {
    let redCount = 0;
    let orangeCount = 0;
    let compoundCount = 0;
    let totalComplaints = 0;
    let peakAqi = 0;
    let peakZone = "";

    zones.forEach(z => {
        if (z.risk_level === "RED") redCount++;
        if (z.risk_level === "ORANGE") orangeCount++;
        if (z.compound_alert) compoundCount++;
        totalComplaints += (z.complaint_count || 0);
        if (z.avg_aqi > peakAqi) {
            peakAqi = z.avg_aqi;
            peakZone = `${z.zone_name} (${z.city})`;
        }
    });

    document.getElementById("metric-monitored-zones").textContent = zones.length;
    document.getElementById("metric-red-zones").textContent = redCount;
    document.getElementById("metric-compound-alerts").textContent = compoundCount;
    document.getElementById("metric-total-complaints").textContent = totalComplaints;
    document.getElementById("metric-peak-aqi").textContent = Math.round(peakAqi);
    document.getElementById("metric-peak-zone").textContent = peakZone;

    const alertCard = document.getElementById("card-compound-alerts");
    if (alertCard) {
        if (compoundCount > 0) {
            alertCard.classList.add("pulse-marker");
        } else {
            alertCard.classList.remove("pulse-marker");
        }
    }
}

// Render Leaflet Markers
function renderMapMarkers(zones) {
    markersLayer.clearLayers();

    zones.forEach(z => {
        const color = getRiskColor(z.risk_level, z.compound_alert);
        const isPulse = z.compound_alert;

        // Custom HTML marker icon
        const iconHtml = `
            <div style="
                background-color: ${color};
                width: ${isPulse ? '24px' : '18px'};
                height: ${isPulse ? '24px' : '18px'};
                border-radius: 50%;
                border: 2px solid #ffffff;
                box-shadow: 0 0 ${isPulse ? '14px' : '6px'} ${color};
            " class="${isPulse ? 'pulse-marker' : ''}"></div>
        `;

        const customIcon = L.divIcon({
            html: iconHtml,
            className: "custom-zone-marker",
            iconSize: isPulse ? [24, 24] : [18, 18],
            iconAnchor: isPulse ? [12, 12] : [9, 9]
        });

        const marker = L.marker([z.lat, z.lon], { icon: customIcon });

        // Popup Content
        const popupContent = `
            <div style="min-width: 220px; font-family: sans-serif;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <strong style="font-size:14px; color:#fff;">${z.zone_name}</strong>
                    <span style="background:${color}; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">
                        ${z.risk_level}
                    </span>
                </div>
                <div style="font-size:12px; color:#94a3b8; margin-bottom:8px;">${z.city} &bull; ${z.date}</div>

                ${z.compound_alert ? `
                    <div style="background:#dc2626; color:#fff; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:bold; margin-bottom:8px; text-align:center;">
                        ⚠️ CRITICAL COMPOUND HEALTH ALERT
                    </div>
                ` : ''}

                <div style="background:#0f172a; padding:8px; border-radius:6px; font-size:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="color:#94a3b8;">Health Risk Score:</span>
                        <strong style="color:#38bdf8; font-size:13px;">${z.risk_score.toFixed(1)} / 100</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                        <span style="color:#94a3b8;">Ambient AQI:</span>
                        <strong style="color:#f8fafc;">${z.avg_aqi.toFixed(1)}</strong>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#94a3b8;">Citizen Complaints:</span>
                        <strong style="color:#ef4444;">${z.complaint_count} reports</strong>
                    </div>
                </div>

                <button onclick="showZoneTrendModal('${z.zone_id}')" style="
                    width: 100%;
                    background: #0284c7;
                    color: #fff;
                    border: none;
                    border-radius: 4px;
                    padding: 6px;
                    font-size: 11px;
                    font-weight: bold;
                    cursor: pointer;
                ">📈 View 30-Day Trend & Advisory</button>
            </div>
        `;

        marker.bindPopup(popupContent);
        markersLayer.addLayer(marker);
    });
}

function getRiskColor(level, compoundAlert) {
    if (compoundAlert) return "#dc2626";
    if (level === "RED") return "#ef4444";
    if (level === "ORANGE") return "#f97316";
    if (level === "YELLOW") return "#eab308";
    return "#22c55e";
}

// Render Advisories in Side Panel
function renderAdvisories(zones) {
    const container = document.getElementById("advisories-list");
    if (!container) return;

    container.innerHTML = "";
    // Filter and prioritize compound alerts and red/orange zones
    const sorted = [...zones].sort((a, b) => {
        if (a.compound_alert !== b.compound_alert) return a.compound_alert ? -1 : 1;
        return b.risk_score - a.risk_score;
    });

    sorted.forEach(z => {
        const adv = z.advisory || {};
        const card = document.createElement("div");
        card.className = `advisory-card ${adv.badge_class || 'info'}`;

        card.innerHTML = `
            <div class="advisory-header">
                <div>
                    <div class="advisory-zone">${z.zone_name}</div>
                    <div class="advisory-city">${z.city} &bull; AQI ${z.avg_aqi.toFixed(0)} &bull; Risk ${z.risk_score.toFixed(1)}</div>
                </div>
                ${z.compound_alert ? `
                    <span class="advisory-badge badge-compound-alert">COMPOUND ALERT</span>
                ` : `
                    <span class="advisory-badge" style="background:${getRiskColor(z.risk_level)}; color:#fff;">${z.risk_level}</span>
                `}
            </div>
            <div class="advisory-summary">${adv.summary || ''}</div>
            <div class="advisory-actions-title">Clinical Guidance & Precautions:</div>
            <ul class="advisory-action-list">
                ${(adv.actions || []).map(act => `<li>${act}</li>`).join('')}
            </ul>
            <div class="advisory-dept">
                <strong>🏛 Municipal Action:</strong> ${adv.health_department_action || 'Surveillance maintained.'}
            </div>
        `;
        container.appendChild(card);
    });
}

// Show Zone Trend Modal with Chart.js
async function showZoneTrendModal(zoneId) {
    try {
        const res = await fetch(`/api/zones/${zoneId}/trend`);
        const result = await res.json();
        if (result.status !== "success") return;

        const zone = cachedZones.find(z => z.zone_id === zoneId) || result.trend[result.trend.length - 1];
        const modal = document.getElementById("modal-trend");
        document.getElementById("modal-trend-title").textContent = `${result.zone_name} (${result.city}) - 30-Day Analysis`;

        // Scenario interpretation badge
        const scenarioBadge = document.getElementById("modal-scenario-badge");
        if (result.scenario === "outbreak") {
            scenarioBadge.innerHTML = `<span style="background:#dc2626; color:#fff; padding:4px 8px; border-radius:4px; font-weight:bold;">🚨 VALIDATED OUTBREAK: Rising AQI Coupled with Surge in Citizen Health Complaints</span>`;
        } else if (result.scenario === "false_alarm") {
            scenarioBadge.innerHTML = `<span style="background:#ca8a04; color:#fff; padding:4px 8px; border-radius:4px; font-weight:bold;">⚠️ LOCALIZED DUST / CONSTRUCTION: High AQI with Near-Zero Symptom Reports</span>`;
        } else {
            scenarioBadge.innerHTML = `<span style="background:#334155; color:#cbd5e1; padding:4px 8px; border-radius:4px;">Normal Urban Atmospheric Surveillance</span>`;
        }

        // Render Chart
        const ctx = document.getElementById("trendChart").getContext("2d");
        const labels = result.trend.map(r => r.date.substring(5)); // MM-DD
        const riskScores = result.trend.map(r => r.risk_score);
        const aqiValues = result.trend.map(r => r.avg_aqi);
        const complaintCounts = result.trend.map(r => r.complaint_count);

        if (trendChartInstance) {
            trendChartInstance.destroy();
        }

        trendChartInstance = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Composite Health Risk (0-100)",
                        data: riskScores,
                        borderColor: "#ef4444",
                        backgroundColor: "rgba(239, 68, 68, 0.15)",
                        borderWidth: 3,
                        yAxisID: "yRisk",
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: "Ambient AQI",
                        data: aqiValues,
                        borderColor: "#38bdf8",
                        backgroundColor: "transparent",
                        borderWidth: 2,
                        yAxisID: "yAqi",
                        tension: 0.2
                    },
                    {
                        label: "Citizen Complaint Count",
                        data: complaintCounts,
                        borderColor: "#eab308",
                        backgroundColor: "rgba(234, 179, 8, 0.2)",
                        borderWidth: 2,
                        type: "bar",
                        yAxisID: "yCount"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: {
                        ticks: { color: "#94a3b8", maxRotation: 45 },
                        grid: { color: "rgba(51, 65, 85, 0.3)" }
                    },
                    yRisk: {
                        type: "linear",
                        display: true,
                        position: "left",
                        min: 0,
                        max: 100,
                        title: { display: true, text: "Risk Score (0-100)", color: "#ef4444" },
                        ticks: { color: "#ef4444" },
                        grid: { color: "rgba(51, 65, 85, 0.3)" }
                    },
                    yAqi: {
                        type: "linear",
                        display: true,
                        position: "right",
                        min: 0,
                        max: 500,
                        title: { display: true, text: "AQI", color: "#38bdf8" },
                        ticks: { color: "#38bdf8" },
                        grid: { drawOnChartArea: false }
                    },
                    yCount: {
                        type: "linear",
                        display: false,
                        position: "right",
                        min: 0,
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#f8fafc" } }
                }
            }
        });

        modal.classList.add("active");
    } catch (err) {
        console.error("Error displaying trend modal:", err);
    }
}

// Populate Zones Dropdown in Citizen Report Modal
function populateZoneDropdown() {
    const sel = document.getElementById("report-zone-select");
    if (!sel || sel.options.length > 1) return;

    // Group by City / State
    const tnOptgroup = document.createElement("optgroup");
    tnOptgroup.label = "🌟 Tamil Nadu Key Hubs & Districts";

    cachedZones.filter(z => z.city === "Coimbatore" || z.city === "Chennai").forEach(z => {
        const opt = document.createElement("option");
        opt.value = z.zone_id;
        opt.textContent = `${z.city} - ${z.zone_name}`;
        tnOptgroup.appendChild(opt);
    });

    // Add other monitored zones
    const otherOptgroup = document.createElement("optgroup");
    otherOptgroup.label = "🇮🇳 Other Metropolitan Corridors";
    cachedZones.filter(z => z.city !== "Coimbatore" && z.city !== "Chennai").forEach(z => {
        const opt = document.createElement("option");
        opt.value = z.zone_id;
        opt.textContent = `${z.city} - ${z.zone_name}`;
        otherOptgroup.appendChild(opt);
    });

    sel.appendChild(tnOptgroup);
    sel.appendChild(otherOptgroup);
}

// Handle Citizen Complaint Form Submit
async function handleComplaintSubmit(e) {
    e.preventDefault();
    const zoneId = document.getElementById("report-zone-select").value;
    const citizenName = document.getElementById("report-citizen-name").value || "Anonymous Citizen";
    const severity = document.querySelector("input[name='severity']:checked")?.value || "moderate";
    const ageGroup = document.getElementById("report-age-group").value || "adult";
    const description = document.getElementById("report-desc").value || "Web report";

    const selectedSymptoms = [];
    document.querySelectorAll("input[name='symptoms']:checked").forEach(cb => {
        selectedSymptoms.push(cb.value);
    });

    if (selectedSymptoms.length === 0) {
        alert("Please select at least one symptom experienced.");
        return;
    }

    const payload = {
        zone_id: zoneId,
        citizen_name: citizenName,
        symptoms: selectedSymptoms,
        severity: severity,
        age_group: ageGroup,
        description: description
    };

    try {
        const res = await fetch("/api/complaints", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.status === "success") {
            alert(`Report Registered: ${result.report_id}\n\nYour complaint has been written directly to MongoDB symptom_reports!`);
            document.getElementById("modal-complaint").classList.remove("active");
            document.getElementById("complaint-form").reset();
            loadComplaintsSummary();
        } else {
            alert("Submission error: " + (result.message || "Unknown error"));
        }
    } catch (err) {
        console.error("Complaint submission failed:", err);
        alert("Network error submitting complaint.");
    }
}

// Load MongoDB Complaints & Symptoms Analytics
async function loadComplaintsSummary() {
    try {
        const res = await fetch("/api/complaints/summary");
        const json = await res.json();
        if (json.status !== "success") return;

        const data = json.data;
        const barContainer = document.getElementById("symptoms-bar-container");
        if (barContainer && data.symptoms) {
            barContainer.innerHTML = "";
            const maxCount = Math.max(...data.symptoms.map(s => s.count), 1);
            data.symptoms.forEach(s => {
                const pct = Math.round((s.count / maxCount) * 100);
                const item = document.createElement("div");
                item.className = "symptom-bar-item";
                item.innerHTML = `
                    <div class="symptom-bar-info">
                        <span style="text-transform: capitalize; font-weight:600;">${s.symptom.replace(/_/g, ' ')}</span>
                        <span style="color:#ef4444; font-weight:bold;">${s.count} reports</span>
                    </div>
                    <div class="symptom-progress">
                        <div class="symptom-progress-fill" style="width: ${pct}%"></div>
                    </div>
                `;
                barContainer.appendChild(item);
            });
        }

        // Render Recent Complaints Feed
        const feedContainer = document.getElementById("recent-complaints-feed");
        if (feedContainer && data.recent_reports) {
            feedContainer.innerHTML = "";
            data.recent_reports.slice(0, 8).forEach(r => {
                const item = document.createElement("div");
                item.style.cssText = "background:#0f172a; padding:8px 10px; border-radius:6px; margin-bottom:6px; font-size:12px; border:1px solid #334155;";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <strong style="color:#fff;">${r.zone_name}</strong>
                        <span style="color:#ef4444; font-weight:600; text-transform:uppercase; font-size:10px;">${r.severity}</span>
                    </div>
                    <div style="color:#94a3b8; font-size:11px; margin-bottom:4px;">${r.city} &bull; ${r.reported_at || ''}</div>
                    <div style="color:#38bdf8;">Symptoms: ${(r.symptoms || []).join(', ')}</div>
                `;
                feedContainer.appendChild(item);
            });
        }
    } catch (err) {
        console.error("Failed to load complaints summary:", err);
    }
}

// Load Admin Ranking Table
async function loadAdminRanking(targetDate = null) {
    try {
        const url = targetDate ? `/api/admin/ranking?date=${targetDate}` : "/api/admin/ranking";
        const res = await fetch(url);
        const json = await res.json();
        if (json.status !== "success") return;

        const tbody = document.getElementById("ranking-tbody");
        if (tbody && json.cities) {
            tbody.innerHTML = "";
            json.cities.forEach(c => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td><strong>${c.city}</strong></td>
                    <td style="color:#ef4444; font-weight:bold;">${c.red_zones}</td>
                    <td style="color:#f97316; font-weight:bold;">${c.orange_zones}</td>
                    <td>${c.total_complaints}</td>
                    <td style="color:#38bdf8; font-weight:bold;">${c.avg_risk_score}</td>
                    <td style="color:${c.compound_alerts > 0 ? '#ef4444' : '#94a3b8'}; font-weight:bold;">
                        ${c.compound_alerts > 0 ? `🚨 ${c.compound_alerts} Active` : 'None'}
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (err) {
        console.error("Failed to load ranking:", err);
    }
}

// Trigger Pipeline Recalculation
async function triggerPipelineRecalculation() {
    const btn = document.getElementById("btn-trigger-pipeline");
    const originalText = btn.innerHTML;
    btn.innerHTML = "⏳ Recalculating Big Data Fusion...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/pipeline/trigger", { method: "POST" });
        const json = await res.json();
        alert(json.message || "Pipeline recalculation started!");
        setTimeout(() => {
            loadDashboardData(currentDate);
            loadTamilNaduDistricts(currentDate);
            loadComplaintsSummary();
            loadAdminRanking(currentDate);
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 3000);
    } catch (err) {
        console.error("Pipeline trigger error:", err);
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
