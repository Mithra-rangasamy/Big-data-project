// CIT 21MDS56: Air Quality & Public Health Early-Warning System - dashboard.js
// Focused on Tamil Nadu State and all 30 Districts + Multi-Modal Big Data Fusion
// Features 1-12: Traffic-Light Banner, Geolocation, Symptom Chips, Confirmation Modal,
// Explainer Modal, Social Share with Deep-Linking, Mobile Navigation, and Guided Tour

let map;
let markersLayer;
let facilitiesLayer;
let heatLayer = null;
let tnGeoJsonLayer = null;
let currentDate = null;
let currentLang = "en";
let currentGroup = "general_public";
let trendChartInstance = null;
let cachedZones = [];
let cachedDates = [];
let cachedTnDistricts = [];
let districtDataMap = {};
let isHeatmapActive = false;
let isFacilitiesActive = false;
let isSliderPlaying = false;
let sliderInterval = null;

// New feature state
let selectedZone = null;
let simpleAdviceConfig = null;
let explainerConfig = null;
let tourStep = 0;

// City & Regional coordinates mapping - Focused on Tamil Nadu
const CITY_COORDS = {
    tn: { center: [11.0500, 78.4500], zoom: 7.2 }, // Full Tamil Nadu state overview
    coimbatore: { center: [10.9800, 76.9600], zoom: 11 }, // Coimbatore CIT & Industrial Belt
    chennai: { center: [13.0827, 80.2707], zoom: 11 }, // Chennai Metro & Port Corridors
    madurai: { center: [9.9252, 78.1198], zoom: 11 }, // Madurai Cultural & Agro-Trade Hub
    trichy_salem: { center: [11.2000, 78.4000], zoom: 9 }, // Central Engineering & Steel Corridor
    all: { center: [19.0760, 78.5000], zoom: 5 } // All India comparison
};

document.addEventListener("DOMContentLoaded", async () => {
    initMap();
    initEventListeners();
    await loadSimpleAdviceConfig();
    await loadExplainerConfig();
    await loadDates();
    await loadDashboardData();
    await loadTamilNaduDistricts();
    loadComplaintsSummary();
    loadAdminRanking();

    // Check deep link parameter ?zone=<id>
    checkDeepLinkZone();

    // Check auto-location prompt on first visit
    checkAutoLocationPrompt();

    // Check guided tour on first visit
    checkGuidedTourAutoStart();
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
    facilitiesLayer = L.layerGroup().addTo(map);

    // Layer switcher control (bottom right)
    L.control.layers({
        "🌙 Dark Canvas (Clean)": darkCanvas,
        "🗺️ OpenStreetMap": osmStandard
    }, {
        "📍 Monitoring Stations": markersLayer,
        "🏥 Emergency Facilities": facilitiesLayer
    }, { position: "bottomright" }).addTo(map);

    setTimeout(() => {
        if (map) map.invalidateSize();
    }, 250);
}

// Setup Event Listeners
function initEventListeners() {
    // City & Region zoom buttons
    document.querySelectorAll(".city-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const cityKey = e.currentTarget.getAttribute("data-city");
            if (!cityKey || !CITY_COORDS[cityKey]) return;

            document.querySelectorAll(".city-btn").forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");

            const target = CITY_COORDS[cityKey];
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

    // Heatmap Toggle (Feature L)
    const btnHeatmap = document.getElementById("btn-toggle-heatmap");
    if (btnHeatmap) {
        btnHeatmap.addEventListener("click", () => {
            toggleHeatmap();
        });
    }

    // Language switcher (Feature K)
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            currentLang = e.currentTarget.getAttribute("data-lang");
            loadDashboardData(currentDate);
        });
    });

    // Vulnerable group buttons (Feature B)
    document.querySelectorAll(".group-filter-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".group-filter-btn").forEach(b => b.classList.remove("active"));
            e.currentTarget.classList.add("active");
            currentGroup = e.currentTarget.getAttribute("data-group");
            loadDashboardData(currentDate);
        });
    });

    // Time Slider Replay Control (Feature L)
    const timeSlider = document.getElementById("time-slider");
    const playBtn = document.getElementById("btn-play-slider");

    if (timeSlider) {
        timeSlider.addEventListener("input", (e) => {
            const idx = parseInt(e.target.value);
            if (cachedDates && cachedDates[idx]) {
                const targetDate = cachedDates[idx];
                document.getElementById("slider-date-label").textContent = targetDate;
                document.getElementById("date-select").value = targetDate;
                currentDate = targetDate;
                loadDashboardData(currentDate);
                loadTamilNaduDistricts(currentDate);
                loadAdminRanking(currentDate);
            }
        });
    }

    if (playBtn) {
        playBtn.addEventListener("click", () => {
            toggleSliderPlay();
        });
    }

    // Date selector change
    const dateSelect = document.getElementById("date-select");
    if (dateSelect) {
        dateSelect.addEventListener("change", (e) => {
            currentDate = e.target.value;
            syncSliderToDate(currentDate);
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

            e.currentTarget.classList.add("active");
            const tabId = e.currentTarget.getAttribute("data-tab");
            const pane = document.getElementById(tabId);
            if (pane) pane.classList.add("active");
        });
    });

    // Modal Close
    document.querySelectorAll(".modal-close").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".modal-overlay").forEach(m => m.classList.remove("active"));
        });
    });

    document.querySelectorAll(".modal-overlay").forEach(overlay => {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) overlay.classList.remove("active");
        });
    });

    // Trigger Pipeline Recalculation
    const btnTrigger = document.getElementById("btn-trigger-pipeline");
    if (btnTrigger) {
        btnTrigger.addEventListener("click", async () => {
            btnTrigger.disabled = true;
            btnTrigger.textContent = "⏳ Running...";
            try {
                const res = await fetch("/api/pipeline/trigger", { method: "POST" });
                const json = await res.json();
                showToast(json.message);
                loadDashboardData();
                loadTamilNaduDistricts();
            } catch (err) {
                alert("Trigger failed: " + err);
            } finally {
                btnTrigger.disabled = false;
                btnTrigger.textContent = "🔄 Recalculate";
            }
        });
    }

    // Mobile Hamburger Menu Toggle (Feature 11)
    const navToggle = document.getElementById("nav-toggle-btn");
    const navActions = document.getElementById("nav-actions");
    if (navToggle && navActions) {
        navToggle.addEventListener("click", () => {
            navActions.classList.toggle("is-open");
        });
    }

    // Banner Buttons (Features 1, 2, 5, 6)
    const btnLocation = document.getElementById("btn-use-location");
    if (btnLocation) {
        btnLocation.addEventListener("click", () => detectUserLocation(false));
    }

    const btnExplainer = document.getElementById("btn-open-explainer");
    if (btnExplainer) {
        btnExplainer.addEventListener("click", () => openExplainerModal());
    }

    const btnShare = document.getElementById("btn-share") || document.getElementById("btn-share-banner");
    if (btnShare) {
        btnShare.addEventListener("click", () => shareCurrentZone());
    }

    // Technical Term Tooltip Triggers (Feature 5)
    document.querySelectorAll(".term-tooltip-trigger").forEach(el => {
        el.addEventListener("click", (e) => {
            e.stopPropagation();
            const term = e.currentTarget.getAttribute("data-term");
            openExplainerModal(term);
        });
    });

    // Guided Tour Buttons (Feature 12)
    const btnTour = document.getElementById("btn-start-tour");
    if (btnTour) {
        btnTour.addEventListener("click", () => startGuidedTour());
    }

    const tourBtnNext = document.getElementById("tour-btn-next");
    const tourBtnBack = document.getElementById("tour-btn-back");
    const tourBtnSkip = document.getElementById("tour-btn-skip");
    if (tourBtnNext) tourBtnNext.addEventListener("click", () => nextTourStep());
    if (tourBtnBack) tourBtnBack.addEventListener("click", () => prevTourStep());
    if (tourBtnSkip) tourBtnSkip.addEventListener("click", () => endGuidedTour());

    // Report Symptom Modal Open & Form Setup (Features 3 & 4)
    const btnReport = document.getElementById("btn-report-symptom");
    if (btnReport) {
        btnReport.addEventListener("click", () => {
            openComplaintModal();
        });
    }

    // Tap-to-select Symptom Chips
    document.querySelectorAll(".symptom-chip").forEach(chip => {
        chip.addEventListener("click", (e) => {
            e.currentTarget.classList.toggle("active");
            document.getElementById("symptom-required-hint").style.display = "none";
        });
    });

    // Severity Selector Pills
    document.querySelectorAll(".severity-pill").forEach(pill => {
        pill.addEventListener("click", (e) => {
            document.querySelectorAll(".severity-pill").forEach(p => p.classList.remove("active"));
            e.currentTarget.classList.add("active");
        });
    });

    // Form City / Zone Dropdown Sync
    const reportCitySelect = document.getElementById("report-city-select");
    if (reportCitySelect) {
        reportCitySelect.addEventListener("change", (e) => {
            filterReportZoneSelectByCity(e.target.value);
        });
    }

    // Form Submit
    const formComplaint = document.getElementById("complaint-form");
    if (formComplaint) {
        formComplaint.addEventListener("submit", async (e) => {
            e.preventDefault();
            await submitCitizenComplaint();
        });
    }

    // Confirmation Modal Close Button
    const btnCloseConfirm = document.getElementById("btn-close-confirmation");
    if (btnCloseConfirm) {
        btnCloseConfirm.addEventListener("click", () => {
            document.getElementById("modal-submission-confirm").classList.remove("active");
        });
    }
}

// =============================================================================
// Feature 1: Plain Traffic-Light Banner
// =============================================================================
async function loadSimpleAdviceConfig() {
    try {
        const res = await fetch("/api/config/advice-simple");
        simpleAdviceConfig = await res.json();
    } catch (err) {
        console.warn("Could not load advice_simple.json:", err);
    }
}

function updateTrafficLightBanner(zone, distanceInfo = null) { return; }

function detectUserLocation(isAutoPrompt = false) {
    if (!navigator.geolocation) {
        if (!isAutoPrompt) alert("Geolocation is not supported by your browser.");
        return;
    }

    const btn = document.getElementById("btn-use-location");
    if (btn && !isAutoPrompt) {
        btn.textContent = "📍 Locating...";
        btn.disabled = true;
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
            if (btn && !isAutoPrompt) {
                btn.textContent = "📍 Use My Location";
                btn.disabled = false;
            }

            const uLat = pos.coords.latitude;
            const uLon = pos.coords.longitude;

            let nearest = null;
            let minDist = Infinity;

            cachedZones.forEach(z => {
                if (z.lat && z.lon) {
                    const d = haversineKm(uLat, uLon, z.lat, z.lon);
                    if (d < minDist) {
                        minDist = d;
                        nearest = z;
                    }
                }
            });

            if (nearest && minDist <= 50.0) {
                selectedZone = nearest;
                // banner removed
                map.flyTo([nearest.lat, nearest.lon], 12, { duration: 1.2 });
                showToast(`📍 Nearest Zone: ${nearest.zone_name} (${minDist.toFixed(1)} km away)`);
                prefillComplaintZone(nearest);
            } else {
                showToast(`📍 Location is ${minDist.toFixed(0)} km from our monitored hubs (>50 km). Showing Coimbatore.`);
                if (!selectedZone && cachedZones.length > 0) {
                    selectDefaultZone();
                }
            }
        },
        (err) => {
            if (btn && !isAutoPrompt) {
                btn.textContent = "📍 Use My Location";
                btn.disabled = false;
            }
            if (!isAutoPrompt) {
                alert("Location permission denied or unavailable. You can select any district or zone manually from the map.");
            }
            if (!selectedZone) {
                selectDefaultZone();
            }
        },
        { timeout: 8000, maximumAge: 60000 }
    );
}

function checkAutoLocationPrompt() {
    const prompted = localStorage.getItem("ews_location_prompted");
    if (!prompted) {
        localStorage.setItem("ews_location_prompted", "true");
        setTimeout(() => {
            detectUserLocation(true);
        }, 1500);
    }
}

function selectDefaultZone() {
    if (!cachedZones || cachedZones.length === 0) return;
    const priority = cachedZones.find(z => z.compound_alert) ||
                     cachedZones.find(z => z.risk_level === "RED") ||
                     cachedZones.find(z => z.city === "Coimbatore") ||
                     cachedZones[0];
    selectedZone = priority;
    updateTrafficLightBanner(priority);
    prefillComplaintZone(priority);
}

// =============================================================================
// Feature 5: Simple AQI Explainer
// =============================================================================
function openExplainerModal(section = null) { return; }

function shareCurrentZone() {
    const zone = selectedZone || cachedZones[0];
    if (!zone) return;

    const advice = document.getElementById("banner-advice-text")?.textContent || "Check live air quality status.";
    const shareUrl = `${window.location.origin}/?zone=${zone.zone_id}`;
    const shareText = `Air Quality Alert for ${zone.zone_name}, ${zone.city}: ${zone.risk_level} (${zone.avg_aqi ? Math.round(zone.avg_aqi) : ''} AQI). ${advice}\nLive Dashboard: ${shareUrl}`;

    if (navigator.share) {
        navigator.share({
            title: `Air Quality Alert: ${zone.zone_name}`,
            text: shareText,
            url: shareUrl
        }).catch(() => {});
    } else {
        // Fallback: Copy link and offer WhatsApp
        if (navigator.clipboard) {
            navigator.clipboard.writeText(shareText);
            showToast("📋 Link & alert copied to clipboard! Share on WhatsApp ready.");
        }
        const waUrl = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
        window.open(waUrl, "_blank");
    }
}

function checkDeepLinkZone() {
    const params = new URLSearchParams(window.location.search);
    const zoneId = params.get("zone");
    if (!zoneId) return;

    setTimeout(() => {
        const match = cachedZones.find(z => z.zone_id === zoneId);
        if (match) {
            selectedZone = match;
            // banner removed
            map.flyTo([match.lat, match.lon], 12, { duration: 1.2 });
            prefillComplaintZone(match);
            showToast(`📍 Focused on deep-linked zone: ${match.zone_name}`);
        }
    }, 600);
}

function showToast(msg) {
    const toast = document.getElementById("toast-notice");
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
}

// =============================================================================
// Feature 3: Tap-to-Select Symptom Chips Complaint Form
// =============================================================================
function openComplaintModal() {
    const modal = document.getElementById("modal-complaint");
    if (!modal) return;
    if (selectedZone) {
        prefillComplaintZone(selectedZone);
    }
    modal.classList.add("active");
}

function prefillComplaintZone(zone) {
    if (!zone) return;
    const citySelect = document.getElementById("report-city-select");
    const zoneSelect = document.getElementById("report-zone-select");

    if (citySelect && zone.city) {
        citySelect.value = zone.city;
        filterReportZoneSelectByCity(zone.city);
    }
    if (zoneSelect && zone.zone_id) {
        zoneSelect.value = zone.zone_id;
    }
}

function filterReportZoneSelectByCity(cityName) {
    const select = document.getElementById("report-zone-select");
    if (!select || !cachedZones) return;

    select.innerHTML = '<option value="">-- Choose Monitored Zone --</option>';
    const filtered = cachedZones.filter(z => !cityName || z.city.toLowerCase() === cityName.toLowerCase());
    filtered.forEach(z => {
        const opt = document.createElement("option");
        opt.value = z.zone_id;
        opt.textContent = `${z.zone_name} (${z.city})`;
        select.appendChild(opt);
    });
}

async function submitCitizenComplaint() {
    const zid = document.getElementById("report-zone-select").value;
    const name = (document.getElementById("report-citizen-name") ? document.getElementById("report-citizen-name").value.trim() : "");
    const desc = (document.getElementById("report-desc") ? document.getElementById("report-desc").value.trim() : "");
    const age = (document.getElementById("report-age-group") ? document.getElementById("report-age-group").value : "adult");
    const sevRadio = document.querySelector('input[name="severity"]:checked');
    const sev = sevRadio ? sevRadio.value : "moderate";

    const checkedBoxes = Array.from(document.querySelectorAll('input[name="symptoms"]:checked')).map(cb => cb.value);
    const symptoms = checkedBoxes.length > 0 ? checkedBoxes : ["cough"];

    if (!zid) {
        alert("Please select a monitored zone.");
        return;
    }
    if (!desc || desc.length < 4) {
        alert("Please provide at least 4 characters of description.");
        return;
    }

    const payload = {
        zone_id: zid,
        citizen_name: name || "Anonymous Citizen",
        symptoms: symptoms,
        severity: sev,
        age_group: age,
        description: desc
    };

    try {
        const res = await fetch("/api/complaints", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (res.status === 201) {
            alert(`Report Registered: ${json.report_id}\n\nYour complaint has been verified and registered with the Early-Warning Network!`);
            document.getElementById("modal-complaint").classList.remove("active");
            document.getElementById("complaint-form").reset();
            loadComplaintsSummary();
        } else {
            alert("Quality Gate Intercepted: " + (json.rejection_reason || json.message));
        }
    } catch (err) {
        alert("Connection error while submitting report: " + err);
    }
}

// =============================================================================
// Feature 4: Submission Confirmation Modal
// =============================================================================
function openSubmissionConfirmation(reportId, zoneId) {
    const modal = document.getElementById("modal-submission-confirm");
    const refEl = document.getElementById("confirm-ref-id");
    const zoneEl = document.getElementById("confirm-zone-name");
    const badgeEl = document.getElementById("confirm-risk-badge");

    if (!modal) return;

    refEl.textContent = reportId || "RPT-WEB-XXXXX";
    const zoneMatch = cachedZones.find(z => z.zone_id === zoneId);
    if (zoneMatch) {
        zoneEl.textContent = `${zoneMatch.zone_name} (${zoneMatch.city})`;
        badgeEl.textContent = `${getRiskEmoji(zoneMatch.risk_level)} ${zoneMatch.compound_alert ? 'COMPOUND ALERT' : zoneMatch.risk_level}`;
        badgeEl.style.background = getRiskColor(zoneMatch.risk_level, zoneMatch.compound_alert);
        badgeEl.style.color = "#fff";
    } else {
        zoneEl.textContent = zoneId;
        badgeEl.textContent = "REGISTERED";
        badgeEl.style.background = "#0284c7";
    }

    modal.classList.add("active");
}

// =============================================================================
// Feature 12: 4-Step Vanilla JS Guided Tour
// =============================================================================
const TOUR_STEPS = [
    {
        target: "map",
        stepText: "Step 1 of 4",
        title: "🗺️ Surveillance Map & TN Choropleth",
        body: "Explore real-time monitoring stations and all 30 Tamil Nadu districts. Click any district or station marker to inspect 30-day trends and clinical directives."
    },
    {
        target: "btn-use-location",
        stepText: "Step 2 of 4",
        title: "📍 Location Auto-Detection",
        body: "Click 'My Location' anytime to calculate your distance to all monitoring stations and automatically focus on your nearest zone within 50 km."
    },
    {
        target: "btn-report-symptom",
        stepText: "Step 3 of 4",
        title: "📢 Citizen Health Reporting",
        body: "Report symptoms (persistent cough, breathlessness, eye burning) directly into MongoDB to drive the Big Data fusion risk calculation."
    },
    {
        target: "btn-share",
        stepText: "Step 4 of 4",
        title: "📤 Share Air Quality Advisory",
        body: "Share the live health risk advisory with family and neighbors on WhatsApp or copy deep-links with one tap."
    }
];

function checkGuidedTourAutoStart() {
    const tourDone = localStorage.getItem("ews_tour_completed");
    if (!tourDone) {
        setTimeout(() => {
            startGuidedTour();
        }, 1200);
    }
}

function startGuidedTour() {
    tourStep = 0;
    renderCurrentTourStep();
}

function renderCurrentTourStep() {
    const popover = document.getElementById("tour-popover");
    const stepEl = document.getElementById("tour-step");
    const titleEl = document.getElementById("tour-title");
    const bodyEl = document.getElementById("tour-body");
    const backBtn = document.getElementById("tour-btn-back");
    const nextBtn = document.getElementById("tour-btn-next");

    if (!popover) return;

    document.querySelectorAll(".tour-spotlight").forEach(el => el.classList.remove("tour-spotlight"));

    const cur = TOUR_STEPS[tourStep];
    stepEl.textContent = cur.stepText;
    titleEl.textContent = cur.title;
    bodyEl.textContent = cur.body;

    backBtn.style.display = (tourStep > 0) ? "inline-flex" : "none";
    nextBtn.textContent = (tourStep === TOUR_STEPS.length - 1) ? "Finish Tour" : "Next";

    const targetEl = document.getElementById(cur.target);
    if (targetEl) {
        targetEl.classList.add("tour-spotlight");
        targetEl.scrollIntoView({ behavior: "smooth", block: "center" });

        const rect = targetEl.getBoundingClientRect();
        let top = rect.bottom + 10;
        let left = rect.left + 10;

        if (top + 200 > window.innerHeight) {
            top = Math.max(10, rect.top - 200);
        }
        if (left + 320 > window.innerWidth) {
            left = Math.max(10, window.innerWidth - 330);
        }

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
    } else {
        popover.style.top = "100px";
        popover.style.left = "20px";
    }

    popover.classList.add("active");
}

function nextTourStep() {
    if (tourStep < TOUR_STEPS.length - 1) {
        tourStep++;
        renderCurrentTourStep();
    } else {
        endGuidedTour();
    }
}

function prevTourStep() {
    if (tourStep > 0) {
        tourStep--;
        renderCurrentTourStep();
    }
}

function endGuidedTour() {
    const popover = document.getElementById("tour-popover");
    if (popover) popover.classList.remove("active");
    document.querySelectorAll(".tour-spotlight").forEach(el => el.classList.remove("tour-spotlight"));
    localStorage.setItem("ews_tour_completed", "true");
    showToast("🧭 Tour finished! You can revisit it anytime via 'Take Tour'.");
}

// =============================================================================
// Core Map, Tamil Nadu Districts & Aggregation Renderers
// =============================================================================
async function loadDates() {
    try {
        const res = await fetch("/api/dates");
        const json = await res.json();
        if (json.status === "success" && json.dates) {
            const select = document.getElementById("date-select");
            select.innerHTML = "";
            cachedDates = json.dates;

            json.dates.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d;
                opt.textContent = `Date: ${d}`;
                if (d === json.latest) opt.selected = true;
                select.appendChild(opt);
            });

            currentDate = json.latest;
            const slider = document.getElementById("time-slider");
            if (slider) {
                slider.max = json.dates.length - 1;
                slider.value = json.dates.length - 1;
            }
            const label = document.getElementById("slider-date-label");
            if (label) label.textContent = json.latest;
        }
    } catch (err) {
        console.error("Error loading dates:", err);
    }
}

function syncSliderToDate(targetDate) {
    if (!cachedDates) return;
    const idx = cachedDates.indexOf(targetDate);
    if (idx !== -1) {
        const slider = document.getElementById("time-slider");
        if (slider) slider.value = idx;
        const label = document.getElementById("slider-date-label");
        if (label) label.textContent = targetDate;
    }
}

function toggleSliderPlay() {
    const btn = document.getElementById("btn-play-slider");
    if (!btn || !cachedDates || cachedDates.length === 0) return;

    if (isSliderPlaying) {
        clearInterval(sliderInterval);
        isSliderPlaying = false;
        btn.textContent = "▶ Play Replay";
    } else {
        isSliderPlaying = true;
        btn.textContent = "⏸ Pause";

        let currentIdx = parseInt(document.getElementById("time-slider").value);
        sliderInterval = setInterval(() => {
            currentIdx = (currentIdx + 1) % cachedDates.length;
            const targetDate = cachedDates[currentIdx];
            document.getElementById("time-slider").value = currentIdx;
            document.getElementById("slider-date-label").textContent = targetDate;
            document.getElementById("date-select").value = targetDate;
            currentDate = targetDate;

            loadDashboardData(targetDate);
            loadTamilNaduDistricts(targetDate);
            loadAdminRanking(targetDate);
        }, 1800);
    }
}

function toggleHeatmap() {
    const btn = document.getElementById("btn-toggle-heatmap");
    if (!btn) return;

    if (isHeatmapActive) {
        if (heatLayer) map.removeLayer(heatLayer);
        isHeatmapActive = false;
        btn.textContent = "🔥 Heatmap: OFF";
        btn.style.borderColor = "#eab308";
        btn.style.color = "#fde047";
    } else {
        const heatPoints = cachedZones.map(z => [z.lat, z.lon, Math.min(1.0, z.avg_aqi / 300.0)]);
        heatLayer = L.heatLayer(heatPoints, {
            radius: 35,
            blur: 20,
            maxZoom: 14,
            gradient: { 0.2: "#22c55e", 0.4: "#eab308", 0.7: "#f97316", 1.0: "#ef4444" }
        }).addTo(map);

        isHeatmapActive = true;
        btn.textContent = "🔥 Heatmap: ON";
        btn.style.borderColor = "#ef4444";
        btn.style.color = "#f87171";
    }
}

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

        populateDistrictDropdown(cachedTnDistricts);
        renderTamilNaduDistrictsList(cachedTnDistricts);

        if (tnGeoJsonLayer) {
            map.removeLayer(tnGeoJsonLayer);
        }

        tnGeoJsonLayer = L.geoJSON(geoJson, {
            style: styleDistrictFeature,
            onEachFeature: onEachDistrictFeature
        }).addTo(map);

        markersLayer.bringToFront();
    } catch (err) {
        console.error("Failed to load Tamil Nadu district surveillance:", err);
    }
}

function getRiskColor(level, compoundAlert = false) {
    if (compoundAlert) return "#dc2626";
    if (level === "RED") return "#ef4444";
    if (level === "ORANGE") return "#f97316";
    if (level === "YELLOW") return "#eab308";
    if (level === "STALE") return "#6c757d";
    return "#22c55e";
}

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

function focusOnDistrict(distName) {
    const info = districtDataMap[distName.toLowerCase()];
    if (!info) return;

    if (info.centroid) {
        map.flyTo(info.centroid, 10.5, { duration: 1.2 });
    }

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

function renderTamilNaduDistrictsList(districts) {
    const container = document.getElementById("tn-districts-list");
    if (!container) return;
    container.innerHTML = "";

    const sorted = [...districts].sort((a, b) => {
        if (a.compound_alert !== b.compound_alert) return a.compound_alert ? -1 : 1;
        return b.risk_score - a.risk_score;
    });

    sorted.forEach(d => {
        const card = document.createElement("div");
        card.style.cssText = "background:#1e293b; border:1px solid #334155; border-radius:6px; padding:10px; margin-bottom:8px; cursor:pointer; transition:all 0.15s ease;";

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:#fff; font-size:13px;">${d.district_name}</strong>
                <span style="background:${getRiskColor(d.risk_level, d.compound_alert)}; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">
                    ${d.compound_alert ? 'COMPOUND' : d.risk_level}
                </span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:#94a3b8; margin-top:4px;">
                <span>AQI: <strong style="color:#f8fafc;">${d.avg_aqi}</strong></span>
                <span>Risk: <strong style="color:#38bdf8;">${d.risk_score}</strong></span>
                <span>Reports: <strong style="color:#ef4444;">${d.complaints}</strong></span>
            </div>
        `;

        card.addEventListener("click", () => focusOnDistrict(d.district_name));
        card.addEventListener("mouseenter", () => card.style.background = "#334155");
        card.addEventListener("mouseleave", () => card.style.background = "#1e293b");

        container.appendChild(card);
    });
}

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
        alertBanner.innerHTML = "🚨 <strong>COMPOUND HEALTH CONVERGENCE:</strong> Hazardous air coinciding with symptomatic outbreaks in this district!";
    } else {
        alertBanner.style.display = "none";
    }

    modal.classList.add("active");
}

// Load Core Zone Risk Data
async function loadDashboardData(targetDate = null) {
    try {
        const url = targetDate ? `/api/zones/risk?date=${targetDate}&lang=${currentLang}&group=${currentGroup}` : `/api/zones/risk?lang=${currentLang}&group=${currentGroup}`;
        const res = await fetch(url);
        const result = await res.json();
        if (result.status !== "success" || !result.data) return;

        cachedZones = result.data;
        updateMetrics(result.data);
        renderMapMarkers(result.data);
        renderAdvisories(result.data);
        populateReportZoneSelect(result.data);

        // Update selectedZone & Banner
        if (selectedZone) {
            const updated = cachedZones.find(z => z.zone_id === selectedZone.zone_id);
            if (updated) selectedZone = updated;
            updateTrafficLightBanner(selectedZone);
        } else {
            selectDefaultZone();
        }
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

        const popupContent = `
            <div style="min-width: 220px; font-family: sans-serif;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <strong style="font-size:14px; color:#fff;">${z.zone_name}</strong>
                    <span style="background:${color}; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;">
                        ${z.compound_alert ? "COMPOUND ALERT" : z.risk_level}
                    </span>
                </div>
                <div style="font-size:12px; color:#94a3b8; margin-bottom:8px;">${z.city} &bull; ${z.date}</div>

                <div style="background:rgba(239, 68, 68, 0.15); border:1px solid #dc2626; padding:4px 8px; border-radius:4px; font-size:11px; margin-bottom:8px;">
                    <strong style="color:#f87171;">Dominant Concern:</strong> ${(z.dominant_pollutant_name || 'PM2.5').toUpperCase()}
                </div>

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
                ">📈 30-Day Trend & 6-Pollutants</button>
            </div>
        `;

        marker.bindPopup(popupContent);
        marker.on("click", () => {
            selectedZone = z;
            // banner removed
            prefillComplaintZone(z);
        });

        markersLayer.addLayer(marker);
    });
}

// Render Advisories in Side Panel (Features B & K)
function renderAdvisories(zones) {
    const container = document.getElementById("advisories-list");
    if (!container) return;
    container.innerHTML = "";

    const sorted = [...zones].sort((a, b) => {
        if (a.compound_alert !== b.compound_alert) return a.compound_alert ? -1 : 1;
        return b.risk_score - a.risk_score;
    });

    sorted.forEach(z => {
        const adv = z.advisory || {};
        const card = document.createElement("div");
        card.className = `advisory-card ${adv.badge_class || 'info'}`;
        card.style.cursor = "pointer";

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

            <div style="background:#0f172a; padding:6px 10px; border-radius:4px; margin:6px 0; border:1px solid #334155; font-size:11px;">
                <strong style="color:#f87171;">Dominant: ${(z.dominant_pollutant_name || 'PM2.5').toUpperCase()}</strong> &bull; ${adv.dominant_pollutant_notice || adv.summary}
            </div>

            <div style="background:rgba(56, 189, 248, 0.08); border-left:3px solid #38bdf8; padding:6px 8px; border-radius:4px; font-size:11px; color:#cbd5e1; margin-bottom:8px;">
                <strong style="color:#38bdf8; text-transform:uppercase;">${currentGroup.replace('_', ' ')} Directive:</strong><br>
                ${adv.group_guidance || 'Follow general public protective precautions.'}
            </div>

            <div class="advisory-actions-title">Clinical Guidance & Precautions:</div>
            <ul class="advisory-action-list">
                ${(adv.actions || []).map(act => `<li>${act}</li>`).join('')}
            </ul>
            <div class="advisory-dept">
                <strong>🏛 Municipal Action:</strong> ${adv.health_department_action || 'Surveillance maintained.'}
            </div>
        `;

        card.addEventListener("click", () => {
            selectedZone = z;
            // banner removed
            map.flyTo([z.lat, z.lon], 12, { duration: 1.0 });
            prefillComplaintZone(z);
        });

        container.appendChild(card);
    });
}

// Show Zone Trend Modal with 6 Pollutants & 24h Forecast (Features A, C, H, J)
async function showZoneTrendModal(zoneId) {
    try {
        const [trendRes, pRes, fRes, facRes] = await Promise.all([
            fetch(`/api/zones/${zoneId}/trend`),
            fetch(`/api/zones/${zoneId}/pollutants?date=${currentDate || ''}`),
            fetch(`/api/forecast/${zoneId}?date=${currentDate || ''}`),
            fetch(`/api/facilities/nearby?zone=${zoneId}`)
        ]);

        const result = await trendRes.json();
        const pData = await pRes.json();
        const fData = await fRes.json();
        const facData = await facRes.json();

        if (result.status !== "success" || !result.data) return;

        const modal = document.getElementById("modal-trend");
        const lastRec = result.data[result.data.length - 1];
        document.getElementById("modal-trend-title").textContent = `${lastRec.zone_name} (${lastRec.city}) - Multi-Modal Surveillance`;

        const scenarioBadge = document.getElementById("modal-scenario-badge");
        if (lastRec.compound_alert) {
            scenarioBadge.innerHTML = `<span style="background:#dc2626; color:#fff; padding:4px 8px; border-radius:4px; font-weight:bold;">🚨 VALIDATED COMPOUND OUTBREAK: Rising AQI Coupled with Surging Morbidity</span>`;
        } else {
            scenarioBadge.innerHTML = `<span style="background:${getRiskColor(lastRec.risk_level)}; color:#fff; padding:3px 8px; border-radius:4px; font-weight:bold;">Scenario: ${lastRec.risk_level} Health Tier</span>`;
        }

        // Render 6 Criteria Pollutants (Feature A)
        if (pData.status === "success" && pData.pollutants) {
            document.getElementById("modal-dominant-badge").textContent = `Dominant Concern: ${(pData.dominant_pollutant_name || 'PM2.5').toUpperCase()}`;
            document.getElementById("modal-dominant-notice").textContent = pData.dominant_pollutant_notice || "CPCB normalization ratio exceeded.";

            const grid = document.getElementById("modal-pollutants-grid");
            grid.innerHTML = "";

            const pollutantsList = [
                { key: "pm25", label: "PM2.5", unit: "µg/m³" },
                { key: "pm10", label: "PM10", unit: "µg/m³" },
                { key: "no2", label: "NO2", unit: "µg/m³" },
                { key: "so2", label: "SO2", unit: "µg/m³" },
                { key: "co", label: "CO", unit: "mg/m³" },
                { key: "o3", label: "O3", unit: "µg/m³" }
            ];

            pollutantsList.forEach(p => {
                const pVal = pData.pollutants[p.key] || 0;
                const isDom = pData.dominant_pollutant_name && pData.dominant_pollutant_name.toLowerCase() === p.key;

                const card = document.createElement("div");
                card.style.cssText = `background:#1e293b; padding:6px; border-radius:6px; text-align:center; border:1px solid ${isDom ? '#ef4444' : '#334155'};`;
                card.innerHTML = `
                    <div style="font-size:10px; color:${isDom ? '#f87171' : '#94a3b8'}; font-weight:bold;">${p.label}</div>
                    <div style="font-size:13px; font-weight:800; color:#fff; margin:2px 0;">${pVal}</div>
                    <div style="font-size:9px; color:#64748b;">${p.unit}</div>
                `;
                grid.appendChild(card);
            });
        }

        // Feature J: Emergency hospital locator
        if (facData.status === "success" && facData.nearest_emergency_hospital) {
            const h = facData.nearest_emergency_hospital;
            document.getElementById("modal-hosp-name").textContent = h.name;
            document.getElementById("modal-hosp-specialty").textContent = h.specialty;
            document.getElementById("modal-hosp-dist").textContent = `${h.distance_km} km`;
            document.getElementById("modal-hosp-phone").textContent = `📞 ${h.phone}`;
            document.getElementById("modal-hospital-bar").style.display = "flex";
        }

        // Render Chart
        const ctx = document.getElementById("trendChart").getContext("2d");
        const labels = result.data.map(r => r.date.substring(5));
        const riskScores = result.data.map(r => r.risk_score);
        const aqiValues = result.data.map(r => r.avg_aqi);
        const complaintCounts = result.data.map(r => r.complaint_count);

        if (trendChartInstance) {
            trendChartInstance.destroy();
        }

        const datasets = [
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
                label: "Ambient AQI (Historical)",
                data: aqiValues,
                borderColor: "#38bdf8",
                backgroundColor: "transparent",
                borderWidth: 2,
                yAxisID: "yAqi",
                tension: 0.2
            },
            {
                label: "Citizen Symptoms Ingested",
                data: complaintCounts,
                borderColor: "#eab308",
                backgroundColor: "rgba(234, 179, 8, 0.2)",
                borderWidth: 2,
                type: "bar",
                yAxisID: "yComplaints"
            }
        ];

        // 24-Hour Forecast Curve (Feature H)
        if (fData.status === "success" && fData.hourly_forecast) {
            const fLabels = fData.hourly_forecast.map(h => `FC ${h.time}`);
            const combinedLabels = [...labels, ...fLabels];
            const emptyHistoryPadding = new Array(labels.length - 1).fill(null);
            const lastHistoricalAqi = aqiValues[aqiValues.length - 1];
            const fValues = [lastHistoricalAqi, ...fData.hourly_forecast.map(h => h.predicted_aqi)];

            datasets.push({
                label: "24h AQI Forecast (Diurnal Harmonic)",
                data: [...emptyHistoryPadding, ...fValues],
                borderColor: "#a855f7",
                borderDash: [6, 4],
                borderWidth: 2.5,
                backgroundColor: "transparent",
                yAxisID: "yAqi",
                pointRadius: 2
            });

            trendChartInstance = new Chart(ctx, {
                type: "line",
                data: { labels: combinedLabels, datasets: datasets },
                options: getTrendChartOptions()
            });
        } else {
            trendChartInstance = new Chart(ctx, {
                type: "line",
                data: { labels: labels, datasets: datasets },
                options: getTrendChartOptions()
            });
        }

        modal.classList.add("active");
    } catch (err) {
        console.error("Error displaying trend modal:", err);
    }
}
window.showZoneTrendModal = showZoneTrendModal;

function getTrendChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
            legend: { labels: { color: "#cbd5e1", font: { size: 11 } } }
        },
        scales: {
            x: { ticks: { color: "#94a3b8", maxTicksLimit: 14 } },
            yRisk: {
                type: "linear",
                position: "left",
                min: 0,
                max: 100,
                title: { display: true, text: "Health Risk Score", color: "#ef4444" },
                ticks: { color: "#ef4444" }
            },
            yAqi: {
                type: "linear",
                position: "right",
                min: 0,
                title: { display: true, text: "AQI", color: "#38bdf8" },
                ticks: { color: "#38bdf8" },
                grid: { drawOnChartArea: false }
            },
            yComplaints: {
                type: "linear",
                position: "right",
                min: 0,
                title: { display: false },
                ticks: { display: false },
                grid: { drawOnChartArea: false }
            }
        }
    };
}

function populateReportZoneSelect(zones) {
    const select = document.getElementById("report-zone-select");
    if (!select || select.children.length > 1) return;
    select.innerHTML = '<option value="">-- Choose Monitored Zone --</option>';
    zones.forEach(z => {
        const opt = document.createElement("option");
        opt.value = z.zone_id;
        opt.textContent = `${z.zone_name} (${z.city})`;
        select.appendChild(opt);
    });
}

// Load Complaints Summary Breakdown
async function loadComplaintsSummary() {
    try {
        const res = await fetch("/api/social/feed");
        const json = await res.json();
        const feed = document.getElementById("recent-complaints-feed");
        if (feed && json.data) {
            feed.innerHTML = "";
            json.data.slice(0, 8).forEach(p => {
                const item = document.createElement("div");
                item.style.cssText = "background:#0f172a; padding:8px 10px; border-radius:6px; margin-bottom:6px; border:1px solid #334155; font-size:11px;";
                item.innerHTML = `
                    <div style="display:flex; justify-content:space-between; color:#94a3b8;">
                        <span>${p.city || 'Tamil Nadu'} &bull; ${p.platform || 'Portal'}</span>
                        <span style="color:#ef4444; font-weight:bold;">${(p.symptoms_detected || []).join(', ')}</span>
                    </div>
                    <div style="color:#cbd5e1; margin-top:3px;">"${p.text}"</div>
                `;
                feed.appendChild(item);
            });
        }
    } catch (err) {
        console.error("Error loading complaints feed:", err);
    }
}

// Load Admin City Rankings
async function loadAdminRanking(targetDate = null) {
    try {
        const url = targetDate ? `/api/admin/ranking?date=${targetDate}` : "/api/admin/ranking";
        const res = await fetch(url);
        const json = await res.json();
        const tbody = document.getElementById("ranking-tbody");
        if (!tbody || !json.cities) return;
        tbody.innerHTML = "";

        json.cities.forEach(c => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${c.city}</strong></td>
                <td style="color:#ef4444; font-weight:bold;">${c.red_zones}</td>
                <td style="color:#ea580c; font-weight:bold;">${c.orange_zones}</td>
                <td>${c.total_complaints}</td>
                <td><strong style="color:#38bdf8;">${c.avg_risk_score.toFixed(1)}</strong></td>
                <td>${c.compound_alerts > 0 ? '🚨 ACTIVE' : 'Normal'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading admin rankings:", err);
    }
}
