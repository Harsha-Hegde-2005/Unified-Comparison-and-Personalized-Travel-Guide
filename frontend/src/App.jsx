import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import heroImg from "./assets/hero.jpg";

/* ─────────────────────────────────────────────────────────────
   CONFIG
───────────────────────────────────────────────────────────── */
const API_BASE = "http://localhost:8000";
const getGoogleMapsKey = () => {
  return localStorage.getItem("gmaps_api_key") || window._backendGmapsKey || import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "YOUR_GOOGLE_MAPS_API_KEY";
};

const originalFetch = window.fetch;
window.fetch = async (url, options = {}) => {
  const urlStr = String(url);
  if (urlStr.startsWith(API_BASE) || urlStr.startsWith("/")) {
    const key = getGoogleMapsKey();
    if (key && key !== "YOUR_GOOGLE_MAPS_API_KEY") {
      options.headers = {
        ...options.headers,
        "X-Google-Maps-Key": key
      };
    }
  }
  return originalFetch(url, options);
};

/* ─────────────────────────────────────────────────────────────
   DESIGN TOKENS
───────────────────────────────────────────────────────────── */
const C = {
  bg: "#f4f5fa", surface: "#ffffff", card: "#ffffff",
  border: "#eef0f6", border2: "#e2e4ed",
  text: "#1a1625", muted: "#7d788a", dim: "#f3f1f7",
  accent: "#7c3aed", metro: "#8b5cf6",
  green: "#10b981", red: "#ef4444", yellow: "#f59e0b",
};

const MC = {
  bmtc: { label: "BMTC Bus", short: "BUS", color: "#f97316", bg: "#1a0f06", icon: "bus", line: "Ordinary · Vajra · AC" },
  metro: { label: "Namma Metro", short: "METRO", color: "#8b5cf6", bg: "#100c1a", icon: "metro", line: "Green · Purple · Yellow" },
  cab: { label: "Cab / Auto", short: "CAB", color: "#f59e0b", bg: "#1a1200", icon: "cab", line: "Namma Yatri · Ola · Uber · Rapido" },
  car: { label: "Own Vehicle", short: "CAR", color: "#10b981", bg: "#051510", icon: "car", line: "Fuel + Parking est." },
  multimodal: { label: "Multimodal Transit", short: "MULTI", color: "#ec4899", bg: "#1c0d18", icon: "transfer", line: "Bus + Metro + Auto combos" },
};

/* ─────────────────────────────────────────────────────────────
   ICONS
───────────────────────────────────────────────────────────── */
const P = {
  bus: "M8 6v6m8-6v6M3 16h18M5 4h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zM7 20h2m6 0h2",
  metro: "M3 7h18M3 12h18M5 7V5a2 2 0 012-2h10a2 2 0 012 2v2M5 17v2a2 2 0 002 2h10a2 2 0 002-2v-2",
  cab: "M5 17H3a2 2 0 01-2-2V9a2 2 0 012-2h3l2-4h4l2 4h3a2 2 0 012 2v6a2 2 0 01-2 2h-2M7.5 20.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm9 0a1.5 1.5 0 100-3 1.5 1.5 0 000 3z",
  car: "M19 17H5M5 17a2 2 0 01-2-2V9a2 2 0 012-2h3l2-3h4l2 3h3a2 2 0 012 2v6a2 2 0 01-2 2",
  walk: "M13 4a1 1 0 100-2 1 1 0 000 2zm-3 15l1-5 2 2v5h2v-6l-2-2 1-4m-2-3l-3 1v4H5v-5l5-2",
  transfer: "M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4",
  clock: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-6v-4l2.5-2.5",
  mappin: "M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0118 0zM12 13a3 3 0 100-6 3 3 0 000 6z",
  swap: "M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4",
  chevron: "M6 9l6 6 6-6",
  check: "M20 6L9 17l-5-5",
  arrow: "M5 12h14M12 5l7 7-7 7",
  now: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  save: "M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2zM17 21v-8H7v8M7 3v5h8",
  home: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z",
  grid: "M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z",
  table: "M3 3h18M3 9h18M3 15h18M9 3v18M15 3v18",
  trend: "M23 6l-9.5 9.5-5-5L1 18",
  share: "M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8M16 6l-4-4-4 4M12 2v13",
  info: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-7v-4m0-4h.01",
  alert: "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4m0 4h.01",
  search: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  x: "M18 6L6 18M6 6l12 12",
  list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  route: "M3 12h18M3 6h18M3 18h18",
  chat: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z",
  bolt: "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  compass: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-15l3.8 8.3-8.3-3.8z",
  gps: "M12 2v3m0 14v3m-10-10h3m14 0h3M12 21a9 9 0 110-18 9 9 0 010 18zm0-5a4 4 0 100-8 4 4 0 000 8z",
  star: "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.969 0 1.371 1.24.588 1.81l-3.97 2.88a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.97-2.88a1 1 0 00-1.176 0l-3.97 2.88c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.97-2.88c-.784-.57-.381-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z",
  folder: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z",
  bell: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
  rocket: "M15.59 14.37a6 6 0 01-5.84-5.84l4.25-4.25a2 2 0 012.83 0l2.83 2.83a2 2 0 010 2.83l-4.07 4.43zm-7.66.86A11.08 11.08 0 001.5 22.5a.5.5 0 00.5.5h7.13a11.08 11.08 0 007.27-6.43l-4.93-2.34-3.04 1z",
  doc: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  logout: "M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1",
  users: "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2m16-10a4 4 0 10-8 0 4 4 0 008 0z",
  bot: "M9 3h6M12 3v3M4 11a2 2 0 012-2h12a2 2 0 012 2v7a2 2 0 01-2 2H6a2 2 0 01-2-2v-7zm5 3h.01M15 14h.01M9 17h6",
  user: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z",
  sparkles: "M9.663 17h4.673M12 3v1m6.364.364l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  facebook: "M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z",
  twitter: "M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z",
  instagram: "M17 2H7a5 5 0 00-5 5v10a5 5 0 005 5h10a5 5 0 005-5V7a5 5 0 00-5-5z M16 11.37A4 4 0 1112.63 8 4 4 0 0116 11.37z M17.5 6.5h.01",
  youtube: "M22.54 6.42a2.78 2.78 0 00-1.95-1.96C18.88 4 12 4 12 4s-6.88 0-8.59.46a2.78 2.78 0 00-1.95 1.96A29 29 0 001 11.54a29 29 0 00.46 5.12 2.78 2.78 0 001.95 1.96C5.12 19.08 12 19.08 12 19.08s6.88 0 8.59 0a2.78 2.78 0 001.95-1.96 29 29 0 00.46-5.12 29 29 0 00-.46-5.12z M9.54 15.08V8l6 3.54-6 3.54z",
};


function Ic({ n, s = 16, c = "currentColor", sw = 1.8, style }) {
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none"
      stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style}>
      <path d={P[n] || P.info} />
    </svg>
  );
}

function Pill({ children, color, small }) {
  return (
    <span style={{
      background: color + "22", color, border: `1px solid ${color}44`,
      borderRadius: 20, padding: small ? "2px 8px" : "3px 11px",
      fontSize: small ? 10 : 11, fontWeight: 700,
      whiteSpace: "nowrap", display: "inline-block",
    }}>{children}</span>
  );
}

/* ─────────────────────────────────────────────────────────────
   API LAYER
───────────────────────────────────────────────────────────── */
async function apiCompare(src, dst, time, pref, vehicle) {
  const res = await fetch(`${API_BASE}/api/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source: src,
      destination: dst,
      time: time || null,
      preference: pref,
      vehicle: vehicle || null
    }),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const d = await res.json();
  return d;
}

async function apiAllBuses(src, dst, time) {
  const res = await fetch(`${API_BASE}/api/bmtc/all-buses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: src, destination: dst, time: time || null }),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function apiRouteSearch(route) {
  const res = await fetch(`${API_BASE}/api/bmtc/route-search?route=${encodeURIComponent(route)}`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function apiRouteSuggestions(q) {
  try {
    const res = await fetch(`${API_BASE}/api/bmtc/routes?q=${encodeURIComponent(q)}`);
    if (!res.ok) return [];
    const d = await res.json();
    return d.routes || [];
  } catch { return []; }
}

async function apiMetroTimetable(source = "", time = "") {
  let url = `${API_BASE}/api/timetable/metro`;
  const params = [];
  if (source) params.push(`source=${encodeURIComponent(source)}`);
  if (time) params.push(`time=${encodeURIComponent(time)}`);
  if (params.length > 0) {
    url += "?" + params.join("&");
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function apiRouteTimetable(route) {
  const res = await fetch(`${API_BASE}/api/bmtc/route-timetable?route=${encodeURIComponent(route)}`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function apiStops() {
  try {
    const [b, m] = await Promise.all([
      fetch(`${API_BASE}/api/bmtc/stops`).then(r => r.json()),
      fetch(`${API_BASE}/api/metro/stations`).then(r => r.json()),
    ]);
    const bmtcStops = b.stops || [];
    const metroStations = (m.stations || []).map(s => s.endsWith(" Metro Station") ? s : `${s} Metro Station`);
    return {
      bmtc: bmtcStops,
      metro: metroStations,
      all: [...new Set([...bmtcStops, ...metroStations])].sort(),
    };
  } catch { return { all: [], bmtc: [], metro: [] }; }
}

async function apiStopsCoords(stopsList) {
  try {
    const res = await fetch(`${API_BASE}/api/stops/coords`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stops: stopsList }),
    });
    if (!res.ok) return {};
    const d = await res.json();
    return d.coordinates || {};
  } catch { return {}; }
}

async function apiSignup(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Sign up failed");
  }
  return res.json();
}

async function apiLogin(username, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

async function apiSaveJourney(token, journey) {
  const res = await fetch(`${API_BASE}/api/user/journey`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(journey),
  });
  if (!res.ok) throw new Error("Failed to save journey");
  return res.json();
}

async function apiDeleteJourney(token, journeyId) {
  const res = await fetch(`${API_BASE}/api/user/journey/${journeyId}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("Failed to delete journey");
  return res.json();
}

async function apiGetDashboard(token) {
  const res = await fetch(`${API_BASE}/api/user/dashboard`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

function parseMapPos(s) {
  if (!s) return "";
  const match = String(s).match(/^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$/);
  if (match) {
    return { lat: parseFloat(match[1]), lng: parseFloat(match[2]) };
  }
  return s + ", Bengaluru";
}

async function apiGetVehicles(token) {
  const res = await fetch(`${API_BASE}/api/user/vehicles`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) throw new Error("Failed to fetch vehicles");
  return res.json();
}

async function apiAddVehicle(token, vehicle) {
  const res = await fetch(`${API_BASE}/api/user/vehicles`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(vehicle),
  });
  if (!res.ok) throw new Error("Failed to add vehicle");
  return res.json();
}

async function apiDeleteVehicle(token, vehicleId) {
  const res = await fetch(`${API_BASE}/api/user/vehicles/${vehicleId}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("Failed to delete vehicle");
  return res.json();
}

async function apiGetDocuments(token) {
  const res = await fetch(`${API_BASE}/api/user/documents`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

async function apiAddDocument(token, formData) {
  const res = await fetch(`${API_BASE}/api/user/documents`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`
    },
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload document");
  return res.json();
}

async function apiDeleteDocument(token, docId) {
  const res = await fetch(`${API_BASE}/api/user/documents/${docId}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

/* ─────────────────────────────────────────────────────────────
   LINEAR ROUTE MAP COMPONENT
───────────────────────────────────────────────────────────── */
function LinearRouteMap({ segments, activeMode }) {
  if (!segments || segments.length === 0) {
    return (
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24, textAlign: "center", color: C.muted, fontSize: 13 }}>
        No route selected. Select a route card to view the linear route map.
      </div>
    );
  }

  const segmentColors = ["#f97316", "#3b82f6", "#ec4899", "#14b8a6", "#eab308", "#ef4444"];

  // Collect all stops from all segments in order
  const stopsList = [];
  segments.forEach((seg, idx) => {
    let color = C.accent;
    const isMetro = seg.type === "metro";
    const isWalk = seg.type === "walk" || (seg.route && seg.route.toLowerCase().includes("walk"));

    if (isMetro) {
      const rName = (seg.route || "").toLowerCase();
      if (rName.includes("green")) color = "#22c55e";
      else if (rName.includes("purple")) color = "#8b5cf6";
      else if (rName.includes("yellow")) color = "#eab308";
      else color = "#8b5cf6";
    } else if (isWalk) {
      color = "#6b7a99";
    } else {
      const transitSegmentIdx = segments.filter((s, sIdx) => sIdx < idx && s.type !== "walk" && !(s.route && s.route.toLowerCase().includes("walk"))).length;
      color = segmentColors[transitSegmentIdx % segmentColors.length];
    }

    const segStops = seg.stops || [];
    if (segStops.length === 0) {
      if (seg.from && seg.to) {
        segStops.push(seg.from, seg.to);
      }
    }

    segStops.forEach((stop, sIdx) => {
      // Avoid duplicate stops at transfer boundary
      if (stopsList.length > 0 && stopsList[stopsList.length - 1].name === stop) {
        stopsList[stopsList.length - 1].isTransfer = true;
        stopsList[stopsList.length - 1].nextColor = color;
        stopsList[stopsList.length - 1].nextRoute = seg.route || "Walk";
        return;
      }
      stopsList.push({
        name: stop,
        color: color,
        route: seg.route || "Walk",
        isFirst: stopsList.length === 0,
        isLast: false,
        isTransfer: sIdx === 0 && stopsList.length > 0,
        type: seg.type
      });
    });
  });

  if (stopsList.length > 0) {
    stopsList[stopsList.length - 1].isLast = true;
  }

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20, minHeight: 340, display: "flex", flexDirection: "column", justifyContent: "center", boxSizing: "border-box" }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 12, letterSpacing: "0.05em" }}>LINEAR STATION TIMELINE (---o---o---)</div>

      {/* Scrollable Track Container */}
      <div style={{ overflowX: "auto", padding: "30px 10px 40px 10px", width: "100%", display: "flex", alignItems: "center", boxSizing: "border-box" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 0, position: "relative" }}>

          {stopsList.map((stop, sIdx) => {
            const isEndpoint = stop.isFirst || stop.isLast;
            const lineColor = stop.nextColor || stop.color;
            const routeLabel = stop.nextRoute || stop.route;
            const isTransfer = stop.isTransfer;

            return (
              <div key={sIdx} style={{ display: "flex", alignItems: "center", position: "relative" }}>

                {/* Station Node Wrapper */}
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 100, position: "relative", flexShrink: 0 }}>

                  {/* Stop Name Label Above Node */}
                  <div style={{
                    position: "absolute",
                    bottom: 24,
                    width: 130,
                    textAlign: "center",
                    fontSize: isEndpoint || isTransfer ? 12 : 10,
                    fontWeight: isEndpoint || isTransfer ? 700 : 500,
                    color: isEndpoint || isTransfer ? C.text : C.muted,
                    whiteSpace: "normal",
                    lineHeight: "13px",
                    height: 26,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}>
                    {stop.name}
                  </div>

                  {/* Circular Node */}
                  <div style={{
                    width: isEndpoint || isTransfer ? 16 : 10,
                    height: isEndpoint || isTransfer ? 16 : 10,
                    borderRadius: "50%",
                    background: isEndpoint ? stop.color : isTransfer ? "#fff" : stop.color,
                    border: `3px solid ${stop.color}`,
                    zIndex: 2,
                    boxShadow: isEndpoint ? `0 0 0 4px ${stop.color}44` : isTransfer ? `0 0 0 3px ${stop.color}44` : "none",
                    cursor: "pointer"
                  }} title={stop.name} />

                  {/* Label Below Node */}
                  <div style={{
                    position: "absolute",
                    top: 24,
                    fontSize: 9,
                    fontWeight: 800,
                    color: stop.color,
                    letterSpacing: "0.02em"
                  }}>
                    {stop.isFirst ? "START" : stop.isLast ? "DESTINATION" : isTransfer ? "TRANSFER" : "STOP"}
                  </div>
                </div>

                {/* Connection line between nodes */}
                {!stop.isLast && (
                  <div style={{
                    width: 60,
                    height: 5,
                    background: lineColor,
                    position: "relative",
                    zIndex: 1,
                    opacity: 0.85,
                    borderStyle: stop.type === "walk" ? "dashed" : "solid"
                  }}>
                    {/* Route tag label above the line */}
                    <div style={{
                      position: "absolute",
                      top: -16,
                      left: "50%",
                      transform: "translateX(-50%)",
                      fontSize: 8.5,
                      fontWeight: 800,
                      color: lineColor,
                      background: C.surface,
                      border: `1px solid ${lineColor}44`,
                      borderRadius: 4,
                      padding: "1px 5px",
                      whiteSpace: "nowrap"
                    }}>{routeLabel}</div>
                  </div>
                )}
              </div>
            );
          })}

        </div>
      </div>

      <div style={{ fontSize: 10, color: C.muted, textAlign: "center", marginTop: 14 }}>
        ↔ Scroll horizontally to view all intermediate stops.
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   HELPERS & GOOGLE MAPS COMPONENT
───────────────────────────────────────────────────────────── */
function getSegmentIndexForGuideStep(step, guide, segments) {
  if (!guide || !segments) return null;

  // Check if it's a walk step
  const isWalk = step.icon === "walk" || (step.text && step.text.toLowerCase().includes("walk")) || step.nav_url;
  if (isWalk) {
    const walkSteps = guide.filter(s => s.icon === "walk" || (s.text && s.text.toLowerCase().includes("walk")) || s.nav_url);
    const isFirstWalk = walkSteps.length > 0 && walkSteps[0].step === step.step;

    if (isFirstWalk) {
      const firstIdx = segments.findIndex(seg => seg.type === "walk");
      return firstIdx !== -1 ? firstIdx : "temp_start_walk";
    } else {
      let lastIdx = -1;
      for (let i = segments.length - 1; i >= 0; i--) {
        if (segments[i].type === "walk") {
          lastIdx = i;
          break;
        }
      }
      return lastIdx !== -1 ? lastIdx : "temp_end_walk";
    }
  } else if (step.icon === "metro" || step.icon === "bus") {
    const transitSteps = guide.filter(s => s.icon === "bus" || s.icon === "metro");
    const transitStepIdx = transitSteps.findIndex(s => s.step === step.step);
    if (transitStepIdx !== -1) {
      const transitSegments = segments.filter(seg => seg.type === "bmtc" || seg.type === "metro");
      const matchedSeg = transitSegments[transitStepIdx];
      if (matchedSeg) {
        return segments.indexOf(matchedSeg);
      }
    }
  }
  return null;
}

function GoogleMap({ src, dst, segments, activeMode, guide = null, activeSegmentIndex = null, setActiveSegmentIndex = () => { }, useOsm, setUseOsm }) {
  const ref = useRef(null);
  const mapRef = useRef(null);
  const osmMapRef = useRef(null);
  const [loaded, setLoaded] = useState(false);
  const [osmLoaded, setOsmLoaded] = useState(false);
  const coordsCacheRef = useRef({});
  const [userCoords, setUserCoords] = useState(null);

  useEffect(() => {
    const handleFallback = () => {
      setUseOsm(true);
    };
    window.addEventListener("osm_fallback", handleFallback);
    return () => window.removeEventListener("osm_fallback", handleFallback);
  }, [setUseOsm]);

  useEffect(() => {
    window.gm_authFailure = () => {
      console.warn("Google Maps authentication failed. Falling back to OpenStreetMap.");
      window._osmActive = true;
      window.dispatchEvent(new Event("osm_fallback"));
    };

    const key = getGoogleMapsKey();
    if (!key || key === "YOUR_GOOGLE_MAPS_API_KEY") {
      console.warn("No Google Maps API Key provided. Falling back to OpenStreetMap.");
      window._osmActive = true;
      window.dispatchEvent(new Event("osm_fallback"));
      return;
    }

    if (window.google) { setLoaded(true); return; }
    if (document.getElementById("gmaps-script")) {
      const s = document.getElementById("gmaps-script");
      const handleLoad = () => setLoaded(true);
      s.addEventListener("load", handleLoad);
      return () => s.removeEventListener("load", handleLoad);
    }
    const s = document.createElement("script");
    s.id = "gmaps-script";
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places`;
    s.async = true;
    s.onload = () => setLoaded(true);
    s.onerror = () => {
      console.warn("Google Maps script failed to load. Falling back to OpenStreetMap.");
      window._osmActive = true;
      window.dispatchEvent(new Event("osm_fallback"));
    };
    document.head.appendChild(s);
  }, []);

  useEffect(() => {
    if (!useOsm) return;
    if (window.L) { setOsmLoaded(true); return; }
    if (document.getElementById("leaflet-script")) {
      const s = document.getElementById("leaflet-script");
      const handleLoad = () => setOsmLoaded(true);
      s.addEventListener("load", handleLoad);
      return () => s.removeEventListener("load", handleLoad);
    }

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    link.id = "leaflet-css";
    document.head.appendChild(link);

    const s = document.createElement("script");
    s.id = "leaflet-script";
    s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    s.async = true;
    s.onload = () => setOsmLoaded(true);
    s.onerror = () => {
      console.error("Leaflet script failed to load.");
    };
    document.head.appendChild(s);
  }, [useOsm]);

  useEffect(() => {
    if (activeSegmentIndex === "temp_start_walk" || activeSegmentIndex === "temp_end_walk") {
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            setUserCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          },
          (err) => {
            console.warn("Could not get current location for navigation fallback:", err);
            setUserCoords({ lat: 12.9716, lng: 77.5946 });
          }
        );
      }
    }
  }, [activeSegmentIndex]);

  useEffect(() => {
    if (useOsm) {
      if (!osmLoaded || !ref.current) return;
    } else {
      if (!loaded || !ref.current) return;
    }

    if (!useOsm && !mapRef.current) {
      mapRef.current = new window.google.maps.Map(ref.current, {
        center: { lat: 12.9716, lng: 77.5946 }, zoom: 12,
        styles: [
          { elementType: "geometry", stylers: [{ color: "#0f1120" }] },
          { elementType: "labels.text.fill", stylers: [{ color: "#6b7a99" }] },
          { elementType: "labels.text.stroke", stylers: [{ color: "#0f1120" }] },
          { featureType: "road", elementType: "geometry", stylers: [{ color: "#1e2440" }] },
          { featureType: "road.highway", elementType: "geometry", stylers: [{ color: "#252d4a" }] },
          { featureType: "water", elementType: "geometry", stylers: [{ color: "#08090f" }] },
          { featureType: "poi", stylers: [{ visibility: "off" }] },
        ],
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: false,
        streetViewControl: false,
      });
      window.gMapInstance = mapRef.current;
    }
    const map = mapRef.current;

    // Collect all stop names from segments to resolve coordinates
    const allStopNames = [];
    if (src) allStopNames.push(src);
    if (dst) allStopNames.push(dst);
    if (segments) {
      segments.forEach(seg => {
        if (seg.from) allStopNames.push(seg.from);
        if (seg.to) allStopNames.push(seg.to);
        if (seg.stops) {
          seg.stops.forEach(st => allStopNames.push(st));
        }
      });
    }

    const uniqueStops = [...new Set(allStopNames)].filter(Boolean);

    const resolveAndRender = async () => {
      const cache = { ...coordsCacheRef.current };
      if (userCoords) {
        cache["current_location"] = userCoords;
      } else {
        cache["current_location"] = { lat: 12.9716, lng: 77.5946 };
      }

      // Auto-parse coordinate formats directly
      uniqueStops.forEach(stop => {
        if (!cache[stop]) {
          let match = String(stop).match(/\(\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)/);
          if (!match) {
            match = String(stop).match(/^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$/);
          }
          if (match) {
            cache[stop] = { lat: parseFloat(match[1]), lng: parseFloat(match[2]) };
          }
        }
      });

      const missing = uniqueStops.filter(s => !cache[s]);

      if (missing.length > 0) {
        try {
          const backendCoords = await apiStopsCoords(missing);
          Object.assign(cache, backendCoords);
        } catch (e) {
          console.error("Error fetching stop coords:", e);
        }

        // Fallback geocoding for any still-missing stops
        const stillMissing = uniqueStops.filter(s => !cache[s]);
        if (stillMissing.length > 0) {
          if (!useOsm && window.google && window.google.maps && window.google.maps.Geocoder) {
            const geocoder = new window.google.maps.Geocoder();
            const geocodePromises = stillMissing.map(stopName => {
              return new Promise((resolve) => {
                geocoder.geocode({ address: stopName + ", Bengaluru" }, (res, status) => {
                  if (status === "OK" && res && res[0]) {
                    const loc = res[0].geometry.location;
                    cache[stopName] = { lat: loc.lat(), lng: loc.lng() };
                  }
                  resolve();
                });
              });
            });
            await Promise.all(geocodePromises);
          } else {
            // OSM Geocoding fallback (Nominatim)
            const geocodePromises = stillMissing.map(stopName => {
              return fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(stopName + ", Bengaluru")}&format=json&limit=1`)
                .then(r => r.json())
                .then(data => {
                  if (data && data[0]) {
                    cache[stopName] = { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon) };
                  }
                })
                .catch(err => console.warn("OSM geocoding failed for stop:", stopName, err));
            });
            await Promise.all(geocodePromises);
          }
        }
      }

      if (useOsm && window.L) {
        // Render Leaflet OSM
        if (osmMapRef.current) {
          osmMapRef.current.remove();
          osmMapRef.current = null;
        }
        if (ref.current) {
          ref.current.innerHTML = ""; // Clear any previous Google Map elements to prevent collision
        }

        const osmMap = window.L.map(ref.current).setView([12.9716, 77.5946], 12);
        osmMapRef.current = osmMap;
        window.osmMapInstance = osmMap;

        window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; OpenStreetMap &copy; CartoDB',
          subdomains: 'abcd',
          maxZoom: 20
        }).addTo(osmMap);

        const markers = [];
        const latlngs = [];

        let srcPos = cache[src];
        let dstPos = cache[dst];

        if (srcPos && activeSegmentIndex === null) {
          const m = window.L.circleMarker([srcPos.lat, srcPos.lng], {
            radius: 8,
            fillColor: "#22c55e",
            fillOpacity: 1,
            color: "#ffffff",
            weight: 2
          }).addTo(osmMap).bindPopup(`Start: ${src}`);
          markers.push(m);
        }

        if (dstPos && activeSegmentIndex === null) {
          const m = window.L.circleMarker([dstPos.lat, dstPos.lng], {
            radius: 8,
            fillColor: "#ef4444",
            fillOpacity: 1,
            color: "#ffffff",
            weight: 2
          }).addTo(osmMap).bindPopup(`Destination: ${dst}`);
          markers.push(m);
        }

        let segmentsToRender = segments || [];
        if (activeSegmentIndex === "temp_start_walk") {
          const destinationStop = segments && segments[0] ? (segments[0].from || "") : (src || "");
          segmentsToRender = [{
            type: "walk",
            route: "Walk",
            from: "current_location",
            to: destinationStop,
            stops: ["current_location", destinationStop]
          }];
        } else if (activeSegmentIndex === "temp_end_walk") {
          const originStop = segments && segments.length > 0 ? (segments[segments.length - 1].to || "") : (dst || "");
          segmentsToRender = [{
            type: "walk",
            route: "Walk",
            from: originStop,
            to: "current_location",
            stops: [originStop, "current_location"]
          }];
        } else if (activeSegmentIndex !== null) {
          segmentsToRender = segments && segments[activeSegmentIndex] ? [segments[activeSegmentIndex]] : [];
        }

        if (segmentsToRender && segmentsToRender.length > 0) {
          const segmentColors = ["#f97316", "#3b82f6", "#ec4899", "#14b8a6", "#eab308", "#ef4444"];
          segmentsToRender.forEach((seg, idx) => {
            let color = C.accent;
            const isMetro = seg.type === "metro";
            const isWalk = seg.type === "walk" || (seg.route && seg.route.toLowerCase().includes("walk"));

            if (isMetro) {
              const rName = (seg.route || "").toLowerCase();
              if (rName.includes("green")) color = "#22c55e";
              else if (rName.includes("purple")) color = "#8b5cf6";
              else if (rName.includes("yellow")) color = "#eab308";
              else color = "#8b5cf6";
            } else if (isWalk) {
              color = "#6b7a99";
            } else {
              const transitSegmentIdx = segmentsToRender.filter((s, sIdx) => sIdx < idx && s.type !== "walk" && !(s.route && s.route.toLowerCase().includes("walk"))).length;
              color = segmentColors[transitSegmentIdx % segmentColors.length];
            }

            const segStops = seg.stops || [];
            const pathCoords = segStops.map(s => cache[s]).filter(Boolean);

            if (pathCoords.length > 1) {
              const leafletPath = pathCoords.map(c => [c.lat, c.lng]);
              window.L.polyline(leafletPath, {
                color: color,
                weight: 5,
                opacity: 0.85,
                dashArray: isWalk ? "5, 10" : undefined
              }).addTo(osmMap);
              leafletPath.forEach(pt => latlngs.push(pt));
            }

            segStops.forEach(stopName => {
              const pos = cache[stopName];
              if (!pos) return;
              latlngs.push([pos.lat, pos.lng]);

              const isStartOfLeg = stopName === seg.from;
              const isEndOfLeg = stopName === seg.to;
              const isTransferStop = isStartOfLeg || isEndOfLeg;

              let markerColor = color;
              if (stopName.toLowerCase() === (src || "").toLowerCase()) {
                markerColor = "#22c55e";
              } else if (stopName.toLowerCase() === (dst || "").toLowerCase()) {
                markerColor = "#ef4444";
              }

              const m = window.L.circleMarker([pos.lat, pos.lng], {
                radius: isTransferStop ? 6 : 4,
                fillColor: isTransferStop ? markerColor : "#ffffff",
                fillOpacity: 1,
                color: isTransferStop ? "#ffffff" : markerColor,
                weight: isTransferStop ? 2 : 1.5
              }).addTo(osmMap).bindPopup(`<strong>${stopName}</strong>${seg.route ? `<br/>Line: ${seg.route}` : ""}`);
              markers.push(m);
            });
          });
        } else {
          if (srcPos && dstPos) {
            window.L.polyline([[srcPos.lat, srcPos.lng], [dstPos.lat, dstPos.lng]], {
              color: "#3b82f6",
              weight: 5
            }).addTo(osmMap);
            latlngs.push([srcPos.lat, srcPos.lng], [dstPos.lat, dstPos.lng]);
          }
        }

        if (latlngs.length > 0) {
          osmMap.fitBounds(latlngs, { padding: [30, 30] });
        }
        return;
      }

      // Clear previous map objects
      if (window._utrsMarkers) window._utrsMarkers.forEach(m => m.setMap(null));
      window._utrsMarkers = [];

      if (window._utrsRenderers) window._utrsRenderers.forEach(r => r.setMap(null));
      window._utrsRenderers = [];

      if (window._utrsPolylines) window._utrsPolylines.forEach(p => p.setMap(null));
      window._utrsPolylines = [];

      const bounds = new window.google.maps.LatLngBounds();

      // Plot Start and Destination Markers (Only when not navigating a single segment)
      let srcPos = cache[src];
      let dstPos = cache[dst];

      if (srcPos && activeSegmentIndex === null) {
        const sm = new window.google.maps.Marker({
          map, position: srcPos, title: `Start: ${src}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 9,
            fillColor: C.green,
            fillOpacity: 1,
            strokeColor: "#fff",
            strokeWeight: 2
          }
        });
        window._utrsMarkers.push(sm);
        bounds.extend(srcPos);
      }

      if (dstPos && activeSegmentIndex === null) {
        const dm = new window.google.maps.Marker({
          map, position: dstPos, title: `Destination: ${dst}`,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 9,
            fillColor: C.red,
            fillOpacity: 1,
            strokeColor: "#fff",
            strokeWeight: 2
          }
        });
        window._utrsMarkers.push(dm);
        bounds.extend(dstPos);
      }

      // Resolve segments to render dynamically
      let segmentsToRender = segments || [];

      if (activeSegmentIndex === "temp_start_walk") {
        const destinationStop = segments && segments[0] ? (segments[0].from || "") : (src || "");
        segmentsToRender = [{
          type: "walk",
          route: "Walk",
          from: "current_location",
          to: destinationStop,
          stops: ["current_location", destinationStop]
        }];
      } else if (activeSegmentIndex === "temp_end_walk") {
        const originStop = segments && segments.length > 0 ? (segments[segments.length - 1].to || "") : (dst || "");
        segmentsToRender = [{
          type: "walk",
          route: "Walk",
          from: originStop,
          to: "current_location",
          stops: [originStop, "current_location"]
        }];
      } else if (activeSegmentIndex !== null) {
        segmentsToRender = segments && segments[activeSegmentIndex] ? [segments[activeSegmentIndex]] : [];
      }

      // Render segments
      if (segmentsToRender && segmentsToRender.length > 0) {
        const segmentColors = ["#f97316", "#3b82f6", "#ec4899", "#14b8a6", "#eab308", "#ef4444"];

        segmentsToRender.forEach((seg, idx) => {
          let color = C.accent;
          const isMetro = seg.type === "metro";
          const isWalk = seg.type === "walk" || (seg.route && seg.route.toLowerCase().includes("walk"));

          if (isMetro) {
            const rName = (seg.route || "").toLowerCase();
            if (rName.includes("green")) color = "#22c55e";
            else if (rName.includes("purple")) color = "#8b5cf6";
            else if (rName.includes("yellow")) color = "#eab308";
            else color = "#8b5cf6"; // default purple metro
          } else if (isWalk) {
            color = "#6b7a99";
          } else {
            // Alternate colors for transfer transit legs
            const transitSegmentIdx = segmentsToRender.filter((s, sIdx) => sIdx < idx && s.type !== "walk" && !(s.route && s.route.toLowerCase().includes("walk"))).length;
            color = segmentColors[transitSegmentIdx % segmentColors.length];
          }

          const segStops = seg.stops || [];
          const pathCoords = segStops.map(s => cache[s]).filter(Boolean);

          // Plot intermediate stop markers
          segStops.forEach(stopName => {
            const pos = cache[stopName];
            if (!pos) return;
            bounds.extend(pos);

            // Skip global bounds markers ONLY if in overview mode
            const isGlobalBound = stopName.toLowerCase() === (src || "").toLowerCase() || stopName.toLowerCase() === (dst || "").toLowerCase();
            if (isGlobalBound && activeSegmentIndex === null) return;

            const isStartOfLeg = stopName === seg.from;
            const isEndOfLeg = stopName === seg.to;
            const isTransferStop = isStartOfLeg || isEndOfLeg;

            // Highlight start/end if it corresponds to global start/dest
            let markerColor = color;
            if (stopName.toLowerCase() === (src || "").toLowerCase()) {
              markerColor = C.green;
            } else if (stopName.toLowerCase() === (dst || "").toLowerCase()) {
              markerColor = C.red;
            }

            const stopMarker = new window.google.maps.Marker({
              map,
              position: pos,
              title: stopName,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: isTransferStop ? 6 : 4,
                fillColor: isTransferStop ? markerColor : "#fff",
                fillOpacity: 1,
                strokeColor: isTransferStop ? "#fff" : markerColor,
                strokeWeight: isTransferStop ? 2 : 1.5,
              }
            });

            const info = new window.google.maps.InfoWindow({
              content: `<div style="color:#000;font-size:12px;font-family:sans-serif;padding:2px 4px;"><strong>${stopName}</strong>${seg.route ? `<br/>Line: ${seg.route}` : ""}</div>`
            });
            stopMarker.addListener("mouseover", () => info.open(map, stopMarker));
            stopMarker.addListener("mouseout", () => info.close());
            stopMarker.addListener("click", () => info.open(map, stopMarker));

            window._utrsMarkers.push(stopMarker);
          });

          // Draw the segment line
          if (isMetro) {
            if (pathCoords.length > 1) {
              const poly = new window.google.maps.Polyline({
                map, path: pathCoords, strokeColor: color, strokeWeight: 5, strokeOpacity: 0.9
              });
              window._utrsPolylines.push(poly);
            }
          } else if (isWalk) {
            if (seg.from && seg.to) {
              const ds = new window.google.maps.DirectionsService();
              const dr = new window.google.maps.DirectionsRenderer({
                map, suppressMarkers: true,
                preserveViewport: activeSegmentIndex === null,
                polylineOptions: {
                  strokeColor: color, strokeWeight: 4, strokeOpacity: 0,
                  icons: [{
                    icon: { path: "M 0,-1 0,1", strokeOpacity: 0.8, scale: 3 },
                    offset: "0", repeat: "15px"
                  }]
                }
              });
              ds.route({
                origin: cache[seg.from] || parseMapPos(seg.from),
                destination: cache[seg.to] || parseMapPos(seg.to),
                travelMode: "WALKING"
              }, (res, status) => {
                if (status === "OK") {
                  dr.setDirections(res);
                } else {
                  console.warn("Walking DirectionsService failed, drawing straight fallback polyline.", status);
                  if (pathCoords.length > 1) {
                    const poly = new window.google.maps.Polyline({
                      map, path: pathCoords, strokeColor: color, strokeWeight: 4, strokeOpacity: 0,
                      icons: [{
                        icon: { path: "M 0,-1 0,1", strokeOpacity: 0.8, scale: 3 },
                        offset: "0", repeat: "15px"
                      }]
                    });
                    window._utrsPolylines.push(poly);
                  }
                }
              });
              window._utrsRenderers.push(dr);
            } else if (pathCoords.length > 1) {
              const poly = new window.google.maps.Polyline({
                map, path: pathCoords, strokeColor: color, strokeWeight: 4, strokeOpacity: 0,
                icons: [{
                  icon: { path: "M 0,-1 0,1", strokeOpacity: 0.8, scale: 3 },
                  offset: "0", repeat: "15px"
                }]
              });
              window._utrsPolylines.push(poly);
            }
          } else {
            // Bus, Cab, Car
            if (seg.from && seg.to) {
              const ds = new window.google.maps.DirectionsService();
              const dr = new window.google.maps.DirectionsRenderer({
                map, suppressMarkers: true,
                preserveViewport: activeSegmentIndex === null,
                polylineOptions: { strokeColor: color, strokeWeight: 5, strokeOpacity: 0.85 }
              });

              let waypoints = [];
              if (segStops.length > 2) {
                const innerStops = segStops.slice(1, -1);
                const maxWaypoints = 15;
                const step = Math.ceil(innerStops.length / maxWaypoints);
                const sampled = innerStops.filter((_, sidx) => sidx % step === 0);
                waypoints = sampled.map(stopName => ({
                  location: cache[stopName] || parseMapPos(stopName), stopover: false
                }));
              }

              ds.route({
                origin: cache[seg.from] || parseMapPos(seg.from),
                destination: cache[seg.to] || parseMapPos(seg.to),
                waypoints: waypoints,
                optimizeWaypoints: false,
                travelMode: "DRIVING"
              }, (res, status) => {
                if (status === "OK") {
                  dr.setDirections(res);
                } else {
                  console.warn("Directions failed for segment, falling back to Polyline.", status);
                  if (pathCoords.length > 1) {
                    const poly = new window.google.maps.Polyline({
                      map, path: pathCoords, strokeColor: color, strokeWeight: 5, strokeOpacity: 0.8
                    });
                    window._utrsPolylines.push(poly);
                  }
                }
              });
              window._utrsRenderers.push(dr);
            }
          }
        });
      } else {
        // Fallback for simple src -> dst driving directions when no segments
        if (srcPos && dstPos) {
          const ds = new window.google.maps.DirectionsService();
          const dr = new window.google.maps.DirectionsRenderer({
            map, suppressMarkers: true,
            preserveViewport: activeSegmentIndex === null,
            polylineOptions: { strokeColor: C.accent, strokeWeight: 5, strokeOpacity: 0.85 }
          });
          ds.route({
            origin: srcPos, destination: dstPos, travelMode: "DRIVING"
          }, (res, status) => { if (status === "OK") dr.setDirections(res); });
          window._utrsRenderers.push(dr);
        }
      }

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds);
        const listener = window.google.maps.event.addListener(map, "idle", () => {
          if (map.getZoom() > 16) map.setZoom(16);
          window.google.maps.event.removeListener(listener);
        });
      }
    };

    resolveAndRender();
  }, [loaded, useOsm, osmLoaded, src, dst, segments, activeMode, activeSegmentIndex, userCoords]);


  // Compute navigation legs
  const navLegs = [];
  if (guide && segments) {
    guide.forEach(step => {
      const segIdx = getSegmentIndexForGuideStep(step, guide, segments);
      if (segIdx !== null) {
        navLegs.push({ step: step.step, segIdx, text: step.text, duration: step.duration, detail: step.detail, icon: step.icon });
      }
    });
  }

  const currentLegIdx = navLegs.findIndex(leg => leg.segIdx === activeSegmentIndex);
  const currentLeg = currentLegIdx !== -1 ? navLegs[currentLegIdx] : null;

  return (
    <div style={{ position: "relative", height: "100%", minHeight: 340, borderRadius: 16, overflow: "hidden", border: `1px solid ${C.border}` }}>
      <div ref={ref} style={{ width: "100%", height: "100%", minHeight: 340 }} />
      {!(useOsm ? osmLoaded : loaded) && (
        <div style={{
          position: "absolute", inset: 0, background: C.surface,
          display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 10,
          zIndex: 999
        }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: `3px solid ${C.accent}`, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
          <div style={{ fontSize: 12, color: C.muted }}>Loading map…</div>
        </div>
      )}
      {useOsm && (
        <div style={{
          position: "absolute", top: 12, left: 52, background: "rgba(15, 17, 32, 0.85)",
          backdropFilter: "blur(8px)", border: `1px solid ${C.border2}`, borderRadius: 8,
          padding: "5px 10px", fontSize: 10, color: C.muted, fontWeight: 700, zIndex: 1000, pointerEvents: "none"
        }}>
          🗺️ OpenStreetMap Backup
        </div>
      )}

      {src && activeSegmentIndex === null && <div style={{ position: "absolute", bottom: 46, left: 12, background: C.green + "ee", borderRadius: 7, padding: "3px 9px", fontSize: 11, color: "white", fontWeight: 700, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>🟢 {src}</div>}
      {dst && activeSegmentIndex === null && <div style={{ position: "absolute", bottom: 12, left: 12, background: C.red + "ee", borderRadius: 7, padding: "3px 9px", fontSize: 11, color: "white", fontWeight: 700, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>🔴 {dst}</div>}
      {activeMode && activeSegmentIndex === null && <div style={{ position: "absolute", top: 12, right: 12, background: MC[activeMode]?.color + "dd", borderRadius: 8, padding: "4px 10px", fontSize: 11, color: "white", fontWeight: 700 }}>{MC[activeMode]?.short} Route</div>}

      {/* Floating Navigation Card Overlay */}
      {activeSegmentIndex !== null && currentLeg && (
        <div style={{
          position: "absolute",
          top: 12,
          left: 12,
          right: 12,
          background: "rgba(15, 17, 32, 0.9)",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          border: `1px solid ${C.border2}`,
          borderRadius: 12,
          padding: "12px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
          zIndex: 10,
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
          animation: "fadeIn 0.25s ease-out"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: C.accent, letterSpacing: "0.05em" }}>
                NAVIGATION: STEP {currentLegIdx + 1} OF {navLegs.length}
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginTop: 2 }}>
                {currentLeg.text}
              </div>
              <div style={{ fontSize: 11, color: C.accent, marginTop: 4, fontWeight: 600 }}>
                {currentLeg.duration && `${currentLeg.duration}`}
                {currentLeg.detail && ` · ${currentLeg.detail}`}
              </div>
            </div>
            <button
              onClick={() => setActiveSegmentIndex(null)}
              style={{
                background: "rgba(255, 255, 255, 0.05)",
                border: "none",
                borderRadius: "50%",
                width: 24,
                height: 24,
                color: C.muted,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transition: "all 0.15s"
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)"; e.currentTarget.style.color = "#fff"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"; e.currentTarget.style.color = C.muted; }}
            >
              <Ic n="x" s={12} />
            </button>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => {
                if (currentLegIdx > 0) {
                  setActiveSegmentIndex(navLegs[currentLegIdx - 1].segIdx);
                } else {
                  setActiveSegmentIndex(null);
                }
              }}
              style={{
                flex: 1,
                background: "rgba(255, 255, 255, 0.05)",
                border: `1px solid ${C.border2}`,
                borderRadius: 8,
                color: C.text,
                padding: "8px 12px",
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "inherit",
                transition: "all 0.15s"
              }}
              onMouseEnter={e => e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)"}
              onMouseLeave={e => e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)"}
            >
              Prev Step
            </button>
            <button
              onClick={() => {
                if (currentLegIdx < navLegs.length - 1) {
                  setActiveSegmentIndex(navLegs[currentLegIdx + 1].segIdx);
                } else {
                  setActiveSegmentIndex(null);
                }
              }}
              style={{
                flex: 2,
                background: C.accent,
                border: "none",
                borderRadius: 8,
                color: "#fff",
                padding: "8px 12px",
                fontSize: 12,
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "inherit",
                boxShadow: `0 4px 12px ${C.accent}44`,
                transition: "all 0.15s"
              }}
              onMouseEnter={e => e.currentTarget.style.filter = "brightness(1.1)"}
              onMouseLeave={e => e.currentTarget.style.filter = "none"}
            >
              {currentLegIdx < navLegs.length - 1 ? (
                `Next: ${navLegs[currentLegIdx + 1].icon === "walk" ? "Walk" : navLegs[currentLegIdx + 1].icon.toUpperCase()}`
              ) : "Finish Navigation"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AUTOCOMPLETE INPUT
───────────────────────────────────────────────────────────── */
function StopInput({ value, onChange, placeholder, dot, options, showGps }) {
  const [open, setOpen] = useState(false);
  const [locLoading, setLocLoading] = useState(false);
  const [googlePredictions, setGooglePredictions] = useState([]);
  const [osmPredictions, setOsmPredictions] = useState([]);
  const [useOsm, setUseOsm] = useState(() => {
    if (localStorage.getItem("force_osm") === "true") return true;
    if (localStorage.getItem("force_osm") === "false") return false;
    return !!window._osmActive || !window.google;
  });
  const serviceRef = useRef(null);

  useEffect(() => {
    const handleFallback = () => {
      setUseOsm(true);
    };
    window.addEventListener("osm_fallback", handleFallback);
    return () => window.removeEventListener("osm_fallback", handleFallback);
  }, []);

  useEffect(() => {
    if (window.google && !serviceRef.current) {
      serviceRef.current = new window.google.maps.places.AutocompleteService();
    }
  }, [window.google]);

  useEffect(() => {
    if (!value || value.trim().length < 2) {
      setGooglePredictions([]);
      setOsmPredictions([]);
      return;
    }

    // Skip predictions if input is already coordinates or formatted coordinates
    const hasCoords = /\(\s*-?\d+\.\d+\s*,\s*-?\d+\.\d+\s*\)/.test(value) || /^\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*$/.test(value);
    if (hasCoords) {
      setGooglePredictions([]);
      setOsmPredictions([]);
      return;
    }

    const delayDebounce = setTimeout(() => {
      if (useOsm) {
        // Fetch suggestions from Photon API (focusing on Bengaluru location)
        fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(value)}&lat=12.9716&lon=77.5946&limit=5`)
          .then(res => res.json())
          .then(data => {
            if (data && data.features) {
              const predictions = data.features.map(f => {
                const name = f.properties.name || "";
                const city = f.properties.city || f.properties.town || f.properties.county || "";
                const description = city ? `${name}, ${city}` : name;
                return {
                  place_id: f.properties.osm_id || Math.random().toString(),
                  description,
                  structured_formatting: {
                    main_text: name,
                    secondary_text: city || "Bengaluru, Karnataka"
                  },
                  coordinates: {
                    lat: f.geometry.coordinates[1],
                    lng: f.geometry.coordinates[0]
                  }
                };
              });
              setOsmPredictions(predictions);
            } else {
              setOsmPredictions([]);
            }
          })
          .catch(err => {
            console.error("Photon API suggestions error:", err);
            setOsmPredictions([]);
          });
      } else {
        if (window.google && !serviceRef.current) {
          serviceRef.current = new window.google.maps.places.AutocompleteService();
        }

        if (!serviceRef.current) return;

        serviceRef.current.getPlacePredictions({
          input: value,
          locationBias: {
            radius: 25000,
            center: { lat: 12.9716, lng: 77.5946 }
          },
          componentRestrictions: { country: "in" }
        }, (predictions, status) => {
          if (window.google && status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
            setGooglePredictions(predictions.slice(0, 5));
          } else {
            setGooglePredictions([]);
            if (status === "REQUEST_DENIED" || status === "OVER_QUERY_LIMIT") {
              console.warn("Google places predictions failed: " + status + ". Triggering OSM fallback.");
              window._osmActive = true;
              window.dispatchEvent(new Event("osm_fallback"));
            }
          }
        });
      }
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [value, useOsm]);

  const handleGps = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser");
      return;
    }
    setLocLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocLoading(false);
        const { latitude, longitude } = position.coords;
        onChange(`${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);
      },
      (error) => {
        setLocLoading(false);
        alert(`Location permission denied or failed: ${error.message}`);
      }
    );
  };

  const handleSelectGooglePlace = (p) => {
    setOpen(false);
    setLocLoading(true);
    if (!window.google) {
      setLocLoading(false);
      alert("Google Maps is loading. Please try again in a moment.");
      return;
    }

    // Try PlacesService.getDetails first since Places API is already verified to be enabled
    try {
      const dummyDiv = document.createElement("div");
      const service = new window.google.maps.places.PlacesService(dummyDiv);
      service.getDetails({
        placeId: p.place_id,
        fields: ["geometry", "name"]
      }, (place, status) => {
        if (status === window.google.maps.places.PlacesServiceStatus.OK && place && place.geometry && place.geometry.location) {
          setLocLoading(false);
          const loc = place.geometry.location;
          const lat = loc.lat().toFixed(6);
          const lng = loc.lng().toFixed(6);
          const placeName = p.structured_formatting.main_text || place.name || p.description;
          onChange(`${placeName} (${lat}, ${lng})`);
        } else {
          console.warn("Google PlacesService.getDetails failed:", status, ". Trying Geocoder.");
          fallbackToGeocoder(p, status);
        }
      });
    } catch (err) {
      console.error("PlacesService initialization failed, trying Geocoder:", err);
      fallbackToGeocoder(p, "SERVICE_INIT_ERROR");
    }
  };

  const fallbackToGeocoder = (p, originalDetailsStatus) => {
    const geocoder = new window.google.maps.Geocoder();
    geocoder.geocode({ placeId: p.place_id }, (results, status) => {
      if (status === "OK" && results && results[0]) {
        setLocLoading(false);
        const loc = results[0].geometry.location;
        const lat = loc.lat().toFixed(6);
        const lng = loc.lng().toFixed(6);
        const placeName = p.structured_formatting.main_text || p.description;
        onChange(`${placeName} (${lat}, ${lng})`);
      } else {
        console.warn("Google Maps geocode by placeId failed:", status);
        geocoder.geocode({ address: p.description }, (results2, status2) => {
          if (status2 === "OK" && results2 && results2[0]) {
            setLocLoading(false);
            const loc2 = results2[0].geometry.location;
            const lat = loc2.lat().toFixed(6);
            const lng = loc2.lng().toFixed(6);
            const placeName = p.structured_formatting.main_text || p.description;
            onChange(`${placeName} (${lat}, ${lng})`);
          } else {
            console.warn("Google Maps geocode by address fallback failed:", status2);
            fallbackToOsm(p, originalDetailsStatus, status, status2);
          }
        });
      }
    });
  };

  const fallbackToOsm = (p, placeDetailsStatus, placeIdStatus, addressStatus) => {
    const buildOsmQueries = (desc) => {
      const qs = [desc];
      const parts = desc.split(",").map(p => p.trim()).filter(Boolean);
      if (parts.length > 2) {
        qs.push(`${parts[0]}, ${parts[1]}`);
        qs.push(parts[0]);
        // Try stripping layout suffixes or factory suffixes
        const cleanFirst = parts[0].split("-")[0].trim();
        if (cleanFirst !== parts[0]) {
          qs.push(cleanFirst);
          qs.push(`${cleanFirst}, Bengaluru`);
        }
      } else if (parts.length > 1) {
        qs.push(parts[0]);
      }

      const cleanParts = parts.map(p => p.replace(/\b(opp|opposite|near|behind|beside|next to)\b.*$/i, "").trim()).filter(Boolean);
      if (cleanParts.length > 0 && cleanParts[0] !== parts[0]) {
        qs.push(cleanParts[0]);
        if (cleanParts.length > 1) {
          qs.push(`${cleanParts[0]}, ${cleanParts[1]}`);
        }
      }
      return [...new Set(qs)];
    };

    const queriesToTry = buildOsmQueries(p.description);

    const tryGeocode = (index) => {
      if (index >= queriesToTry.length) {
        setLocLoading(false);
        alert(`Could not resolve coordinates for "${p.description}".\n\nGoogle API Errors:\n- PlacesService: ${placeDetailsStatus}\n- Geocoder (Place ID): ${placeIdStatus}\n- Geocoder (Address): ${addressStatus}\n\nOSM Fallback: Tried ${queriesToTry.length} address variants, but no matches were found.`);
        return;
      }
      const query = queriesToTry[index];
      fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&lat=12.9716&lon=77.5946&limit=1`)
        .then(res => res.json())
        .then(data => {
          if (data && data.features && data.features.length > 0) {
            setLocLoading(false);
            const feat = data.features[0];
            const lat = feat.geometry.coordinates[1].toFixed(6);
            const lng = feat.geometry.coordinates[0].toFixed(6);
            const placeName = p.structured_formatting.main_text || p.description;
            onChange(`${placeName} (${lat}, ${lng})`);
          } else {
            tryGeocode(index + 1);
          }
        })
        .catch(err => {
          console.error(`Photon geocoding error for "${query}":`, err);
          tryGeocode(index + 1);
        });
    };

    tryGeocode(0);
  };

  const handleSelectOsmPlace = (p) => {
    setOpen(false);
    const lat = p.coordinates.lat.toFixed(6);
    const lng = p.coordinates.lng.toFixed(6);
    const placeName = p.structured_formatting.main_text;
    onChange(`${placeName} (${lat}, ${lng})`);
  };

  const localFiltered = (options || []).filter(s =>
    s.toLowerCase().includes(value.toLowerCase()) && s !== value
  ).slice(0, 5);

  const hasAnyDropdownData = localFiltered.length > 0 || (useOsm ? osmPredictions.length > 0 : googlePredictions.length > 0);

  return (
    <div style={{ position: "relative", flex: 1 }}>
      <div style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", zIndex: 2 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: dot, border: `2px solid ${dot}88` }} />
      </div>

      <input value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        placeholder={placeholder}
        style={{
          width: "100%",
          boxSizing: "border-box",
          background: C.surface,
          border: `1.5px solid ${C.border2}`,
          borderRadius: 12,
          color: C.text,
          padding: `13px ${showGps ? '36px' : '14px'} 13px 34px`,
          fontSize: 14,
          outline: "none",
          fontFamily: "inherit"
        }}
      />

      {showGps && (
        <button
          onClick={handleGps}
          disabled={locLoading}
          style={{
            position: "absolute",
            right: 12,
            top: "50%",
            transform: "translateY(-50%)",
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 2
          }}
          title="Use current location"
        >
          {locLoading ? (
            <span style={{
              display: "inline-block",
              width: 14,
              height: 14,
              border: `2px solid ${C.accent}`,
              borderTopColor: "transparent",
              borderRadius: "50%",
              animation: "spin 1s linear infinite"
            }} />
          ) : (
            <Ic n="gps" s={15} c={C.muted} />
          )}
        </button>
      )}

      {open && hasAnyDropdownData && (
        <div style={{
          position: "absolute",
          top: "calc(100% + 4px)",
          left: 0,
          right: 0,
          background: C.card,
          border: `1px solid ${C.border2}`,
          borderRadius: 12,
          zIndex: 200,
          maxHeight: 280,
          overflowY: "auto",
          boxShadow: "0 16px 48px #00000090"
        }}>
          {localFiltered.length > 0 && (
            <div>
              <div style={{
                padding: "8px 12px 4px",
                fontSize: 10,
                color: C.accent,
                fontWeight: 800,
                textTransform: "uppercase",
                letterSpacing: "0.05em",
                borderBottom: `1px solid ${C.border}`
              }}>Transit Stops</div>
              {localFiltered.map(s => {
                const isMetro = s.toLowerCase().includes("metro") || s.toLowerCase().includes("station");
                return (
                  <div key={s} onMouseDown={() => { onChange(s); setOpen(false); }}
                    style={{
                      padding: "10px 14px",
                      cursor: "pointer",
                      fontSize: 13,
                      color: C.text,
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      borderBottom: `1px solid ${C.border}`
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = C.surface}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <Ic n={isMetro ? "metro" : "bus"} s={12} c={isMetro ? C.metro : C.accent} />
                    {s}
                  </div>
                );
              })}
            </div>
          )}

          {useOsm ? (
            osmPredictions.length > 0 && (
              <div>
                <div style={{
                  padding: "8px 12px 4px",
                  fontSize: 10,
                  color: C.muted,
                  fontWeight: 800,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  borderTop: localFiltered.length > 0 ? `1px solid ${C.border}` : "none",
                  borderBottom: `1px solid ${C.border}`
                }}>OpenStreetMap Places</div>
                {osmPredictions.map(p => (
                  <div key={p.place_id} onMouseDown={() => handleSelectOsmPlace(p)}
                    style={{
                      padding: "10px 14px",
                      cursor: "pointer",
                      fontSize: 13,
                      color: C.text,
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 8,
                      borderBottom: `1px solid ${C.border}`
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = C.surface}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <div style={{ marginTop: 2 }}>
                      <Ic n="mappin" s={12} c={C.muted} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 12.5 }}>{p.structured_formatting.main_text}</div>
                      <div style={{ fontSize: 11, color: C.muted }}>{p.structured_formatting.secondary_text}</div>
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            googlePredictions.length > 0 && (
              <div>
                <div style={{
                  padding: "8px 12px 4px",
                  fontSize: 10,
                  color: C.muted,
                  fontWeight: 800,
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                  borderTop: localFiltered.length > 0 ? `1px solid ${C.border}` : "none",
                  borderBottom: `1px solid ${C.border}`
                }}>Google Maps Places</div>
                {googlePredictions.map(p => (
                  <div key={p.place_id} onMouseDown={() => handleSelectGooglePlace(p)}
                    style={{
                      padding: "10px 14px",
                      cursor: "pointer",
                      fontSize: 13,
                      color: C.text,
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 8,
                      borderBottom: `1px solid ${C.border}`
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = C.surface}
                    onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                  >
                    <div style={{ marginTop: 2 }}>
                      <Ic n="mappin" s={12} c={C.muted} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 12.5 }}>{p.structured_formatting.main_text}</div>
                      <div style={{ fontSize: 11, color: C.muted }}>{p.structured_formatting.secondary_text}</div>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   STOP TIMELINE
───────────────────────────────────────────────────────────── */
function StopTimeline({ stops, color }) {
  const [expanded, setExpanded] = useState(false);
  if (!stops || stops.length === 0) return null;
  const show = !expanded && stops.length > 5 ? [stops[0], null, stops[stops.length - 1]] : stops;
  return (
    <div style={{ paddingLeft: 2 }}>
      {show.map((stop, i) => {
        if (stop === null) return (
          <div key="mid" style={{ display: "flex", gap: 12, alignItems: "center", padding: "4px 0", position: "relative" }}>
            <div style={{ width: 20, display: "flex", justifyContent: "center", position: "relative", alignSelf: "stretch" }}>
              <div style={{ position: "absolute", top: 0, bottom: 0, width: 1.5, background: color + "30" }} />
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: color + "50", zIndex: 2, alignSelf: "center" }} />
            </div>
            <button onClick={() => setExpanded(true)} style={{ background: C.card, border: `1px solid ${color}44`, borderRadius: 6, color, fontSize: 11, fontWeight: 700, padding: "3px 10px", cursor: "pointer", fontFamily: "inherit", zIndex: 2 }}>
              +{stops.length - 2} intermediate stops
            </button>
          </div>
        );
        const isFirst = i === 0;
        const isLast = i === show.length - 1;
        return (
          <div key={`${stop}-${i}`} style={{ display: "flex", gap: 12, position: "relative" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 20, position: "relative", flexShrink: 0 }}>
              <div style={{
                width: isFirst || isLast ? 10 : 6,
                height: isFirst || isLast ? 10 : 6,
                borderRadius: "50%",
                background: isFirst ? C.green : isLast ? C.red : color,
                boxShadow: isFirst || isLast ? `0 0 0 3px ${isFirst ? C.green : C.red}22` : "none",
                zIndex: 2,
                marginTop: 4
              }} />
              {!isLast && <div style={{ position: "absolute", top: 10, bottom: 0, width: 1.5, background: color + "30", zIndex: 1 }} />}
            </div>
            <div style={{ flex: 1, paddingBottom: isLast ? 0 : 8 }}>
              <div style={{ fontSize: isFirst || isLast ? 13 : 11.5, fontWeight: isFirst || isLast ? 700 : 400, color: isFirst || isLast ? C.text : C.muted }}>{stop}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   TRAVEL GUIDE
───────────────────────────────────────────────────────────── */
function TravelGuide({ guide, color, activeSegmentIndex = null, setActiveSegmentIndex = () => { }, segments = null, setMapView = () => { } }) {
  if (!guide || guide.length === 0) return null;

  // Helper to map a guide step to a segment index
  const getSegIdx = (step) => getSegmentIndexForGuideStep(step, guide, segments);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {guide.map((step, i) => {
        const segIdx = getSegIdx(step);
        const isActive = segIdx !== null && activeSegmentIndex === segIdx;

        return (
          <div
            key={i}
            onClick={() => {
              if (segIdx !== null) {
                setActiveSegmentIndex(segIdx);
                setMapView("gmap");
              }
            }}
            style={{
              display: "flex",
              gap: 12,
              cursor: segIdx !== null ? "pointer" : "default",
              padding: "8px 10px",
              borderRadius: 10,
              background: isActive ? `${color}15` : "transparent",
              border: `1.5px solid ${isActive ? `${color}35` : "transparent"}`,
              transition: "all 0.2s"
            }}
            onMouseEnter={e => {
              if (segIdx !== null && !isActive) {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
              }
            }}
            onMouseLeave={e => {
              if (segIdx !== null && !isActive) {
                e.currentTarget.style.background = "transparent";
              }
            }}
          >
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 34 }}>
              <div style={{
                width: 34,
                height: 34,
                borderRadius: 10,
                background: isActive ? `${color}33` : color + "20",
                border: `1.5px solid ${isActive ? color : `${color}44`}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                boxShadow: isActive ? `0 0 10px ${color}33` : "none",
                transition: "all 0.2s"
              }}>
                <Ic n={step.icon || "arrow"} s={15} c={isActive ? "#fff" : color} />
              </div>
              {i < guide.length - 1 && <div style={{ width: 1.5, flex: 1, background: color + "25", minHeight: 18, margin: "4px 0" }} />}
            </div>
            <div style={{ flex: 1, paddingBottom: i < guide.length - 1 ? 14 : 0 }}>
              <div style={{ fontWeight: isActive ? 700 : 600, fontSize: 13, color: isActive ? "#fff" : C.text }}>{step.text}</div>
              <div style={{ display: "flex", gap: 10, marginTop: 2, flexWrap: "wrap", alignItems: "center" }}>
                {step.duration && <span style={{ fontSize: 11, color: C.muted }}>{step.duration}</span>}
                {step.detail && <span style={{ fontSize: 11, color }}>{step.detail}</span>}
                {step.nav_url && (
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      if (segIdx !== null) {
                        setActiveSegmentIndex(segIdx);
                        setMapView("gmap");
                      }
                    }}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      background: isActive ? color : C.accent + "18",
                      color: isActive ? "#fff" : C.accent,
                      border: `1px solid ${isActive ? color : `${C.accent}44`}`,
                      borderRadius: 6,
                      padding: "2px 8px",
                      fontSize: 10,
                      fontWeight: 700,
                      cursor: "pointer",
                      transition: "all 0.15s",
                      fontFamily: "inherit"
                    }}
                    onMouseEnter={e => {
                      if (!isActive) {
                        e.currentTarget.style.background = C.accent;
                        e.currentTarget.style.color = "#fff";
                      }
                    }}
                    onMouseLeave={e => {
                      if (!isActive) {
                        e.currentTarget.style.background = C.accent + "18";
                        e.currentTarget.style.color = C.accent;
                      }
                    }}
                  >
                    <Ic n="gps" s={10} /> {isActive ? "Navigating..." : "Navigate"}
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   SEE ALL BUSES PANEL
───────────────────────────────────────────────────────────── */
function isVajraBus(routeName) {
  // Match routes with AC, V- prefix, VAJRA or VOLVO anywhere in name
  const r = (routeName || "").toUpperCase();
  return r.includes("AC") || r.startsWith("V-") || r.includes("VAJRA") || r.includes("VOLVO");
}

function AllBusesPanel({ src, dst, time, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all | direct | transfer | vajra
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    setLoading(true);
    setData(null);
    apiAllBuses(src.toLowerCase(), dst.toLowerCase(), time)
      .then(setData).catch(() => setData({ direct: [], transfer: [] }))
      .finally(() => setLoading(false));
  }, [src, dst, time]);

  const toggleExpand = (id) => setExpandedId(expandedId === id ? null : id);

  const direct = data?.direct || [];
  const transfer = data?.transfer || [];

  const directVajraAvailable = direct.some(b => isVajraBus(b.route));
  const transferVajraAvailable = transfer.some(opt => opt.buses?.some(isVajraBus) || opt.segment_details?.some(s => isVajraBus(s.route)));

  const filteredDirect = filter === "vajra"
    ? direct.filter(b => isVajraBus(b.route))
    : (filter === "direct" || filter === "all") ? direct : [];
  const filteredXfer = filter === "vajra"
    ? transfer.filter(opt => opt.buses?.some(isVajraBus) || opt.segment_details?.some(s => isVajraBus(s.route)))
    : (filter === "transfer" || filter === "all") ? transfer : [];

  // Build quick bus number summary
  const allBusNums = [
    ...direct.map(b => b.route),
    ...transfer.flatMap(opt => opt.buses || []),
  ];
  const uniqueBusNums = [...new Set(allBusNums)].slice(0, 18);

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20, marginTop: 16 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 14 }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15, color: C.text }}>All BMTC Buses</div>
          <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{src} → {dst}</div>
        </div>
        <button onClick={onClose} style={{
          background: "none", border: `1px solid ${C.border2}`, borderRadius: 8,
          padding: "5px 12px", color: C.muted, cursor: "pointer", fontFamily: "inherit",
          fontSize: 12, flexShrink: 0, marginLeft: 12,
        }}>✕ Close</button>
      </div>

      {/* Quick bus numbers summary */}
      {!loading && uniqueBusNums.length > 0 && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10,
          padding: "10px 12px", marginBottom: 14,
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: "0.06em", marginBottom: 8 }}>POSSIBLE BUS NUMBERS</div>
          <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
            {uniqueBusNums.map(rn => (
              <span key={rn} style={{
                background: isVajraBus(rn) ? C.accent + "22" : MC.bmtc.color + "18",
                color: isVajraBus(rn) ? C.accent : MC.bmtc.color,
                border: `1px solid ${isVajraBus(rn) ? C.accent : MC.bmtc.color}44`,
                borderRadius: 6, padding: "3px 8px", fontSize: 11, fontWeight: 700,
              }}>{rn}</span>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs — Segmented control style */}
      <div style={{
        display: "flex", background: C.surface, borderRadius: 12,
        padding: 4, gap: 4, marginBottom: 14, border: `1px solid ${C.border2}`,
      }}>
        {[
          { k: "all", l: `All (${direct.length + transfer.length})` },
          { k: "direct", l: `Direct (${direct.length})` },
          { k: "transfer", l: `Transfer (${transfer.length})` },
          { k: "vajra", l: "Vajra / AC" },
        ].map(f => (
          <button key={f.k}
            onClick={() => { setFilter(f.k); setExpandedId(null); }}
            style={{
              flex: 1,
              background: filter === f.k ? C.card : "transparent",
              border: "none",
              boxShadow: filter === f.k ? "0 2px 8px #00000030" : "none",
              borderRadius: 8, padding: "8px 4px", fontSize: 11, fontWeight: 700,
              color: filter === f.k ? MC.bmtc.color : C.muted,
              cursor: "pointer", fontFamily: "inherit", whiteSpace: "nowrap",
              transition: "all 0.15s",
            }}>{f.l}</button>
        ))}
      </div>

      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "20px 0", color: C.muted }}>
          <div style={{ width: 16, height: 16, borderRadius: "50%", border: `2px solid ${MC.bmtc.color}`, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
          Finding all buses…
        </div>
      )}

      {/* Vajra availability notice */}
      {!loading && filter === "vajra" && (
        <div style={{ marginBottom: 12 }}>
          {!directVajraAvailable && (
            <div style={{
              background: C.red + "18", border: `1px solid ${C.red}33`, borderRadius: 10,
              padding: "9px 12px", color: C.red, fontSize: 12, display: "flex",
              alignItems: "center", gap: 8, marginBottom: transferVajraAvailable ? 8 : 0,
            }}>
              <Ic n="alert" s={13} c={C.red} />
              <span>No direct Vajra / AC bus for this route.</span>
            </div>
          )}
          {transferVajraAvailable && !directVajraAvailable && (
            <div style={{
              background: C.accent + "11", border: `1px solid ${C.accent}33`, borderRadius: 10,
              padding: "9px 12px", color: C.accent, fontSize: 12, display: "flex",
              alignItems: "center", gap: 8,
            }}>
              <Ic n="info" s={13} c={C.accent} />
              <span>Vajra / AC available on partial segments (see transfer options below).</span>
            </div>
          )}
        </div>
      )}

      {/* DIRECT BUSES */}
      {!loading && filteredDirect.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, letterSpacing: "0.05em", marginBottom: 8 }}>DIRECT BUSES</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {filteredDirect.map((b, i) => {
              const expId = `d-${i}`;
              const isExp = expandedId === expId;
              const hasToll = b.has_toll || b.toll > 0;
              const isVajra = isVajraBus(b.route);
              return (
                <div key={i} style={{
                  background: C.surface, borderRadius: 10,
                  border: `1px solid ${isExp ? MC.bmtc.color + "66" : C.border}`,
                  overflow: "hidden", transition: "border-color 0.15s",
                }}>
                  {/* Summary row */}
                  <button onClick={() => toggleExpand(expId)} style={{
                    display: "flex", alignItems: "center", gap: 10, background: "none",
                    border: "none", padding: "11px 14px", width: "100%",
                    cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                  }}>
                    <Pill color={isVajra ? C.accent : MC.bmtc.color}>{b.route}</Pill>
                    <div style={{ flex: 1, fontSize: 12, color: C.muted }}>{b.stop_count} stops</div>
                    <div style={{ fontSize: 11, color: MC.bmtc.color, fontWeight: 700, marginRight: 4 }}>{b.trips}/day</div>
                    {b.fare !== undefined && <div style={{ fontSize: 13, color: C.text, fontWeight: 700 }}>₹{b.fare}</div>}
                    {b.departure && (
                      <div style={{ fontSize: 11, color: C.muted, marginLeft: 6, display: "flex", alignItems: "center", gap: 4 }}>
                        <span>{b.departure}</span>
                        {b.waiting_time !== undefined && b.waiting_time !== null && (
                          <span style={{ background: C.yellow + "22", color: C.yellow, border: `1px solid ${C.yellow}33`, borderRadius: 4, padding: "1px 4px", fontSize: 9, fontWeight: 700 }}>
                            {b.waiting_time}m wait
                          </span>
                        )}
                      </div>
                    )}
                    <div style={{
                      transform: isExp ? "rotate(180deg)" : "none",
                      transition: "transform 0.2s", color: C.muted, marginLeft: 6, flexShrink: 0,
                    }}><Ic n="chevron" s={14} /></div>
                  </button>

                  {/* Expanded detail */}
                  {isExp && (
                    <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
                      {/* Timing row */}
                      <div style={{
                        display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8,
                        background: C.card, borderRadius: 8, padding: "10px 12px", marginBottom: 10,
                      }}>
                        {[
                          ["Duration", b.duration || b.total_time ? `${b.duration || b.total_time} min` : "--"],
                          ["Distance", b.distance !== undefined && b.distance !== null ? `${b.distance} km` : "--"],
                          ["Departure", b.departure || "--"],
                          ["Arrival", b.arrival || "--"],
                        ].map(([lbl, val]) => (
                          <div key={lbl}>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 2 }}>{lbl}</div>
                            <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{val}</div>
                          </div>
                        ))}
                      </div>

                      {/* Fare breakdown */}
                      <div style={{
                        background: C.card, borderRadius: 8, padding: "8px 12px", fontSize: 12, marginBottom: 10,
                      }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                          <span style={{ color: C.muted }}>Base Ticket ({b.fare_category || (isVajra ? "Vajra/AC" : "Ordinary")})</span>
                          <span style={{ color: C.text }}>₹{b.base_fare ?? b.fare}</span>
                        </div>
                        {hasToll && (
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                            <span style={{ color: C.yellow }}>Toll (NICE/ELC)</span>
                            <span style={{ color: C.yellow }}>+₹{b.toll}</span>
                          </div>
                        )}
                        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800, paddingTop: 5, borderTop: `1px dashed ${C.border}`, color: MC.bmtc.color }}>
                          <span>Total</span><span>₹{b.fare}</span>
                        </div>
                      </div>

                      {/* Alternative bus numbers */}
                      {b.other_buses?.length > 0 && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: 10, color: C.muted, fontWeight: 700, marginBottom: 5, letterSpacing: "0.04em" }}>ALSO RUNS THIS ROUTE</div>
                          <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                            {b.other_buses.map(ob => (
                              <span key={ob} style={{
                                background: C.dim, color: C.text,
                                padding: "2px 7px", borderRadius: 5, fontSize: 10, fontWeight: 600,
                              }}>{ob}</span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Stop timeline */}
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: "0.05em", marginBottom: 6 }}>STOPS</div>
                        <StopTimeline stops={b.stops || []} color={isVajra ? C.accent : MC.bmtc.color} />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* WITH TRANSFERS */}
      {!loading && filteredXfer.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, letterSpacing: "0.05em", marginBottom: 8 }}>WITH TRANSFERS</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {filteredXfer.map((opt, i) => {
              const expId = `t-${i}`;
              const isExp = expandedId === expId;
              const vajraLegs = (opt.segment_details || []).filter(s => isVajraBus(s.route));
              const containsVajra = vajraLegs.length > 0;

              return (
                <div key={i} style={{
                  background: C.surface, borderRadius: 10,
                  border: `1px solid ${isExp ? MC.bmtc.color + "66" : C.border}`,
                  overflow: "hidden", transition: "border-color 0.15s",
                }}>
                  {/* Summary row */}
                  <button onClick={() => toggleExpand(expId)} style={{
                    display: "flex", flexDirection: "column", background: "none", border: "none",
                    padding: "11px 14px", width: "100%", cursor: "pointer",
                    textAlign: "left", fontFamily: "inherit",
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 5, flexWrap: "wrap", width: "100%" }}>
                      {opt.buses.map((b, j) => (
                        <span key={j} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                          <Pill color={isVajraBus(b) ? C.accent : MC.bmtc.color} small>{b}</Pill>
                          {j < opt.buses.length - 1 && <span style={{ color: C.muted, fontSize: 11, fontWeight: 700 }}>→</span>}
                        </span>
                      ))}
                      {containsVajra && (
                        <span style={{
                          fontSize: 9, background: C.accent + "22", color: C.accent,
                          border: `1px solid ${C.accent}44`, borderRadius: 4,
                          padding: "1px 5px", fontWeight: 800,
                        }}>VAJRA</span>
                      )}
                      <div style={{
                        marginLeft: "auto", transform: isExp ? "rotate(180deg)" : "none",
                        transition: "transform 0.2s", color: C.muted, flexShrink: 0,
                      }}><Ic n="chevron" s={14} /></div>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginTop: 5, fontSize: 11, color: C.muted, alignItems: "center" }}>
                      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        {opt.transfers} transfer{opt.transfers !== 1 ? "s" : ""} · {opt.total_time} min · {opt.distance} km
                        {opt.waiting_time !== undefined && opt.waiting_time !== null && (
                          <span style={{ background: C.yellow + "22", color: C.yellow, border: `1px solid ${C.yellow}33`, borderRadius: 4, padding: "1px 4px", fontSize: 9, fontWeight: 700 }}>
                            {opt.waiting_time}m wait
                          </span>
                        )}
                      </span>
                      <strong style={{ color: C.text, fontSize: 12 }}>₹{opt.total_fare}</strong>
                    </div>
                  </button>

                  {/* Expanded legs */}
                  {isExp && (
                    <div style={{ borderTop: `1px solid ${C.border}`, padding: "12px 14px" }}>
                      {containsVajra && (
                        <div style={{
                          background: C.accent + "11", borderLeft: `3px solid ${C.accent}`,
                          padding: "8px 10px", borderRadius: 4, marginBottom: 10,
                        }}>
                          {vajraLegs.map((seg, idx) => (
                            <div key={idx} style={{ fontSize: 11, color: C.accent, fontWeight: 600 }}>
                              ✨ Vajra: {seg.from} → {seg.to} ({seg.route})
                            </div>
                          ))}
                        </div>
                      )}

                      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                        {(opt.segment_details || []).map((seg, idx) => {
                          const hasToll = seg.has_toll || seg.toll > 0;
                          const isSegVajra = isVajraBus(seg.route);
                          return (
                            <div key={idx} style={{
                              background: C.card, borderRadius: 8,
                              border: `1px solid ${isSegVajra ? C.accent + "44" : C.border}`,
                              padding: 10,
                            }}>
                              {/* Leg header */}
                              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                  <span style={{
                                    fontSize: 10, background: C.dim, color: C.muted,
                                    borderRadius: 4, padding: "2px 6px", fontWeight: 700,
                                  }}>LEG {idx + 1}</span>
                                  <Pill color={isSegVajra ? C.accent : MC.bmtc.color} small>{seg.route}</Pill>
                                </div>
                                <span style={{ fontSize: 13, color: C.text, fontWeight: 700 }}>₹{seg.fare}</span>
                              </div>

                              {/* Board / Alight / Time */}
                              <div style={{
                                display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4,
                                fontSize: 11, marginBottom: 8,
                              }}>
                                <div><span style={{ color: C.muted }}>Board</span><br /><strong style={{ color: C.text }}>{seg.from}</strong></div>
                                <div><span style={{ color: C.muted }}>Alight</span><br /><strong style={{ color: C.text }}>{seg.to}</strong></div>
                                <div><span style={{ color: C.muted }}>Duration</span><br /><strong style={{ color: C.text }}>{seg.duration} min</strong></div>
                                <div><span style={{ color: C.muted }}>Time</span><br /><strong style={{ color: C.text }}>{seg.departure} – {seg.arrival}</strong></div>
                              </div>

                              {/* Fare */}
                              <div style={{
                                background: C.surface, borderRadius: 5, padding: "5px 8px",
                                fontSize: 11, marginBottom: 8,
                              }}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}>
                                  <span style={{ color: C.muted }}>{seg.fare_category || (isSegVajra ? "Vajra" : "Ordinary")}</span>
                                  <span style={{ color: C.text }}>₹{seg.base_fare ?? seg.fare}</span>
                                </div>
                                {hasToll && (
                                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 2 }}>
                                    <span style={{ color: C.yellow }}>Toll</span>
                                    <span style={{ color: C.yellow }}>+₹{seg.toll}</span>
                                  </div>
                                )}
                              </div>

                              {/* Other buses */}
                              {seg.other_buses?.length > 0 && (
                                <div style={{ marginBottom: 8 }}>
                                  <div style={{ fontSize: 10, color: C.muted, fontWeight: 700, marginBottom: 4, letterSpacing: "0.04em" }}>ALTERNATIVE BUSES</div>
                                  <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                                    {seg.other_buses.map(ob => (
                                      <span key={ob} style={{
                                        background: C.dim, color: C.text,
                                        padding: "1px 5px", borderRadius: 4, fontSize: 9, fontWeight: 600,
                                      }}>{ob}</span>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Stops */}
                              <div style={{ borderTop: `1px solid ${C.border}`, paddingTop: 6 }}>
                                <StopTimeline stops={seg.stops || []} color={isSegVajra ? C.accent : MC.bmtc.color} />
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && filteredDirect.length === 0 && filteredXfer.length === 0 && (
        <div style={{ textAlign: "center", padding: "30px 0", color: C.muted, fontSize: 13 }}>
          {filter === "vajra" ? "No Vajra / AC buses found for this route." : "No buses found."}
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   ROUTE SEARCH PANEL  (with autocomplete)
───────────────────────────────────────────────────────────── */
function RouteSearchPanel() {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop] = useState(false);
  const [result, setResult] = useState(null);
  const [direction, setDirection] = useState("forward"); // forward | return
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);

  // Debounced autocomplete
  const fetchSuggestions = useCallback((q) => {
    clearTimeout(debounceRef.current);
    if (!q.trim()) { setSuggestions([]); return; }
    debounceRef.current = setTimeout(async () => {
      const list = await apiRouteSuggestions(q);
      setSuggestions(list);
    }, 200);
  }, []);

  const handleQueryChange = (val) => {
    setQuery(val);
    setShowDrop(true);
    fetchSuggestions(val);
  };

  const selectSuggestion = (r) => {
    setQuery(r);
    setSuggestions([]);
    setShowDrop(false);
    doSearch(r);
  };

  const doSearch = async (q) => {
    const term = (q || query).trim();
    if (!term) return;
    setLoading(true); setError(null); setResult(null); setShowDrop(false);
    setDirection("forward");
    try {
      const d = await apiRouteSearch(term);
      setResult(d);
    } catch { setError("Route not found. Try e.g. 360-K, V-360B, KBS-3E"); }
    finally { setLoading(false); }
  };

  const visibleSuggestions = showDrop && suggestions.length > 0
    ? suggestions.filter(s => s.toUpperCase() !== query.toUpperCase()).slice(0, 10)
    : [];

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20 }}>
      <div style={{ fontWeight: 800, fontSize: 15, color: C.text, marginBottom: 14 }}>Route Lookup</div>

      {/* Search input with dropdown */}
      <div style={{ position: "relative", marginBottom: 14 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <input
            value={query}
            onChange={e => handleQueryChange(e.target.value)}
            onFocus={() => { setShowDrop(true); if (query) fetchSuggestions(query); }}
            onBlur={() => setTimeout(() => setShowDrop(false), 160)}
            onKeyDown={e => { if (e.key === "Enter") doSearch(); if (e.key === "Escape") setShowDrop(false); }}
            placeholder="Type route number, e.g. 360-K, V-360B, KBS-3E…"
            style={{
              flex: 1, background: C.surface, border: `1.5px solid ${C.border2}`,
              borderRadius: 10, color: C.text, padding: "11px 14px",
              fontSize: 13, outline: "none", fontFamily: "inherit",
            }}
          />
          <button
            onClick={() => doSearch()}
            disabled={loading}
            style={{
              background: MC.bmtc.color, border: "none", borderRadius: 10,
              padding: "11px 18px", color: "white", fontWeight: 700,
              cursor: loading ? "wait" : "pointer", fontFamily: "inherit",
              fontSize: 13, display: "flex", alignItems: "center", gap: 6, flexShrink: 0,
            }}>
            {loading
              ? <div style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid white", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
              : <Ic n="search" s={14} c="white" />
            }
            Search
          </button>
          {(result || error) && (
            <button
              onClick={() => { setResult(null); setError(null); setQuery(""); setSuggestions([]); }}
              style={{
                background: "none", border: `1px solid ${C.border2}`, borderRadius: 10,
                padding: "11px 13px", color: C.muted, cursor: "pointer", fontFamily: "inherit", flexShrink: 0,
              }}>✕</button>
          )}
        </div>

        {/* Dropdown suggestions */}
        {visibleSuggestions.length > 0 && (
          <div style={{
            position: "absolute", top: "calc(100% + 4px)", left: 0,
            right: 0, background: C.card, border: `1px solid ${C.border2}`,
            borderRadius: 10, zIndex: 300, boxShadow: "0 16px 48px #00000099",
            maxHeight: 260, overflowY: "auto",
          }}>
            {visibleSuggestions.map(r => (
              <div
                key={r}
                onMouseDown={() => selectSuggestion(r)}
                style={{
                  padding: "10px 14px", cursor: "pointer", fontSize: 13,
                  color: C.text, borderBottom: `1px solid ${C.border}`,
                  display: "flex", alignItems: "center", gap: 10,
                }}
                onMouseEnter={e => e.currentTarget.style.background = C.surface}
                onMouseLeave={e => e.currentTarget.style.background = "transparent"}
              >
                <Pill color={isVajraBus(r) ? C.accent : MC.bmtc.color} small>{r}</Pill>
                {isVajraBus(r) && <span style={{ fontSize: 10, color: C.accent, fontWeight: 700 }}>VAJRA/AC</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div style={{
          color: C.red, fontSize: 12, background: C.red + "18",
          border: `1px solid ${C.red}33`, borderRadius: 8, padding: "8px 12px",
        }}>{error}</div>
      )}

      {result && (
        <div>
          {/* Route header */}
          <div style={{
            background: C.surface, borderRadius: 10, padding: "12px 14px",
            marginBottom: 12, display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap",
          }}>
            <Pill color={isVajraBus(result.route) ? C.accent : MC.bmtc.color}>{result.route}</Pill>
            <span style={{ fontSize: 12, color: C.muted }}>
              {direction === "forward" ? result.stop_count : (result.reverse_stops?.length || 0)} stops
            </span>
            {result.trips > 0 && (
              <span style={{ fontSize: 12, color: MC.bmtc.color, fontWeight: 700 }}>{result.trips} trips/day</span>
            )}
            {result.schedule?.departure && (
              <span style={{ fontSize: 12, color: C.muted }}>
                🕐 {result.schedule.departure} → {result.schedule.arrival}
              </span>
            )}
          </div>

          {/* Direction toggle if return stops are available */}
          {result.reverse_stops && result.reverse_stops.length > 0 && (
            <div style={{
              display: "flex", background: C.surface, borderRadius: 12,
              padding: 4, gap: 4, marginBottom: 12, border: `1px solid ${C.border2}`,
            }}>
              {[
                { k: "forward", l: "Outbound / Forward" },
                { k: "return", l: "Inbound / Return" },
              ].map(d => (
                <button key={d.k}
                  onClick={() => setDirection(d.k)}
                  style={{
                    flex: 1,
                    background: direction === d.k ? C.card : "transparent",
                    border: "none",
                    boxShadow: direction === d.k ? "0 2px 8px #00000030" : "none",
                    borderRadius: 8, padding: "8px 4px", fontSize: 11, fontWeight: 700,
                    color: direction === d.k ? MC.bmtc.color : C.muted,
                    cursor: "pointer", fontFamily: "inherit",
                    transition: "all 0.15s",
                  }}>{d.l}</button>
              ))}
            </div>
          )}

          {/* Stops */}
          <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: "0.05em", marginBottom: 8 }}>
            ALL STOPS ({direction === "forward" ? "OUTBOUND" : "INBOUND"})
          </div>
          <div style={{ maxHeight: 320, overflowY: "auto", paddingRight: 4 }}>
            <StopTimeline
              stops={direction === "forward" ? (result.stops || []) : (result.reverse_stops || [])}
              color={isVajraBus(result.route) ? C.accent : MC.bmtc.color}
            />
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   TIMETABLE PANEL
   Shows Namma Metro & GTFS Bus scheduled departures/timings
───────────────────────────────────────────────────────────── */
function TimetablePanel({ results, onClose, stops, src, dst, time }) {
  const [metroData, setMetroData] = useState([]);

  const [srcQuery, setSrcQuery] = useState(src || "");
  const [dstQuery, setDstQuery] = useState(dst || "");
  const [srcSuggestions, setSrcSuggestions] = useState([]);
  const [dstSuggestions, setDstSuggestions] = useState([]);
  const [srcDrop, setSrcDrop] = useState(false);
  const [dstDrop, setDstDrop] = useState(false);

  // Metro timing results
  const [metroResult, setMetroResult] = useState(null);
  const [metroLoading, setMetroLoading] = useState(false);
  const [metroError, setMetroError] = useState(null);

  // BMTC timing results
  const [connectingBuses, setConnectingBuses] = useState([]);
  const [busLoading, setBusLoading] = useState(false);
  const [busError, setBusError] = useState(null);

  // Selected bus timetable (clicked tag)
  const [selectedBusRoute, setSelectedBusRoute] = useState("");
  const [busResult, setBusResult] = useState(null);
  const [busResultLoading, setBusResultLoading] = useState(false);
  const [busResultError, setBusResultError] = useState(null);

  // Standalone Check Route Timings state
  const [checkQuery, setCheckQuery] = useState("");
  const [checkSuggestions, setCheckSuggestions] = useState([]);
  const [checkDrop, setCheckDrop] = useState(false);
  const [checkResult, setCheckResult] = useState(null);
  const [checkResultLoading, setCheckResultLoading] = useState(false);
  const [checkResultError, setCheckResultError] = useState(null);

  const debounceRef = useRef(null);

  useEffect(() => {
    const fetchGeneralMetro = async () => {
      try {
        const d = await apiMetroTimetable();
        setMetroData(d.metro || []);
      } catch { }
    };
    fetchGeneralMetro();
  }, []);

  const fetchTimetable = async (sourceVal, destVal) => {
    if (!sourceVal || !destVal) return;

    // Clear previous results
    setMetroResult(null);
    setConnectingBuses([]);
    setSelectedBusRoute("");
    setBusResult(null);

    // 1. Fetch metro timings
    setMetroLoading(true); setMetroError(null);
    try {
      const d = await apiMetroTimetable(sourceVal, time || "");
      setMetroResult(d);
    } catch {
      setMetroError("Failed to fetch metro timings.");
    } finally {
      setMetroLoading(false);
    }

    // 2. Fetch direct connecting buses
    setBusLoading(true); setBusError(null);
    try {
      const res = await fetch(`${API_BASE}/api/bmtc/all-buses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: sourceVal, destination: destVal, time: time || null })
      });
      if (res.ok) {
        const d = await res.json();
        const routes = new Set();
        if (d.direct) {
          d.direct.forEach(b => {
            if (b.route) routes.add(b.route);
          });
        }
        setConnectingBuses(Array.from(routes));
      } else {
        setBusError("Failed to find connecting buses.");
      }
    } catch {
      setBusError("Failed to fetch connecting buses.");
    } finally {
      setBusLoading(false);
    }
  };

  // Auto-fetch if source and destination are pre-populated
  useEffect(() => {
    if (src && dst) {
      setSrcQuery(src);
      setDstQuery(dst);
      fetchTimetable(src, dst);
    }
  }, [src, dst]);

  const selectConnectingBus = async (r) => {
    setSelectedBusRoute(r);
    setBusResult(null);
    setBusResultError(null);
    setBusResultLoading(true);
    try {
      const d = await apiRouteTimetable(r);
      setBusResult(d);
    } catch {
      setBusResultError("Departures schedule not found.");
    } finally {
      setBusResultLoading(false);
    }
  };

  // Autocomplete suggestions for source/destination
  const handleSrcChange = (val) => {
    setSrcQuery(val);
    setSrcDrop(true);
    if (!val.trim()) { setSrcSuggestions([]); return; }
    const q = val.toLowerCase();
    const matches = (stops?.all || []).filter(s => s.toLowerCase().includes(q)).slice(0, 10);
    setSrcSuggestions(matches);
  };

  const handleDstChange = (val) => {
    setDstQuery(val);
    setDstDrop(true);
    if (!val.trim()) { setDstSuggestions([]); return; }
    const q = val.toLowerCase();
    const matches = (stops?.all || []).filter(s => s.toLowerCase().includes(q)).slice(0, 10);
    setDstSuggestions(matches);
  };

  // Check Route Timings autocomplete
  const fetchCheckSuggestions = useCallback((q) => {
    clearTimeout(debounceRef.current);
    if (!q.trim()) { setCheckSuggestions([]); return; }
    debounceRef.current = setTimeout(async () => {
      const list = await apiRouteSuggestions(q);
      setCheckSuggestions(list);
    }, 200);
  }, []);

  const handleCheckChange = (val) => {
    setCheckQuery(val);
    setCheckDrop(true);
    fetchCheckSuggestions(val);
  };

  const runCheckSearch = async (r) => {
    const routeName = (r || checkQuery).trim();
    if (!routeName) return;
    setCheckDrop(false);
    setCheckResultLoading(true);
    setCheckResultError(null);
    setCheckResult(null);
    try {
      const d = await apiRouteTimetable(routeName);
      setCheckResult(d);
    } catch {
      setCheckResultError("Bus route not found.");
    } finally {
      setCheckResultLoading(false);
    }
  };

  return (
    <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 22, position: "relative", marginBottom: 16 }}>
      <button onClick={onClose} style={{ position: "absolute", top: 16, right: 16, background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 16 }}>✕</button>
      <div style={{ fontWeight: 800, fontSize: 18, color: C.text, display: "flex", alignItems: "center", gap: 8, marginBottom: 18 }}>
        <Ic n="clock" s={18} c={C.accent} /> Transit Timetable
      </div>

      {/* INPUT FORM */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div style={{ flex: 1, minWidth: 200, position: "relative" }}>
          <label style={{ display: "block", fontSize: 10, fontWeight: 700, color: C.muted, textTransform: "uppercase", marginBottom: 6 }}>Source Stop / Coordinates</label>
          <input
            value={srcQuery}
            onChange={e => handleSrcChange(e.target.value)}
            onFocus={() => { setSrcDrop(true); handleSrcChange(srcQuery); }}
            onBlur={() => setTimeout(() => setSrcDrop(false), 160)}
            placeholder="Type coordinates or stop name…"
            style={{ width: "100%", background: C.surface, border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
          />
          {srcDrop && srcSuggestions.length > 0 && (
            <div style={{ position: "absolute", top: "105%", left: 0, right: 0, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, zIndex: 12, maxHeight: 180, overflowY: "auto", boxShadow: "0 8px 24px #00000050" }}>
              {srcSuggestions.map(s => (
                <div key={s} onMouseDown={() => { setSrcQuery(s); setSrcDrop(false); }} style={{ padding: "8px 12px", fontSize: 12, cursor: "pointer", color: C.text, borderBottom: `1px solid ${C.border2}` }} onMouseEnter={e => e.target.style.background = C.surface} onMouseLeave={e => e.target.style.background = "transparent"}>{s}</div>
              ))}
            </div>
          )}
        </div>

        <div style={{ flex: 1, minWidth: 200, position: "relative" }}>
          <label style={{ display: "block", fontSize: 10, fontWeight: 700, color: C.muted, textTransform: "uppercase", marginBottom: 6 }}>Destination Stop / Coordinates</label>
          <input
            value={dstQuery}
            onChange={e => handleDstChange(e.target.value)}
            onFocus={() => { setDstDrop(true); handleDstChange(dstQuery); }}
            onBlur={() => setTimeout(() => setDstDrop(false), 160)}
            placeholder="Type coordinates or stop name…"
            style={{ width: "100%", background: C.surface, border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
          />
          {dstDrop && dstSuggestions.length > 0 && (
            <div style={{ position: "absolute", top: "105%", left: 0, right: 0, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, zIndex: 12, maxHeight: 180, overflowY: "auto", boxShadow: "0 8px 24px #00000050" }}>
              {dstSuggestions.map(s => (
                <div key={s} onMouseDown={() => { setDstQuery(s); setDstDrop(false); }} style={{ padding: "8px 12px", fontSize: 12, cursor: "pointer", color: C.text, borderBottom: `1px solid ${C.border2}` }} onMouseEnter={e => e.target.style.background = C.surface} onMouseLeave={e => e.target.style.background = "transparent"}>{s}</div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => fetchTimetable(srcQuery, dstQuery)}
          disabled={metroLoading || busLoading || !srcQuery.trim() || !dstQuery.trim()}
          style={{ background: C.accent, border: "none", borderRadius: 10, padding: "11px 20px", color: "white", fontWeight: 700, cursor: "pointer", fontFamily: "inherit", fontSize: 13, display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
          <Ic n="search" s={14} c="white" /> Search Timetable
        </button>
      </div>

      {/* SCHEDULES LAYOUT */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        {/* METRO TIMINGS */}
        <div style={{ borderRight: `1px solid ${C.border2}`, paddingRight: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 13, color: C.muted, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 12 }}>
            🚇 Metro Timetable
          </div>
          {metroLoading && <div style={{ fontSize: 12, color: C.muted, padding: 10 }}>Resolving nearest station and timings…</div>}
          {metroError && <div style={{ fontSize: 12, color: C.red, padding: 10 }}>{metroError}</div>}

          {metroResult && metroResult.resolved_station ? (
            <div style={{ background: C.surface, borderRadius: 12, border: `1.5px solid ${metroResult.color}50`, padding: 14, boxShadow: `0 4px 20px ${metroResult.color}15` }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: metroResult.color }} />
                  <span style={{ fontWeight: 800, fontSize: 14, color: C.text }}>{metroResult.resolved_station}</span>
                </div>
                <span style={{ fontSize: 10, color: metroResult.color, fontWeight: 700, background: metroResult.color + "18", padding: "2px 8px", borderRadius: 6 }}>
                  {metroResult.line}
                </span>
              </div>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 10 }}>
                Frequency: <strong>{metroResult.frequency}</strong> {metroResult.is_peak ? "(Peak Hours ⚡)" : "(Normal)"}
              </div>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.text, marginBottom: 6 }}>Upcoming Departures:</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {metroResult.departures && metroResult.departures.length > 0 ? (
                  metroResult.departures.map((t, idx) => (
                    <span key={idx} style={{ background: metroResult.color + "12", border: `1px solid ${metroResult.color}40`, borderRadius: 8, padding: "5px 8px", fontSize: 11, fontWeight: 700, color: C.text, display: "flex", alignItems: "center", gap: 4 }}>
                      🚇 {t} <span style={{ fontSize: 8, color: C.green }}>🟢</span>
                    </span>
                  ))
                ) : (
                  <span style={{ fontSize: 11, color: C.muted }}>No upcoming trains. Operational hours: 05:00 – 23:00.</span>
                )}
              </div>
            </div>
          ) : (
            <div>
              {/* Fallback general metro lines */}
              <div style={{ fontSize: 11, color: C.muted, fontStyle: "italic", marginBottom: 10 }}>
                Enter source above to see departures from your nearest station.
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {metroData.map((line, idx) => (
                  <div key={idx} style={{ background: C.surface, borderRadius: 10, border: `1px solid ${C.border2}`, padding: 10 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: line.color }} />
                      <span style={{ fontWeight: 800, fontSize: 12, color: C.text }}>{line.line}</span>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 10, color: C.muted }}>
                      <div>🕒 First/Last: {line.first_train}-{line.last_train}</div>
                      <div>⚡ Freq: {line.peak_frequency} (Peak)</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* BUS TIMINGS */}
        <div>
          <div style={{ fontWeight: 700, fontSize: 13, color: C.muted, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 12 }}>
            🚌 BMTC Connecting Buses
          </div>
          {busLoading && <div style={{ fontSize: 12, color: C.muted, padding: 10 }}>Finding connecting routes…</div>}
          {busError && <div style={{ fontSize: 12, color: C.red, padding: 10 }}>{busError}</div>}

          {connectingBuses.length > 0 ? (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>
                Select a connecting bus route to display departures:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {connectingBuses.map(r => (
                  <button
                    key={r}
                    onClick={() => selectConnectingBus(r)}
                    style={{
                      background: selectedBusRoute === r ? MC.bmtc.color + "22" : C.surface,
                      border: `1px solid ${selectedBusRoute === r ? MC.bmtc.color : C.border2}`,
                      borderRadius: 8, padding: "6px 12px", fontSize: 11, fontWeight: 700,
                      color: selectedBusRoute === r ? MC.bmtc.color : C.text,
                      cursor: "pointer", fontFamily: "inherit"
                    }}>
                    {r}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            !busLoading && (
              <div style={{ fontSize: 11, color: C.muted, fontStyle: "italic", padding: 10 }}>
                No direct buses found between stops.
              </div>
            )
          )}

          {/* Selected Bus Departures result */}
          {busResultLoading && <div style={{ fontSize: 12, color: C.muted, padding: 10 }}>Loading departures…</div>}
          {busResultError && <div style={{ fontSize: 12, color: C.red, padding: 10 }}>{busResultError}</div>}

          {busResult && (
            <div style={{ background: C.surface, border: `1px solid ${C.border2}`, borderRadius: 12, padding: 12 }}>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8, display: "flex", justifyContent: "space-between" }}>
                <span>📍 From: <strong>{busResult.board_stop}</strong></span>
                <span>📅 <strong>{busResult.total_trips} trips/day</strong></span>
              </div>

              {busResult.departures && busResult.departures.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxHeight: 120, overflowY: "auto" }}>
                  {busResult.departures.map((t, idx) => {
                    const now = new Date();
                    const currentMinutes = now.getHours() * 60 + now.getMinutes();
                    const [h, min] = t.split(":").map(Number);
                    const depMinutes = h * 60 + min;
                    const isUpcoming = depMinutes >= currentMinutes;

                    return (
                      <span key={idx} style={{ background: isUpcoming ? MC.bmtc.color + "22" : C.card, border: `1px solid ${isUpcoming ? MC.bmtc.color + "55" : C.border2}`, borderRadius: 8, padding: "5px 8px", fontSize: 10, fontWeight: 700, color: isUpcoming ? MC.bmtc.color : C.muted, display: "flex", alignItems: "center", gap: 4 }}>
                        🕒 {t} {isUpcoming && <span style={{ fontSize: 8, verticalAlign: "middle" }}>🟢</span>}
                      </span>
                    );
                  })}
                </div>
              ) : (
                <div style={{ fontSize: 10, color: C.muted }}>No scheduled GTFS timings available. Operational window is ~05:00 - 23:30.</div>
              )}
            </div>
          )}
        </div>

      </div>

      <hr style={{ border: "none", borderTop: `1px solid ${C.border}`, margin: "18px 0" }} />

      {/* CHECK ROUTE TIMINGS FIELD */}
      <div>
        <div style={{ fontWeight: 700, fontSize: 13, color: C.muted, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 8 }}>
          🔍 Check Route Timings
        </div>
        <div style={{ display: "flex", gap: 8, position: "relative" }}>
          <input
            value={checkQuery}
            onChange={e => handleCheckChange(e.target.value)}
            onFocus={() => { setCheckDrop(true); if (checkQuery) fetchCheckSuggestions(checkQuery); }}
            onBlur={() => setTimeout(() => setCheckDrop(false), 160)}
            onKeyDown={e => { if (e.key === "Enter") runCheckSearch(); }}
            placeholder="Type any bus route number (e.g. 500-A, 600-FD, V-500D)…"
            style={{ flex: 1, background: C.surface, border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
          />
          <button
            onClick={() => runCheckSearch()}
            disabled={checkResultLoading}
            style={{ background: MC.bmtc.color, border: "none", borderRadius: 10, padding: "10px 18px", color: "white", fontWeight: 700, cursor: checkResultLoading ? "wait" : "pointer", fontFamily: "inherit", fontSize: 13, display: "flex", alignItems: "center", gap: 4, flexShrink: 0 }}>
            {checkResultLoading
              ? <div style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid white", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
              : <Ic n="search" s={14} c="white" />
            }
            Get Timings
          </button>

          {checkDrop && checkSuggestions.length > 0 && (
            <div style={{ position: "absolute", top: "105%", left: 0, right: 0, background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, zIndex: 12, maxHeight: 180, overflowY: "auto", boxShadow: "0 8px 24px #00000050" }}>
              {checkSuggestions.map(r => (
                <div key={r} onMouseDown={() => { setCheckQuery(r); setCheckDrop(false); runCheckSearch(r); }} style={{ padding: "8px 12px", fontSize: 12, cursor: "pointer", color: C.text, borderBottom: `1px solid ${C.border2}` }} onMouseEnter={e => e.target.style.background = C.surface} onMouseLeave={e => e.target.style.background = "transparent"}><strong>{r}</strong></div>
              ))}
            </div>
          )}
        </div>

        {checkResultError && <div style={{ fontSize: 12, color: C.red, marginTop: 8 }}>{checkResultError}</div>}

        {checkResult && (
          <div style={{ background: C.surface, border: `1px solid ${C.border2}`, borderRadius: 12, padding: 12, marginTop: 10 }}>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 8, display: "flex", justifyContent: "space-between" }}>
              <span>📍 Departures from: <strong>{checkResult.board_stop}</strong></span>
              <span>📅 <strong>{checkResult.total_trips} trips/day</strong></span>
            </div>
            {checkResult.departures && checkResult.departures.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxHeight: 120, overflowY: "auto" }}>
                {checkResult.departures.map((t, idx) => {
                  const now = new Date();
                  const currentMinutes = now.getHours() * 60 + now.getMinutes();
                  const [h, min] = t.split(":").map(Number);
                  const depMinutes = h * 60 + min;
                  const isUpcoming = depMinutes >= currentMinutes;

                  return (
                    <span key={idx} style={{ background: isUpcoming ? MC.bmtc.color + "22" : C.card, border: `1px solid ${isUpcoming ? MC.bmtc.color + "55" : C.border2}`, borderRadius: 8, padding: "5px 8px", fontSize: 10, fontWeight: 700, color: isUpcoming ? MC.bmtc.color : C.muted, display: "flex", alignItems: "center", gap: 4 }}>
                      🕒 {t} {isUpcoming && <span style={{ fontSize: 8, verticalAlign: "middle" }}>🟢</span>}
                    </span>
                  );
                })}
              </div>
            ) : (
              <div style={{ fontSize: 10, color: C.muted }}>No scheduled GTFS timings available for this route. Operational window is ~05:00 - 23:30.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   RESULT CARD
───────────────────────────────────────────────────────────── */
function ResultCard({ modeKey, data, selected, onSelect, selectedCabVehicle, setSelectedCabVehicle, selectedMultimodalOption, setSelectedMultimodalOption }) {
  const [tab, setTab] = useState(null);
  const [cabFilter, setCabFilter] = useState("all");
  const [cabProviderFilter, setCabProviderFilter] = useState("all");
  const m = MC[modeKey];
  const isSelected = selected === modeKey;

  // Compute real duration from segment_times if available
  const realDuration = (() => {
    const times = data?.segment_times || [];
    if (times.length > 0) {
      try {
        const dep = times[0].departure;
        const arr = times[times.length - 1].arrival;
        if (dep && arr) {
          const [dh, dm] = dep.split(":").map(Number);
          const [ah, am] = arr.split(":").map(Number);
          const mins = (ah * 60 + am) - (dh * 60 + dm);
          if (mins > 0) return mins;
        }
      } catch { }
    }
    return data?.time || 0;
  })();

  if (!data?.available) return (
    <div style={{ background: C.card, borderRadius: 16, border: `1px solid ${C.border}`, padding: 20, opacity: 0.5 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: m.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Ic n={m.icon} s={20} c={m.color} />
        </div>
        <div>
          <div style={{ fontWeight: 700, color: C.text }}>{m.label}</div>
          <div style={{ fontSize: 12, color: C.muted }}>{data?.error || "Not available"}</div>
        </div>
      </div>
    </div>
  );

  return (
    <div onClick={() => onSelect(modeKey)} style={{
      background: C.card, borderRadius: 16,
      border: `2px solid ${isSelected ? m.color : data.recommended ? m.color + "55" : C.border}`,
      boxShadow: isSelected ? `0 0 0 4px ${m.color}14, 0 12px 40px ${m.color}14` : "none",
      cursor: "pointer", transition: "all 0.18s", overflow: "hidden", position: "relative",
      display: "flex", flexDirection: "column", justifyContent: "space-between", height: "100%",
      gridColumn: modeKey === "multimodal" ? "1 / -1" : "auto"
    }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {data.tag && (
        <div style={{ position: "absolute", top: 0, right: 0, background: m.color, color: "white", fontSize: 10, fontWeight: 800, padding: "4px 14px 4px 10px", borderBottomLeftRadius: 10 }}>
          {data.tag.toUpperCase()}
        </div>
      )}

      {/* Header */}
      <div style={{ padding: "18px 18px 12px", display: "flex", gap: 12, alignItems: "center" }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: m.bg, border: `1.5px solid ${m.color}44`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Ic n={m.icon} s={22} c={m.color} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, fontSize: 15, color: C.text }}>{m.label}</div>
          <div style={{ fontSize: 11, color: C.muted }}>{m.line}</div>
          {modeKey === "bmtc" && (
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
              {data.all_direct && data.all_direct.length > 0 ? (
                data.all_direct.slice(0, 6).map(rn => (
                  <span key={rn} style={{
                    background: isVajraBus(rn) ? C.accent + "18" : m.color + "12",
                    color: isVajraBus(rn) ? C.accent : m.color,
                    border: `1px solid ${isVajraBus(rn) ? C.accent : m.color}33`,
                    borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 700,
                  }}>{rn}</span>
                ))
              ) : data.segments && data.segments.length > 0 ? (
                data.segments.map((seg, sidx) => (
                  <span key={sidx} style={{ display: "inline-flex", alignItems: "center", gap: 3 }}>
                    <span style={{
                      background: isVajraBus(seg.route) ? C.accent + "18" : m.color + "12",
                      color: isVajraBus(seg.route) ? C.accent : m.color,
                      border: `1px solid ${isVajraBus(seg.route) ? C.accent : m.color}33`,
                      borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 700,
                    }}>{seg.route}</span>
                    {sidx < data.segments.length - 1 && <span style={{ color: C.muted, fontSize: 10, fontWeight: 700 }}>→</span>}
                  </span>
                ))
              ) : null}
            </div>
          )}
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 20, color: m.color }}>
            {modeKey === "cab" && data.cost_max && data.cost_max > data.cost
              ? `₹${data.cost} - ₹${data.cost_max}`
              : `₹${data.cost}`}
          </div>
          <div style={{ fontSize: 11, color: C.muted }}>{realDuration} min</div>
        </div>
      </div>

      {/* Stats strip */}
      <div style={{ margin: "0 14px 14px", background: C.surface, borderRadius: 10, padding: "10px 14px", display: "flex", flexWrap: "wrap" }}>
        {[
          { icon: "clock", val: `${realDuration} min` },
          { icon: "transfer", val: `${data.transfers} transfer${data.transfers !== 1 ? "s" : ""}` },
          { icon: "mappin", val: `${data.distance} km` },
          { icon: "now", val: `${data.departure} → ${data.arrival}${data.waiting_time !== undefined && data.waiting_time !== null ? ` (${data.waiting_time}m wait)` : ""}` },
        ].map((s, i) => (
          <div key={i} style={{ flex: "1 1 50%", display: "flex", alignItems: "center", gap: 5, padding: "3px 0" }}>
            <Ic n={s.icon} s={11} c={C.muted} />
            <span style={{ fontSize: 12, color: C.text }}>{s.val}</span>
          </div>
        ))}
      </div>

      {/* Cab options section - only visible when selected and modeKey is cab */}
      {(() => {
        if (modeKey !== "cab" || !isSelected || !data.all_estimates) return null;

        const getVehicleCategory = (est) => {
          const key = (est.vehicle_key || "").toLowerCase();
          const name = (est.vehicle_name || "").toLowerCase();
          // Special service types — check flags first (highest priority)
          if (est.parcel || est.vtype === "parcel" || key.includes("parcel")) return "parcel";
          if (est.rental || est.vtype === "rental" || key.includes("hourly") || key.includes("rental")) return "rental";
          if (est.pet || est.vtype === "pet") return "pet";
          if (est.book_any || est.vtype === "book_any" || name === "book any") return "book_any";
          // Transport types
          if (key.includes("auto") || name.includes("auto")) return "auto";
          if (est.vtype === "scooty" || key.includes("scooty") || name.includes("scooty")) return "scooty";
          if (est.saver || est.vtype === "saver" || key.includes("saver")) return "saver";
          if (key.includes("bike") || name.includes("bike") || key.includes("moto") || name.includes("moto")) return "bike";
          if (est.vtype === "priority" || key.includes("priority")) return "priority";
          if (est.black || est.vtype === "black") return "black";
          if (
            key.includes("ac_cab") || name.includes("cab (ac)") ||
            key.includes("premier") || name.includes("premier") ||
            key.includes("prime") || name.includes("prime") ||
            key.includes("prime_plus") || name.includes("prime plus") ||
            key.includes("green") || name.includes("green") ||
            key.includes("lux") || name.includes("lux") ||
            key.includes("sedan") || name.includes("sedan") ||
            key.includes("go_ac") || name.includes("go ac") ||
            name.includes("ac cab") || name.includes("ac,")
          ) return "ac_cab";
          if (key.includes("xl") || name.includes("xl") || key.includes("suv") || name.includes("suv")) return "other";
          return "cab";
        };

        const PROVIDER_STYLES = {
          namma_yatri: { bg: "#eab308", text: "#000", label: "Namma Yatri" },
          uber: { bg: "#374151", text: "#fff", label: "Uber" },
          ola: { bg: "#84cc16", text: "#000", label: "Ola" },
          rapido: { bg: "#ea580c", text: "#fff", label: "Rapido" },
        };

        // Special badge config for all vehicle types
        const SPECIAL_BADGES = {
          parcel: { label: "PARCEL", color: "#f59e0b", icon: "📦" },
          rental: { label: "HOURLY", color: "#8b5cf6", icon: "⏱️" },
          priority: { label: "PRIORITY", color: "#06b6d4", icon: "⚡" },
          pet: { label: "PET", color: "#f472b6", icon: "🐾" },
          saver: { label: "SAVER", color: "#22c55e", icon: "💰" },
          black: { label: "BLACK", color: "#a3a3a3", icon: "💎" },
          scooty: { label: "SCOOTY", color: "#fb923c", icon: "🛵" },
          book_any: { label: "BOOK ANY", color: "#eab308", icon: "⚡🚗" },
        };

        const categories = [
          { id: "all", label: "All Types", icon: "🌐" },
          { id: "auto", label: "Auto", icon: "🛺" },
          { id: "book_any", label: "Book Any", icon: "⚡🚗" },
          { id: "cab", label: "Cab", icon: "🚗" },
          { id: "ac_cab", label: "AC Cab", icon: "❄️" },
          { id: "bike", label: "Bike", icon: "🏍️" },
          { id: "scooty", label: "Scooty", icon: "🛵" },
          { id: "priority", label: "Priority", icon: "⚡" },
          { id: "black", label: "Black", icon: "💎" },
          { id: "pet", label: "Pet", icon: "🐾" },
          { id: "saver", label: "Saver", icon: "💰" },
          { id: "rental", label: "Hourly", icon: "⏱️" },
          { id: "parcel", label: "Parcel", icon: "📦" },
          { id: "other", label: "Other", icon: "🚙" },
        ];

        const providerOptions = [
          { id: "all", label: "All Providers", icon: "🌐", color: m.color },
          { id: "namma_yatri", label: "Namma Yatri", icon: "🛺", color: "#eab308" },
          { id: "ola", label: "Ola", icon: "🚗", color: "#84cc16" },
          { id: "uber", label: "Uber", icon: "🚗", color: "#e2e8f0" },
          { id: "rapido", label: "Rapido", icon: "🏍️", color: "#ea580c" },
        ];

        const filteredEsts = data.all_estimates.filter(est => {
          const matchesType = cabFilter === "all" || getVehicleCategory(est) === cabFilter;
          const matchesProvider = cabProviderFilter === "all" || est.provider_key === cabProviderFilter;
          return matchesType && matchesProvider;
        });

        return (
          <div onClick={e => e.stopPropagation()} style={{
            padding: "14px 18px",
            borderTop: `1px solid ${C.border}`,
            background: C.bg + "55",
          }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 10, letterSpacing: "0.05em" }}>
              AVAILABLE VEHICLES & PROVIDERS
            </div>

            {/* Category Filter Pills */}
            <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 6, marginBottom: 8, scrollbarWidth: "none" }}>
              {categories.map(cat => {
                const count = data.all_estimates.filter(est =>
                  (cat.id === "all" || getVehicleCategory(est) === cat.id) &&
                  (cabProviderFilter === "all" || est.provider_key === cabProviderFilter)
                ).length;

                if (count === 0 && cat.id !== "all") return null; // hide empty categories

                const isCatActive = cabFilter === cat.id;
                return (
                  <button
                    key={cat.id}
                    onClick={() => setCabFilter(cat.id)}
                    style={{
                      background: isCatActive ? m.color + "22" : C.surface,
                      border: `1.5px solid ${isCatActive ? m.color : C.border2}`,
                      borderRadius: 20,
                      padding: "6px 12px",
                      color: isCatActive ? m.color : C.muted,
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.15s",
                      fontFamily: "inherit"
                    }}
                  >
                    <span>{cat.icon}</span>
                    <span>{cat.label}</span>
                    <span style={{
                      fontSize: 9,
                      background: isCatActive ? m.color + "44" : C.border2,
                      color: isCatActive ? m.color : C.muted,
                      borderRadius: 10,
                      padding: "1px 5px",
                      marginLeft: 2
                    }}>{count}</span>
                  </button>
                );
              })}
            </div>

            {/* Provider Filter Pills */}
            <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 10, marginBottom: 12, scrollbarWidth: "none" }}>
              {providerOptions.map(prov => {
                const count = data.all_estimates.filter(est =>
                  (prov.id === "all" || est.provider_key === prov.id) &&
                  (cabFilter === "all" || getVehicleCategory(est) === cabFilter)
                ).length;

                if (count === 0 && prov.id !== "all") return null;

                const isProvActive = cabProviderFilter === prov.id;
                const activeColor = prov.color;
                return (
                  <button
                    key={prov.id}
                    onClick={() => setCabProviderFilter(prov.id)}
                    style={{
                      background: isProvActive ? activeColor + "22" : C.surface,
                      border: `1.5px solid ${isProvActive ? activeColor : C.border2}`,
                      borderRadius: 20,
                      padding: "6px 12px",
                      color: isProvActive ? activeColor : C.muted,
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.15s",
                      fontFamily: "inherit"
                    }}
                  >
                    <span>{prov.icon}</span>
                    <span>{prov.label}</span>
                    <span style={{
                      fontSize: 9,
                      background: isProvActive ? activeColor + "44" : C.border2,
                      color: isProvActive ? activeColor : C.muted,
                      borderRadius: 10,
                      padding: "1px 5px",
                      marginLeft: 2
                    }}>{count}</span>
                  </button>
                );
              })}
            </div>

            {/* Vehicle List */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8, maxHeight: 300, overflowY: "auto", paddingRight: 4 }}>
              {filteredEsts.length > 0 ? (
                filteredEsts.map((est, index) => {
                  const isVehSelected = selectedCabVehicle &&
                    selectedCabVehicle.provider_key === est.provider_key &&
                    selectedCabVehicle.vehicle_key === est.vehicle_key;

                  const pStyle = PROVIDER_STYLES[est.provider_key] || { bg: C.surface, text: C.text, label: est.provider };

                  const isUnavailable = est.is_vehicle_available === false;
                  const vcat = getVehicleCategory(est);
                  const specialBadge = SPECIAL_BADGES[vcat] || null;

                  return (
                    <button
                      key={index}
                      onClick={() => {
                        if (isUnavailable) return;
                        setSelectedCabVehicle(est);
                        onSelect("cab");
                      }}
                      style={{
                        position: "relative",
                        background: isUnavailable ? C.surface + "88" : isVehSelected ? C.surface : C.card,
                        border: `2px solid ${isUnavailable ? C.border : isVehSelected ? m.color : C.border}`,
                        borderRadius: 12,
                        padding: "12px 14px",
                        textAlign: "left",
                        cursor: isUnavailable ? "not-allowed" : "pointer",
                        width: "100%",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        transition: "all 0.15s",
                        opacity: isUnavailable ? 0.55 : 1,
                        boxShadow: isVehSelected ? `0 4px 16px ${m.color}15` : "none",
                        fontFamily: "inherit"
                      }}
                    >
                      {/* Left details */}
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div style={{
                          fontSize: 24,
                          width: 42,
                          height: 42,
                          background: isVehSelected ? m.color + "18" : C.surface,
                          borderRadius: 10,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          border: `1px solid ${isVehSelected ? m.color + "44" : C.border2}`,
                          filter: isUnavailable ? "grayscale(1)" : "none"
                        }}>
                          {est.icon || "🚗"}
                        </div>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                            <span style={{ fontSize: 13, fontWeight: 800, color: isUnavailable ? C.muted : C.text }}>{est.vehicle_name}</span>
                            {/* Provider badge */}
                            <span style={{
                              fontSize: 9,
                              background: pStyle.bg,
                              color: pStyle.text,
                              padding: "1px 6px",
                              borderRadius: 4,
                              fontWeight: 700,
                              letterSpacing: "0.03em",
                              opacity: isUnavailable ? 0.6 : 1
                            }}>{pStyle.label.toUpperCase()}</span>
                            {/* Special type badge (Priority / Hourly / Parcel) */}
                            {specialBadge && (
                              <span style={{
                                fontSize: 9,
                                background: specialBadge.color + "22",
                                color: specialBadge.color,
                                border: `1px solid ${specialBadge.color}44`,
                                padding: "1px 6px",
                                borderRadius: 4,
                                fontWeight: 700,
                                letterSpacing: "0.03em"
                              }}>{specialBadge.icon} {specialBadge.label}</span>
                            )}
                            {/* Unavailable badge (like real Ola app) */}
                            {isUnavailable && (
                              <span style={{
                                fontSize: 9,
                                background: "#ef444422",
                                color: "#ef4444",
                                border: "1px solid #ef444440",
                                padding: "1px 6px",
                                borderRadius: 4,
                                fontWeight: 700,
                                letterSpacing: "0.04em"
                              }}>UNAVAILABLE</span>
                            )}
                          </div>
                          <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                            {est.description || "Door-to-door ride"} · 👥 {est.capacity || 4}
                          </div>
                        </div>
                      </div>

                      {/* Right details */}
                      <div style={{ textAlign: "right", flexShrink: 0 }}>
                        {isUnavailable ? (
                          <div style={{ fontSize: 12, color: C.muted, fontWeight: 700 }}>—</div>
                        ) : (
                          <>
                            <div style={{ fontSize: 15, fontWeight: 900, color: isVehSelected ? m.color : C.text }}>
                              {est.rental
                                ? `₹${est.cost}/hr`
                                : est.cost_max && est.cost_max > est.cost
                                  ? `₹${est.cost} - ₹${est.cost_max}`
                                  : `₹${est.cost}`}
                            </div>
                            <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                              {est.rental ? "Per package" : `⏱ ${est.time} min`}
                            </div>
                          </>
                        )}
                      </div>
                    </button>
                  );
                })
              ) : (
                <div style={{ padding: "20px 0", textAlign: "center", color: C.muted, fontSize: 12 }}>
                  No options available in this category.
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {/* Multimodal options section - only visible when selected and modeKey is multimodal */}
      {(() => {
        if (modeKey !== "multimodal" || !isSelected || !data.all_options) return null;

        return (
          <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${C.border}`, background: C.bg + "44" }}>
            <div style={{ padding: "12px 4px 8px", fontSize: 11, fontWeight: 800, color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Select Travel Option Combo:
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 280, overflowY: "auto", paddingRight: 4 }}>
              {data.all_options.map((opt, oidx) => {
                const isOptSelected = selectedMultimodalOption && selectedMultimodalOption.combination_type === opt.combination_type;
                return (
                  <button
                    key={oidx}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedMultimodalOption(opt);
                    }}
                    style={{
                      background: isOptSelected ? m.color + "14" : C.surface,
                      border: `1.5px solid ${isOptSelected ? m.color : C.border2}`,
                      borderRadius: 10,
                      padding: "10px 14px",
                      textAlign: "left",
                      width: "100%",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      transition: "all 0.15s",
                      boxShadow: isOptSelected ? `0 4px 16px ${m.color}15` : "none",
                      fontFamily: "inherit",
                      cursor: "pointer"
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 800, color: isOptSelected ? m.color : C.text }}>
                        {opt.combination_label}
                      </div>
                      <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                        {opt.route_summary}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontSize: 14, fontWeight: 900, color: isOptSelected ? m.color : C.text }}>₹{opt.cost}</div>
                      <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>⏱ {opt.time} min</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* Tabs */}
      <div onClick={e => e.stopPropagation()} style={{ borderTop: `1px solid ${C.border}` }}>
        <div style={{ display: "flex" }}>
          {[{ id: "segments", l: "🗂 Segments" }, { id: "stops", l: "🚏 Stops" }, { id: "guide", l: "📋 Guide" }].map(t => (
            <button key={t.id} onClick={() => setTab(tab === t.id ? null : t.id)} style={{
              flex: 1, padding: "9px 4px", background: tab === t.id ? m.color + "18" : "transparent",
              border: "none", borderBottom: tab === t.id ? `2px solid ${m.color}` : "2px solid transparent",
              color: tab === t.id ? m.color : C.muted, fontSize: 11, fontWeight: 700,
              cursor: "pointer", fontFamily: "inherit",
            }}>{t.l}</button>
          ))}
        </div>

        {tab === "segments" && data.segments && (
          <div style={{ padding: "14px 18px" }}>
            {data.segments.map((seg, i) => (
              <div key={i}>
                {i > 0 && <div style={{ display: "flex", alignItems: "center", gap: 6, margin: "8px 0", color: C.muted, fontSize: 11 }}><Ic n="transfer" s={11} c={C.muted} /> Transfer at {data.segments[i - 1].to}</div>}
                <div style={{ background: C.surface, borderRadius: 10, padding: "10px 12px", border: `1px solid ${C.border}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                    <Pill color={m.color}>{seg.route}</Pill>
                    <span style={{ fontSize: 11, color: C.muted }}>{seg.from} → {seg.to}</span>
                  </div>
                  <div style={{ display: "flex", gap: 12, fontSize: 12, color: C.muted, flexWrap: "wrap" }}>
                    <span>🕐 {seg.departure}–{seg.arrival}</span>
                    <span>⏱ {seg.duration} min</span>
                    <span>📍 {seg.distance} km</span>
                    <span>₹{seg.fare}</span>
                    {seg.stops?.length > 0 && <span>{seg.stops.length} stops</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "stops" && (
          <div style={{ padding: "14px 18px", maxHeight: 280, overflowY: "auto" }}>
            {data.segments?.map((seg, i) => (
              <div key={i} style={{ marginBottom: i < data.segments.length - 1 ? 16 : 0 }}>
                {data.segments.length > 1 && <div style={{ marginBottom: 8 }}><Pill color={m.color} small>{seg.route}</Pill></div>}
                <StopTimeline stops={seg.stops?.length > 0 ? seg.stops : [seg.from, seg.to]} color={m.color} />
              </div>
            ))}
          </div>
        )}

        {tab === "guide" && (
          <div style={{ padding: "14px 18px" }}>
            <TravelGuide guide={data.guide} color={m.color} />
          </div>
        )}
      </div>
      </div>

      {/* Select bar */}
      <div style={{ background: isSelected ? m.color : m.bg, padding: "10px 18px", display: "flex", alignItems: "center", justifyContent: "center", gap: 6, transition: "all 0.18s" }}>
        {isSelected && <Ic n="check" s={13} c="white" />}
        <span style={{ fontSize: 12, fontWeight: 700, color: isSelected ? "white" : m.color }}>
          {isSelected ? "Selected ✓" : "Select this option"}
        </span>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   COMPARE TABLE
───────────────────────────────────────────────────────────── */
function CompareTable({ results }) {
  const modes = Object.keys(results).filter(m => results[m]?.available);
  const rows = [
    { label: "Duration", key: "time", lower: true, fmt: v => `${v} min` },
    { label: "Cost", key: "cost", lower: true, fmt: v => `₹${v}` },
    { label: "Transfers", key: "transfers", lower: true, fmt: v => `${v}` },
    { label: "Distance", key: "distance", lower: true, fmt: v => `${v} km` },
    { label: "Departs", key: "departure", lower: false, fmt: v => v },
    { label: "Arrives", key: "arrival", lower: false, fmt: v => v },
  ];
  return (
    <div style={{ background: C.card, borderRadius: 16, overflow: "hidden", border: `1px solid ${C.border}` }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: C.surface }}>
            <th style={{ padding: "12px 16px", textAlign: "left", fontSize: 11, color: C.muted, fontWeight: 700 }}>CRITERIA</th>
            {modes.map(m => (
              <th key={m} style={{ padding: "12px 16px", textAlign: "center" }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                  <div style={{ width: 30, height: 30, borderRadius: 8, background: MC[m].bg, border: `1px solid ${MC[m].color}44`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Ic n={MC[m].icon} s={14} c={MC[m].color} />
                  </div>
                  <span style={{ fontSize: 10, fontWeight: 800, color: MC[m].color }}>{MC[m].short}</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(row => {
            const vals = modes.map(m => results[m][row.key]);
            const numVals = vals.filter(v => typeof v === "number");
            const best = row.lower && numVals.length ? Math.min(...numVals) : null;
            return (
              <tr key={row.key} style={{ borderBottom: `1px solid ${C.border}` }}>
                <td style={{ padding: "11px 16px", fontSize: 12, color: C.muted, fontWeight: 600 }}>{row.label}</td>
                {modes.map(m => {
                  const v = results[m][row.key];
                  const isBest = typeof v === "number" && v === best;
                  return (
                    <td key={m} style={{ padding: "11px 16px", textAlign: "center", fontSize: 13, fontWeight: isBest ? 800 : 500, color: isBest ? MC[m].color : C.text }}>
                      {row.fmt(v)}{isBest && " ★"}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   DASHBOARD
───────────────────────────────────────────────────────────── */
function Dashboard({ token, username, onPlan, onSelectRoute, onLogout, garageOpen, setGarageOpen, gloveboxOpen, setGloveboxOpen }) {
  const [data, setData] = useState({ stats: [], recent: [], saved: [] });
  const [vehicles, setVehicles] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Vehicle form state
  const [vname, setVname] = useState("");
  const [vfuel, setVfuel] = useState("Petrol");
  const [veff, setVeff] = useState("");

  // Document form state
  const [docType, setDocType] = useState("Driving License");
  const [docNum, setDocNum] = useState("");
  const [docExpiry, setDocExpiry] = useState("");
  const [docFile, setDocFile] = useState(null);



  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [dash, vehs, docs] = await Promise.all([
        apiGetDashboard(token),
        apiGetVehicles(token),
        apiGetDocuments(token)
      ]);
      setData(dash);
      setVehicles(vehs);
      setDocuments(docs);
    } catch (e) {
      console.error("Error loading dashboard data:", e);
      if (e.message === "Unauthorized" && onLogout) {
        onLogout();
      }
    } finally {
      setLoading(false);
    }
  }, [token, onLogout]);

  useEffect(() => {
    if (token) loadData();
  }, [token, loadData]);

  const handleAddVehicle = async (e) => {
    e.preventDefault();
    if (!vname.trim() || !veff) return;
    try {
      await apiAddVehicle(token, {
        name: vname.trim(),
        fuel_type: vfuel,
        efficiency: parseFloat(veff)
      });
      setVname("");
      setVeff("");
      setGarageOpen(false);
      const vehs = await apiGetVehicles(token);
      setVehicles(vehs);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteVehicle = async (id) => {
    if (!confirm("Are you sure you want to delete this vehicle?")) return;
    try {
      await apiDeleteVehicle(token, id);
      setVehicles(vehicles.filter(v => v.id !== id));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAddDocument = async (e) => {
    e.preventDefault();
    if (!docNum.trim() || !docExpiry || !docFile) {
      alert("Please fill all document fields and select a file.");
      return;
    }
    try {
      const formData = new FormData();
      formData.append("doc_type", docType);
      formData.append("doc_number", docNum);
      formData.append("expiry_date", docExpiry);
      formData.append("file", docFile);

      await apiAddDocument(token, formData);
      setDocNum("");
      setDocExpiry("");
      setDocFile(null);
      setGloveboxOpen(false);

      const fileInput = document.getElementById("doc-file-input");
      if (fileInput) fileInput.value = "";

      const docs = await apiGetDocuments(token);
      setDocuments(docs);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteDocument = async (id) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await apiDeleteDocument(token, id);
      setDocuments(documents.filter(d => d.id !== id));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteSavedRoute = async (id) => {
    if (!confirm("Are you sure you want to delete this saved route?")) return;
    try {
      await apiDeleteJourney(token, id);
      loadData();
    } catch (err) {
      alert(err.message);
    }
  };

  const getDocExpiryStatus = (expiryStr) => {
    if (!expiryStr) return { label: "No Date", color: C.muted };
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const expiry = new Date(expiryStr);
    expiry.setHours(0, 0, 0, 0);

    if (expiry < today) {
      return { label: "Expired", color: C.red };
    }

    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays <= 30) {
      return { label: `Expiring in ${diffDays}d`, color: C.yellow };
    }

    return { label: "Valid", color: C.green };
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: 300, color: C.muted, flexDirection: "column", gap: 10 }}>
        <div style={{ width: 28, height: 28, borderRadius: "50%", border: `3px solid ${C.accent}`, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
        <div style={{ fontSize: 13 }}>Loading your profile...</div>
      </div>
    );
  }

  const displayStats = (() => {
    const raw = data.stats && data.stats.length >= 4 ? data.stats : [
      { label: "Journeys", val: "0" },
      { label: "Saved", val: "₹0" },
      { label: "Time saved", val: "0 hr" },
      { label: "Avg cost", val: "₹0" }
    ];
    return [
      { label: "Journeys", val: raw[0]?.val || "0", sub: "This month", icon: "mappin", color: "#7c3aed", bg: "rgba(124, 58, 237, 0.08)" },
      { label: "Time saved", val: raw[2]?.val || "0 hr", sub: "This month", icon: "check", color: "#10b981", bg: "rgba(16, 185, 129, 0.08)" },
      { label: "Avg cost", val: raw[3]?.val || "₹0", sub: "Per journey", icon: "bolt", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)" },
      { label: "CO₂ saved", val: "0", sub: "This month", icon: "compass", color: "#ef4444", bg: "rgba(239, 68, 68, 0.08)" }
    ];
  })();

  return (
    <div style={{ fontFamily: "inherit" }}>
      {/* Visual Welcome Banner */}
      <div style={{
        background: "linear-gradient(135deg, #eae8ff 0%, #f5e8ff 100%)",
        border: "1px solid rgba(124, 58, 237, 0.12)",
        borderRadius: 24,
        padding: "36px 40px",
        marginBottom: 32,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "relative",
        overflow: "hidden",
        minHeight: 140
      }}>
        {/* Background Vidhana Soudha Cityscape blending on the right */}
        <div style={{
          position: "absolute",
          right: 0,
          bottom: 0,
          height: "100%",
          width: "50%",
          pointerEvents: "none",
          zIndex: 1
        }}>
          <img src={heroImg} alt="Bengaluru Landmarks" style={{ width: "100%", height: "100%", objectFit: "contain", objectPosition: "right bottom" }} />
        </div>

        <div style={{ zIndex: 2, position: "relative" }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, color: "#1e1b24", margin: "0 0 8px 0", letterSpacing: "-0.03em" }}>Good Morning, {username}! 👋</h1>
          <p style={{ color: C.muted, fontSize: 14, fontWeight: 600, margin: 0 }}>Let's make your journey easy and efficient.</p>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20, marginBottom: 32 }}>
        {displayStats.map((s) => (
          <div 
            key={s.label} 
            style={{ 
              background: "#ffffff", 
              border: `1px solid ${C.border}`, 
              borderRadius: 20, 
              padding: "20px 24px", 
              boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
              transition: "all 0.25s ease",
              cursor: "default"
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = "translateY(-2px)";
              e.currentTarget.style.boxShadow = "rgba(0, 0, 0, 0.04) 0 12px 24px";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = "none";
              e.currentTarget.style.boxShadow = "rgba(0, 0, 0, 0.01) 0 10px 30px";
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ 
                width: 44, 
                height: 44, 
                borderRadius: "50%", 
                background: s.bg,
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center",
                flexShrink: 0
              }}>
                <Ic n={s.icon} s={18} c={s.color} sw={2.2} />
              </div>
              <div>
                <div style={{ fontSize: 24, fontWeight: 900, color: "#1e1b24", lineHeight: "1.2" }}>{s.val}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#1e1b24", marginTop: 2 }}>{s.label}</div>
                <div style={{ fontSize: 10, color: C.muted, fontWeight: 600, marginTop: 1 }}>{s.sub}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Row 1: Recent Searches (left) & Saved Places (right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 24 }}>
        
        {/* Recent Searches */}
        <div style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="clock" s={16} c={C.text} sw={2.2} /> Recent Searches
            </h2>
            {data.recent?.length > 0 && (
              <span style={{ fontSize: 11, background: "rgba(124, 58, 237, 0.08)", color: C.accent, padding: "4px 10px", borderRadius: 20, fontWeight: 700 }}>
                {data.recent.length} searches
              </span>
            )}
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
            {data.recent && data.recent.length > 0 ? (
              data.recent.slice(0, 3).map((r, i) => (
                <div 
                  key={r.id || i}
                  onClick={() => onSelectRoute(r.from, r.to)}
                  style={{ 
                    display: "flex", 
                    alignItems: "center", 
                    gap: 14, 
                    padding: "12px 14px", 
                    borderRadius: 16, 
                    cursor: "pointer", 
                    background: "#f9f9fc",
                    border: "1px solid #f1f1f5",
                    transition: "all 0.2s" 
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = "#f1efff";
                    e.currentTarget.style.borderColor = "rgba(124, 58, 237, 0.2)";
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = "#f9f9fc";
                    e.currentTarget.style.borderColor = "#f1f1f5";
                  }}
                >
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(124, 58, 237, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <Ic n="search" s={14} c={C.accent} sw={2.2} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#1e1b24", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.from} → {r.to}</div>
                    <div style={{ fontSize: 11, color: C.muted, marginTop: 2, fontWeight: 500 }}>{r.date}</div>
                  </div>
                  <div style={{ fontSize: 11, color: C.accent, fontWeight: 700 }}>Search →</div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: "center", padding: "40px 0", color: C.muted, fontSize: 13, flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 10 }}>
                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Ic n="search" s={18} c={C.muted} sw={2.2} />
                </div>
                No recent searches. Start planning to view routes!
              </div>
            )}
          </div>
        </div>

        {/* Saved Places */}
        <div id="saved-places-card" style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="star" s={16} c="#f59e0b" sw={2.2} /> Saved Places
            </h2>
            <button 
              onClick={onPlan} 
              style={{ background: "none", border: "none", fontSize: 12, fontWeight: 700, color: C.accent, cursor: "pointer", padding: 0 }}
            >
              View all
            </button>
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1, justifyContent: "center" }}>
            {data.saved && data.saved.length > 0 ? (
              data.saved.slice(0, 3).map((r, i) => {
                const modeColor = MC[r.mode]?.color || C.accent;
                const modeBg = MC[r.mode]?.bg || "rgba(124, 58, 237, 0.05)";
                return (
                  <div 
                    key={r.id || i}
                    onClick={() => onSelectRoute(r.from, r.to)}
                    style={{ 
                      display: "flex", 
                      alignItems: "center", 
                      gap: 14, 
                      padding: "12px 14px", 
                      borderRadius: 16, 
                      cursor: "pointer", 
                      background: "#f9f9fc",
                      border: "1px solid #f1f5f9",
                      transition: "all 0.2s" 
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = "#f1efff";
                      e.currentTarget.style.borderColor = "rgba(124, 58, 237, 0.2)";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "#f9f9fc";
                      e.currentTarget.style.borderColor = "#f1f5f9";
                    }}
                  >
                    <div style={{ width: 36, height: 36, borderRadius: 10, background: modeBg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <Ic n={MC[r.mode]?.icon || "mappin"} s={15} c={modeColor} sw={2} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: "#1e1b24", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {r.custom_name ? r.custom_name : `${r.from} → ${r.to}`}
                        </span>
                        {r.custom_name && <Pill color={modeColor} small>{MC[r.mode]?.short || "SAVED"}</Pill>}
                      </div>
                      {r.custom_name && <div style={{ fontSize: 11, color: C.muted, marginTop: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.from} → {r.to}</div>}
                      <div style={{ fontSize: 11, color: C.muted, marginTop: 2, fontWeight: 500 }}>{r.date} · Est. Cost: ₹{r.cost}</div>
                    </div>
                    <button 
                      onClick={(e) => { e.stopPropagation(); handleDeleteSavedRoute(r.id); }} 
                      style={{ 
                        background: "none", 
                        border: "none", 
                        color: C.red, 
                        cursor: "pointer", 
                        padding: "6px",
                        borderRadius: 8,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        transition: "background 0.2s"
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = "#fee2e2"}
                      onMouseLeave={e => e.currentTarget.style.background = "none"}
                    >
                      <Ic n="x" s={14} c={C.red} />
                    </button>
                  </div>
                );
              })
            ) : (
              <div style={{ textAlign: "center", padding: "16px 0", color: C.muted, fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 8 }}>
                <div style={{ width: 48, height: 48, borderRadius: "50%", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Ic n="star" s={18} c={C.muted} sw={2.2} />
                </div>
                <div style={{ fontWeight: 800, color: C.text }}>No saved Places yet</div>
                <div style={{ fontSize: 11, color: C.muted }}>Bookmark your favourite locations and routes</div>
                <button 
                  onClick={onPlan} 
                  style={{
                    marginTop: 8,
                    background: "none",
                    border: `1.5px solid ${C.accent}`,
                    borderRadius: 10,
                    padding: "8px 20px",
                    color: C.accent,
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = C.accent; e.currentTarget.style.color = "#ffffff"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "none"; e.currentTarget.style.color = C.accent; }}
                >
                  + Add Place
                </button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Row 2: My Garage (left) & Digital Glovebox (center) & Quick Actions (right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1.1fr", gap: 24, marginBottom: 24 }}>
        
        {/* My Garage */}
        <div id="my-garage-card" style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="car" s={16} c={C.text} sw={2.2} /> My Garage
            </h2>
            <button 
              onClick={() => setGarageOpen(!garageOpen)} 
              style={{ 
                background: "none", 
                border: `1.5px solid ${garageOpen ? C.border2 : C.accent}`, 
                borderRadius: 10, 
                padding: "6px 14px", 
                fontSize: 11, 
                fontWeight: 700,
                color: garageOpen ? C.muted : C.accent, 
                cursor: "pointer", 
                fontFamily: "inherit",
                transition: "all 0.2s"
              }}
            >
              {garageOpen ? "Close" : "+ Add"}
            </button>
          </div>

          {garageOpen && (
            <form onSubmit={handleAddVehicle} style={{ background: "#f9f9fc", borderRadius: 16, padding: 16, marginBottom: 16, border: "1px solid #f1f1f5" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 12, textTransform: "uppercase" }}>New Vehicle Specs</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <input 
                  value={vname} 
                  onChange={e => setVname(e.target.value)} 
                  placeholder="Vehicle Model, e.g. Tesla Model Y" 
                  required 
                  style={{ width: "100%", background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }} 
                />
                <div style={{ display: "flex", gap: 10 }}>
                  <select 
                    value={vfuel} 
                    onChange={e => setVfuel(e.target.value)} 
                    style={{ flex: 1, background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
                  >
                    <option value="Petrol">Petrol</option>
                    <option value="Diesel">Diesel</option>
                    <option value="EV">EV</option>
                    <option value="CNG">CNG</option>
                  </select>
                  <input 
                    type="number" 
                    step="0.01" 
                    value={veff} 
                    onChange={e => setVeff(e.target.value)} 
                    placeholder={vfuel === "EV" ? "km/kWh" : "km/L"} 
                    required 
                    style={{ flex: 1.2, background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }} 
                  />
                </div>
                <button 
                  type="submit" 
                  style={{ 
                    background: "linear-gradient(135deg, #7c3aed, #a855f7)", 
                    border: "none", 
                    color: "white", 
                    borderRadius: 12, 
                    padding: "11px", 
                    fontSize: 13, 
                    fontWeight: 700, 
                    cursor: "pointer", 
                    fontFamily: "inherit"
                  }}
                >
                  Save to Garage
                </button>
              </div>
            </form>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
            {vehicles.length > 0 ? (
              vehicles.slice(0, 3).map(v => (
                <div key={v.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", background: "#f9f9fc", border: "1px solid #f1f1f5", borderRadius: 16 }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(16, 185, 129, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <span style={{ fontSize: 14 }}>{v.fuel_type === "EV" ? "⚡" : "🚗"}</span>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#1e1b24", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.name}</div>
                    <div style={{ fontSize: 10, color: C.muted, marginTop: 2, fontWeight: 500 }}>
                      Type: {v.fuel_type} - Efficiency: {v.efficiency} {v.fuel_type === "EV" ? "km/kWh" : "km/L"}
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDeleteVehicle(v.id)} 
                    style={{ 
                      background: "none", 
                      border: "none", 
                      color: C.red, 
                      cursor: "pointer", 
                      padding: "6px",
                      borderRadius: 8,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      transition: "background 0.2s"
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = "#fee2e2"}
                    onMouseLeave={e => e.currentTarget.style.background = "none"}
                  >
                    <Ic n="x" s={14} c={C.red} />
                  </button>
                </div>
              ))
            ) : (
              <div style={{ textAlign: "center", padding: "30px 0", color: C.muted, fontSize: 12, flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 8 }}>
                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Ic n="car" s={18} c={C.muted} sw={2.2} />
                </div>
                No vehicles added yet. Add vehicles to calculate journey driving costs!
              </div>
            )}
          </div>
        </div>

        {/* Digital Glovebox */}
        <div id="digital-glovebox-card" style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="folder" s={16} c={C.text} sw={2.2} /> Digital Glovebox
            </h2>
            <button 
              onClick={() => setGloveboxOpen(!gloveboxOpen)} 
              style={{ 
                background: "none", 
                border: `1.5px solid ${gloveboxOpen ? C.border2 : C.accent}`, 
                borderRadius: 10, 
                padding: "6px 14px", 
                fontSize: 11, 
                fontWeight: 700,
                color: gloveboxOpen ? C.muted : C.accent, 
                cursor: "pointer", 
                fontFamily: "inherit",
                transition: "all 0.2s"
              }}
            >
              {gloveboxOpen ? "Close" : "+ Add"}
            </button>
          </div>

          {gloveboxOpen && (
            <form onSubmit={handleAddDocument} style={{ background: "#f9f9fc", borderRadius: 16, padding: 16, marginBottom: 16, border: "1px solid #f1f1f5" }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 12, textTransform: "uppercase" }}>New Document Upload</div>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <select 
                  value={docType} 
                  onChange={e => setDocType(e.target.value)} 
                  style={{ width: "100%", background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
                >
                  <option value="Driving License">Driving License</option>
                  <option value="Registration Certificate (RC)">Registration Certificate (RC)</option>
                  <option value="Insurance Policy">Insurance Policy</option>
                  <option value="Pollution Under Control (PUC)">Pollution Under Control (PUC)</option>
                </select>
                <div style={{ display: "flex", gap: 10 }}>
                  <input 
                    value={docNum} 
                    onChange={e => setDocNum(e.target.value)} 
                    placeholder="Doc No." 
                    required 
                    style={{ flex: 1, background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }} 
                  />
                  <input 
                    type="date" 
                    value={docExpiry} 
                    onChange={e => setDocExpiry(e.target.value)} 
                    required 
                    style={{ flex: 1, background: "#ffffff", border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }} 
                  />
                </div>
                <div>
                  <input id="doc-file-input" type="file" onChange={e => setDocFile(e.target.files[0])} required style={{ fontSize: 11, color: C.text }} />
                </div>
                <button 
                  type="submit" 
                  style={{ 
                    background: "linear-gradient(135deg, #7c3aed, #a855f7)", 
                    border: "none", 
                    color: "white", 
                    borderRadius: 12, 
                    padding: "11px", 
                    fontSize: 13, 
                    fontWeight: 700, 
                    cursor: "pointer", 
                    fontFamily: "inherit"
                  }}
                >
                  Upload & Secure
                </button>
              </div>
            </form>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 10, flex: 1 }}>
            {documents.length > 0 ? (
              documents.slice(0, 3).map(d => {
                const status = getDocExpiryStatus(d.expiry_date);
                return (
                  <div key={d.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", background: "#f9f9fc", border: "1px solid #f1f1f5", borderRadius: 16 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: "#1e1b24" }}>{d.doc_type}</span>
                        <Pill color={status.color} small>{status.label}</Pill>
                      </div>
                      <div style={{ fontSize: 10, color: C.muted, marginTop: 4, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>No: {d.doc_number}</div>
                    </div>
                    <div style={{ display: "flex", gap: 4 }}>
                      <a 
                        href={`${API_BASE}${d.file_path}`} 
                        target="_blank" 
                        rel="noreferrer" 
                        style={{ 
                          background: "rgba(124, 58, 237, 0.08)", 
                          color: C.accent, 
                          border: `1px solid rgba(124, 58, 237, 0.2)`, 
                          borderRadius: 8, 
                          padding: "4px 8px", 
                          fontSize: 11, 
                          fontWeight: 700, 
                          textDecoration: "none"
                        }}
                      >
                        View
                      </a>
                      <button 
                        onClick={() => handleDeleteDocument(d.id)} 
                        style={{ 
                          background: "none", 
                          border: "none", 
                          color: C.red, 
                          cursor: "pointer", 
                          padding: "6px",
                          borderRadius: 8,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center"
                        }}
                      >
                        <Ic n="x" s={12} c={C.red} />
                      </button>
                    </div>
                  </div>
                );
              })
            ) : (
              <div style={{ textAlign: "center", padding: "30px 0", color: C.muted, fontSize: 12, flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 8 }}>
                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Ic n="doc" s={18} c={C.muted} sw={2.2} />
                </div>
                <div style={{ fontWeight: 800, color: C.text }}>No documents uploaded yet</div>
                <div style={{ fontSize: 11, color: C.muted }}>Secure DL, insurance & RC here.</div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, marginBottom: 20 }}>
            <Ic n="now" s={16} c="#f59e0b" sw={2.2} /> Quick Actions
          </h2>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, flex: 1 }}>
            {[
              { label: "Live Map", sub: "Track vehicles", icon: "gps", color: "#10b981", bg: "rgba(16, 185, 129, 0.08)" },
              { label: "Fare Guide", sub: "Check fares", icon: "table", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.08)" },
              { label: "Alerts", sub: "Stay updated", icon: "bell", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)" },
              { label: "Search Routes", sub: "Find routes", icon: "search", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.08)" },
            ].map(act => (
              <div 
                key={act.label}
                onClick={onPlan}
                style={{ 
                  border: "1px solid #f1f1f5", 
                  borderRadius: 16, 
                  padding: "12px 14px", 
                  display: "flex", 
                  flexDirection: "column", 
                  gap: 8,
                  background: "#f9f9fc",
                  cursor: "pointer",
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "scale(1.02)";
                  e.currentTarget.style.background = "#ffffff";
                  e.currentTarget.style.borderColor = act.color + "30";
                  e.currentTarget.style.boxShadow = "rgba(0, 0, 0, 0.04) 0 8px 16px";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.background = "#f9f9fc";
                  e.currentTarget.style.borderColor = "#f1f1f5";
                  e.currentTarget.style.boxShadow = "none";
                }}
              >
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: act.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <Ic n={act.icon} s={14} c={act.color} sw={2.2} />
                </div>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 800, color: "#1e1b24" }}>{act.label}</div>
                  <div style={{ fontSize: 10, color: C.muted, marginTop: 2, fontWeight: 500 }}>{act.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Row 3: Commute Suggestions (left) & Travel Alerts (right) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        
        {/* Commute Suggestions */}
        <div style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="rocket" s={16} c={C.accent} sw={2.2} /> Commute Suggestions
            </h2>
            <button 
              onClick={onPlan} 
              style={{ background: "none", border: "none", fontSize: 12, fontWeight: 700, color: C.accent, cursor: "pointer", padding: 0 }}
            >
              See all
            </button>
          </div>

          <div style={{
            background: "rgba(124, 58, 237, 0.04)",
            border: "1px solid rgba(124, 58, 237, 0.1)",
            borderRadius: 16,
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: 16
          }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(124, 58, 237, 0.1)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Ic n="rocket" s={16} c={C.accent} sw={2.2} />
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 800, color: "#1e1b24" }}>Beat the traffic!</div>
              <div style={{ fontSize: 11, color: C.muted, marginTop: 4, fontWeight: 500, lineHeight: 1.4 }}>Travel before 9:00 AM to save up to 25% time on your commute.</div>
            </div>
          </div>

          {/* Dots Pagination */}
          <div style={{ display: "flex", justifyContent: "center", gap: 6, marginTop: 16 }}>
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: C.accent }} />
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#e2e8f0" }} />
            <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#e2e8f0" }} />
          </div>
        </div>

        {/* Travel Alerts */}
        <div id="travel-alerts-card" style={{ 
          background: "#ffffff", 
          border: `1px solid ${C.border}`, 
          borderRadius: 24, 
          padding: "28px 24px",
          boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
          display: "flex",
          flexDirection: "column"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 16, fontWeight: 900, color: "#1e1b24", display: "flex", alignItems: "center", gap: 8, margin: 0 }}>
              <Ic n="bell" s={16} c={C.red} sw={2.2} /> Travel Alerts
            </h2>
            <button 
              onClick={onPlan} 
              style={{ background: "none", border: "none", fontSize: 12, fontWeight: 700, color: C.accent, cursor: "pointer", padding: 0 }}
            >
              View all
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {/* Transit Alert */}
            <div style={{
              background: "rgba(239, 68, 68, 0.03)",
              border: "1px solid rgba(239, 68, 68, 0.08)",
              borderRadius: 16,
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              gap: 12
            }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(239, 68, 68, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Ic n="alert" s={14} c={C.red} sw={2.2} />
              </div>
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 800, color: "#1e1b24" }}>Transit: No active alerts</div>
                <div style={{ fontSize: 10.5, color: C.muted, marginTop: 2, fontWeight: 500 }}>No disruptions on your saved routes.</div>
              </div>
            </div>

            {/* Weather Alert */}
            <div style={{
              background: "rgba(59, 130, 246, 0.03)",
              border: "1px solid rgba(59, 130, 246, 0.08)",
              borderRadius: 16,
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              gap: 12
            }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(59, 130, 246, 0.08)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <span style={{ fontSize: 14 }}>☀️</span>
              </div>
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 800, color: "#1e1b24" }}>Weather: 27°C Partly Cloudy</div>
                <div style={{ fontSize: 10.5, color: C.muted, marginTop: 2, fontWeight: 500 }}>Perfect commute weather. No rain expected today.</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function AuthScreen({ onLoginSuccess, onBackToHome, initialMode = "login" }) {
  const [isLogin, setIsLogin] = useState(initialMode !== "signup");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userFocused, setUserFocused] = useState(false);
  const [passFocused, setPassFocused] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setLoading(true); setError(null);
    try {
      if (isLogin) {
        const res = await apiLogin(username.trim(), password);
        onLoginSuccess(res.username, res.access_token);
      } else {
        const res = await apiSignup(username.trim(), password);
        onLoginSuccess(res.username, res.access_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: `linear-gradient(135deg, ${C.bg} 0%, #eef0f6 100%)`,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: 20,
      fontFamily: "'Plus Jakarta Sans', 'Outfit', 'Segoe UI', sans-serif"
    }}>
      {onBackToHome && (
        <button
          onClick={onBackToHome}
          style={{
            background: "none",
            border: "none",
            color: C.accent,
            fontWeight: 800,
            cursor: "pointer",
            fontSize: 14,
            display: "flex",
            alignItems: "center",
            gap: 6,
            marginBottom: 20,
            transition: "all 0.2s ease",
            padding: "8px 16px",
            borderRadius: 10
          }}
          onMouseEnter={e => e.currentTarget.style.transform = "translateX(-4px)"}
          onMouseLeave={e => e.currentTarget.style.transform = "none"}
        >
          <Ic n="arrow" s={14} c={C.accent} sw={2.5} style={{ transform: "rotate(180deg)" }} />
          Back to Home
        </button>
      )}
      <div style={{
        background: C.surface,
        border: `1px solid ${C.border2}`,
        borderRadius: 24,
        width: 420,
        padding: 36,
        boxShadow: "0 20px 50px rgba(26, 22, 37, 0.05), 0 1px 3px rgba(0, 0, 0, 0.02)",
        position: "relative"
      }}>

        {/* Header */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 28 }}>
          <div style={{
            width: 48,
            height: 48,
            borderRadius: 14,
            background: "linear-gradient(135deg, #7c3aed, #ec4899)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 14,
            boxShadow: "rgba(124, 58, 237, 0.2) 0 8px 16px"
          }}>
            <Ic n="bus" s={24} c="white" sw={2.2} />
          </div>
          <div style={{ fontWeight: 900, fontSize: 22, color: C.text, letterSpacing: "-0.04em" }}>UTRS Bengaluru</div>
          <div style={{ fontSize: 10, color: C.muted, letterSpacing: "0.15em", marginTop: 4, fontWeight: 700 }}>UNIFIED TRANSIT REGISTER</div>
        </div>

        {/* Title */}
        <div style={{ fontSize: 16, fontWeight: 800, color: C.text, marginBottom: 18, textAlign: "center" }}>
          {isLogin ? "Sign In to your Account" : "Create your Account"}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              onFocus={() => setUserFocused(true)}
              onBlur={() => setUserFocused(false)}
              required
              style={{
                width: "100%",
                background: C.surface,
                border: `1.5px solid ${userFocused ? C.accent : C.border2}`,
                borderRadius: 12,
                color: C.text,
                padding: "12px 14px",
                fontSize: 14,
                outline: "none",
                fontFamily: "inherit",
                transition: "all 0.15s ease",
                boxShadow: userFocused ? `0 0 0 3px ${C.accent}20` : "none"
              }}
            />
          </div>
          <div>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onFocus={() => setPassFocused(true)}
              onBlur={() => setPassFocused(false)}
              required
              style={{
                width: "100%",
                background: C.surface,
                border: `1.5px solid ${passFocused ? C.accent : C.border2}`,
                borderRadius: 12,
                color: C.text,
                padding: "12px 14px",
                fontSize: 14,
                outline: "none",
                fontFamily: "inherit",
                transition: "all 0.15s ease",
                boxShadow: passFocused ? `0 0 0 3px ${C.accent}20` : "none"
              }}
            />
          </div>

          {error && (
            <div style={{
              background: `${C.red}15`,
              border: `1px solid ${C.red}30`,
              borderRadius: 10,
              padding: "10px 12px",
              fontSize: 12,
              color: C.red,
              display: "flex",
              alignItems: "center",
              gap: 6
            }}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              background: `linear-gradient(135deg, ${C.accent}, #a855f7)`,
              border: "none",
              color: "white",
              borderRadius: 12,
              padding: "13px",
              fontSize: 14,
              fontWeight: 800,
              cursor: loading ? "wait" : "pointer",
              boxShadow: `0 4px 20px ${C.accent}30`,
              marginTop: 6,
              transition: "all 0.15s ease"
            }}
            onMouseEnter={e => {
              e.currentTarget.style.opacity = "0.95";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.opacity = "1";
              e.currentTarget.style.transform = "none";
            }}
          >
            {loading ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <div style={{ width: 14, height: 14, borderRadius: "50%", border: "2px solid white", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
                <span>Processing...</span>
              </div>
            ) : (
              isLogin ? "Sign In" : "Sign Up"
            )}
          </button>
        </form>

        {/* Switcher */}
        <div style={{ marginTop: 24, fontSize: 13, textAlign: "center", color: C.muted }}>
          {isLogin ? "New to UTRS? " : "Already have an account? "}
          <button
            onClick={() => { setIsLogin(!isLogin); setError(null); }}
            style={{
              background: "none",
              border: "none",
              color: C.accent,
              fontWeight: 700,
              cursor: "pointer",
              padding: "0 4px",
              fontSize: 13,
              textDecoration: "underline"
            }}
          >
            {isLogin ? "Create Account" : "Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}


// Sub-components for chatbot multimodal routing comparisons & nearby POIs
function ComparisonDashboard({ data, onSelectRoute }) {
  const [expandedMode, setExpandedMode] = useState(null);
  
  if (!data || !data.options) return null;

  const modeIcons = {
    bmtc: "🚌",
    metro: "🚇",
    multimodal: "🔀",
    ola: "🚕",
    uber: "🚙",
    rapido: "🏍️",
    namma_yatri: "🛺",
    car: "🚗",
    bike: "🛵"
  };

  const modeLabels = {
    bmtc: "BMTC Bus",
    metro: "Namma Metro",
    multimodal: "Bus + Metro",
    ola: "Ola Cab",
    uber: "Uber Cab",
    rapido: "Rapido Ride",
    namma_yatri: "Namma Yatri",
    car: "Personal Car",
    bike: "Personal Bike"
  };

  const modeColors = {
    bmtc: "#3b82f6",
    metro: "#10b981",
    multimodal: "#ec4899",
    ola: "#f5c518",
    uber: "#e0e0e0",
    rapido: "#a855f7",
    namma_yatri: "#f97316",
    car: "#22c55e",
    bike: "#14b8a6"
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8, width: "100%" }}>
      {data.options.map((opt) => {
        const isExpanded = expandedMode === opt.mode;
        const color = modeColors[opt.mode] || "#64748b";
        
        return (
          <div
            key={opt.mode}
            style={{
              background: "#121420",
              border: `1.5px solid ${isExpanded ? color : "#272a3d"}`,
              borderRadius: 12,
              padding: 12,
              transition: "all 0.2s ease",
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)"
            }}
          >
            {/* Header row */}
            <div 
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
              onClick={() => setExpandedMode(isExpanded ? null : opt.mode)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 18 }}>{modeIcons[opt.mode] || "🚗"}</span>
                <span style={{ fontSize: 13, fontWeight: 800, color: "#ffffff" }}>
                  {modeLabels[opt.mode] || opt.mode}
                </span>
                {opt.score && (
                  <span style={{
                    fontSize: 9.5,
                    fontWeight: 800,
                    color: color,
                    background: `${color}15`,
                    padding: "2px 6px",
                    borderRadius: 6
                  }}>
                    {Math.round(opt.score)}% Match
                  </span>
                )}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 900, color: "#ffffff" }}>₹{opt.cost}</span>
                <span style={{ fontSize: 11, color: "#64748b" }}>{isExpanded ? "▲" : "▼"}</span>
              </div>
            </div>

            {/* Quick Stats Grid */}
            <div style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 8,
              marginTop: 10,
              padding: "6px 8px",
              background: "#08090f",
              borderRadius: 8,
              fontSize: 10.5,
              color: "#94a3b8"
            }}>
              <div>🕒 <strong>{opt.time} min</strong></div>
              <div>📏 <strong>{opt.details?.distance || opt.walking_distance || 0} km</strong></div>
              {(opt.mode === "car" || opt.mode === "bike") ? (
                <div>⛽ <strong>{opt.details?.fuel_needed || opt.fuel_needed || 0} L</strong></div>
              ) : (
                <div>🚶 <strong>{opt.walking_distance || 0} km</strong></div>
              )}
              <div style={{ gridColumn: "span 3", display: "flex", justifyContent: "space-between" }}>
                <span>🌿 CO₂: <strong>{((opt.co2_kg || 0) * 1000).toFixed(0)}g CO₂</strong></span>
                {(opt.mode === "car" || opt.mode === "bike") && (
                  <span style={{ fontSize: 8.5, color: "#f5c518", fontWeight: 700 }}>* Estimated</span>
                )}
              </div>
            </div>

            {/* Explanation and Buttons */}
            {isExpanded && (
              <div style={{ marginTop: 10, borderTop: "1px solid #272a3d", paddingTop: 10 }}>
                <p style={{ fontSize: 11, color: "#94a3b8", lineHeight: 1.4, margin: "0 0 10px 0" }}>
                  {opt.explanation}
                </p>

                {/* Multi-stop leg breakdown */}
                {opt.legs && opt.legs.length > 1 && (
                  <div style={{ marginBottom: 12, padding: 8, background: "#08090f", borderRadius: 8 }}>
                    <div style={{ fontSize: 9.5, fontWeight: 800, color: "#64748b", textTransform: "uppercase", marginBottom: 6 }}>Itinerary Breakdown</div>
                    {opt.legs.map((leg, lIdx) => (
                      <div key={lIdx} style={{ display: "flex", justifyContent: "space-between", fontSize: 10.5, color: "#94a3b8", marginBottom: 4 }}>
                        <span>📍 Leg {lIdx+1}: {leg.from_stop || leg.source || `Stop ${lIdx+1}`} → {leg.to_stop || leg.destination || `Stop ${lIdx+2}`}</span>
                        <span style={{ fontWeight: 700, color: "#ffffff" }}>₹{leg.cost} · {leg.time}m</span>
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectRoute(opt.mode);
                    }}
                    style={{
                      flex: 1,
                      padding: "8px 12px",
                      background: `linear-gradient(135deg, ${color}, ${color}dd)`,
                      border: "none",
                      borderRadius: 8,
                      color: "#ffffff",
                      fontSize: 11,
                      fontWeight: 700,
                      cursor: "pointer",
                      fontFamily: "inherit"
                    }}
                  >
                    Select & Draw Route 🗺️
                  </button>
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function NearbyPlacesDashboard({ data, onSelectPlace }) {
  if (!data || !data.places) return null;

  const places = data.places;

  const handleViewOnMap = (p) => {
    if (window.google && window.gMapInstance) {
      const pos = new window.google.maps.LatLng(p.lat, p.lng);
      window.gMapInstance.setCenter(pos);
      window.gMapInstance.setZoom(16);
      
      if (window.tempMarker) {
        window.tempMarker.setMap(null);
      }
      window.tempMarker = new window.google.maps.Marker({
        position: pos,
        map: window.gMapInstance,
        title: p.name,
        animation: window.google.maps.Animation.DROP
      });
      
      const infoWindow = new window.google.maps.InfoWindow({
        content: `<div style="color: black; font-weight: bold; padding: 4px;">${p.name}</div>`
      });
      infoWindow.open(window.gMapInstance, window.tempMarker);
    } else if (window.osmMapInstance) {
      const map = window.osmMapInstance;
      map.setView([p.lat, p.lng], 16);
      if (window.tempMarker) {
        map.removeLayer(window.tempMarker);
      }
      if (window.L) {
        window.tempMarker = window.L.marker([p.lat, p.lng]).addTo(map)
          .bindPopup(`<div style="color: black; font-weight: bold;">${p.name}</div>`)
          .openPopup();
      }
    }
  };

  const handleGetDirections = (p) => {
    if (onSelectPlace) {
      onSelectPlace(p);
    }
  };

  const categoryEmojis = {
    restaurant: "🍔",
    cafe: "☕",
    hotel: "🏨",
    hospital: "🏥",
    mall: "🛍️",
    atm: "🏧",
    petrol_pump: "⛽",
    bus_stop: "🚌",
    metro_station: "🚇",
    attraction: "🏛️"
  };

  const categoryLabels = {
    restaurant: "Restaurant",
    cafe: "Cafe",
    hotel: "Hotel",
    hospital: "Hospital",
    mall: "Shopping Mall",
    atm: "ATM",
    petrol_pump: "Petrol Pump",
    bus_stop: "Bus Stop",
    metro_station: "Metro Station",
    attraction: "Tourist Attraction"
  };

  return (
    <div style={{
      background: "#121420",
      border: "1.5px solid #3b82f644",
      borderRadius: 12,
      padding: 12,
      marginTop: 8,
      width: "100%"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontSize: 11, fontWeight: 800, color: "#3b82f6", textTransform: "uppercase" }}>
          📍 Explore Near {data.location || "Destination"}
        </div>
        {!data.is_live && (
          <span style={{ fontSize: 8.5, color: "#f5c518", fontWeight: 700, background: "#f5c51815", padding: "2px 6px", borderRadius: 4 }}>
            Estimated Fallback
          </span>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 220, overflowY: "auto", paddingRight: 4 }}>
        {places.length === 0 ? (
          <div style={{ fontSize: 11, color: "#64748b", textAlign: "center", padding: "10px 0" }}>
            No nearby options found.
          </div>
        ) : (
          places.map((p, idx) => (
            <div key={idx} style={{
              background: "#08090f",
              borderRadius: 10,
              padding: 10,
              fontSize: 11,
              border: "1px solid #1e2440",
              display: "flex",
              flexDirection: "column",
              gap: 6
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <div style={{ fontWeight: 800, color: "#ffffff", fontSize: 12 }}>{p.name}</div>
                  <div style={{ fontSize: 9.5, color: "#64748b", marginTop: 2 }}>
                    {categoryEmojis[p.category] || "📍"} {categoryLabels[p.category] || p.category}
                  </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                  <span style={{ fontWeight: 700, color: "#3b82f6", fontSize: 11 }}>
                     {p.distance_km || p.distance} km
                  </span>
                  {p.rating && (
                    <span style={{ color: "#f5c518", fontWeight: 700, fontSize: 9.5 }}>
                      ⭐ {p.rating}
                    </span>
                  )}
                  {p.open_now !== undefined && p.open_now !== null && (
                    <span style={{ fontSize: 8.5, color: p.open_now ? "#10b981" : "#ef4444", fontWeight: 800 }}>
                      {p.open_now ? "🟢 OPEN NOW" : "🔴 CLOSED"}
                    </span>
                  )}
                </div>
              </div>

              {p.address && (
                <div style={{ fontSize: 10, color: "#94a3b8", display: "flex", gap: 4, alignItems: "center" }}>
                  <span>📍</span>
                  <span style={{ textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", maxWidth: 220 }}>
                    {p.address}
                  </span>
                </div>
              )}

              <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                <button
                  onClick={() => handleViewOnMap(p)}
                  style={{
                    flex: 1,
                    padding: "5px 10px",
                    background: "#1e293b",
                    border: "1px solid #334155",
                    borderRadius: 6,
                    color: "#ffffff",
                    fontSize: 9.5,
                    fontWeight: 700,
                    cursor: "pointer",
                    fontFamily: "inherit"
                  }}
                >
                  View on Map 🗺️
                </button>
                <button
                  onClick={() => handleGetDirections(p)}
                  style={{
                    flex: 1,
                    padding: "5px 10px",
                    background: "linear-gradient(135deg, #3b82f6, #1d4ed8)",
                    border: "none",
                    borderRadius: 6,
                    color: "#ffffff",
                    fontSize: 9.5,
                    fontWeight: 700,
                    cursor: "pointer",
                    fontFamily: "inherit"
                  }}
                >
                  Get Directions ➡️
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function ChatbotWidget({ triggerSearch, setSelected, setSrc, setDst, src }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I am your Commuter Assistant. I can help you plan your journey, find options matching your budget, check rain forecast impact, or compare transit vs. driving. Try asking: 'How long does it take from Majestic to Silk Board?' or 'Will it rain at 4 PM?'",
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading, open]);

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    // Add user message
    const userMsg = { sender: "user", text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    let latitude = null;
    let longitude = null;
    
    const lowerText = text.toLowerCase();
    const needsLocation = lowerText.includes("near me") || lowerText.includes("restaurants near") || lowerText.includes("cafe near") || lowerText.includes("hospital near") || lowerText.includes("places near");

    if (needsLocation && navigator.geolocation) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            timeout: 5000,
            maximumAge: 60000
          });
        });
        latitude = position.coords.latitude;
        longitude = position.coords.longitude;
      } catch (err) {
        console.warn("Geolocation query error:", err);
      }
    }

    try {
      const response = await fetch(`${API_BASE}/api/chatbot/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history: messages.map(m => ({ sender: m.sender, text: m.text })),
          latitude,
          longitude
        }),
      });

      if (!response.ok) throw new Error("Server error");
      const data = await response.json();

      setMessages(prev => [...prev, {
        sender: "bot",
        text: data.text,
        intent: data.intent,
        parameters: data.parameters,
        embedded_data: data.embedded_data
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: "bot",
        text: "Sorry, I'm having trouble connecting right now. Please try again.",
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRoute = (mode, embedded_data) => {
    const stops = embedded_data.stops;
    if (stops && stops.length >= 2) {
      const source = stops[0];
      const destination = stops[stops.length - 1];
      triggerSearch(source, destination).then(() => {
        setSelected(mode);
      });
    }
  };

  const handleSelectPlace = (p, embedded_data) => {
    let startLoc = src || "Majestic";
    if (embedded_data && embedded_data.source) {
      startLoc = embedded_data.source;
    }
    const destLoc = `${p.name} (${p.lat}, ${p.lng})`;
    if (setSrc) setSrc(startLoc);
    if (setDst) setDst(destLoc);
    triggerSearch(startLoc, destLoc);
  };

  const handleCardClick = (msg) => {
    const embed = msg.embedded_data;
    const params = msg.parameters;

    let source = params?.source || embed?.source || embed?.from_stop;
    let destination = params?.destination || embed?.destination || embed?.to_stop;

    if (!source || !destination) {
      source = params?.source || "Majestic";
      destination = params?.destination || "Indiranagar";
    }

    triggerSearch(source, destination).then(() => {
      if (embed?.mode) {
        setSelected(embed.mode);
      }
    });
  };

  const chips = [
    { text: "Ola fare from Majestic to Indiranagar" },
    { text: "Nearest bus stop to Bangalore Palace" },
    { text: "Fuel cost: Whitefield to Electronic City by car" },
    { text: "Will it rain at 5 PM today?" },
    { text: "Traffic from MG Road to Hebbal?" },
    { text: "Cheapest route under ₹50 from HSR to Majestic" }
  ];

  return (
    <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 9999, fontFamily: "inherit" }}>
      {/* Floating Button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          style={{
            width: 60,
            height: 60,
            borderRadius: "50%",
            background: "linear-gradient(135deg, #f97316, #8b5cf6)",
            border: "none",
            boxShadow: "0 8px 32px rgba(249, 115, 22, 0.4)",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
            position: "relative"
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.1) translateY(-3px)";
            e.currentTarget.style.boxShadow = "0 12px 40px rgba(249, 115, 22, 0.5)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "0 8px 32px rgba(249, 115, 22, 0.4)";
          }}
        >
          <Ic n="chat" s={28} c="white" sw={2} />
          <span style={{ position: "absolute", top: 2, right: 2, width: 12, height: 12, borderRadius: "50%", background: C.green, border: "2px solid #08090f" }} />
        </button>
      )}

      {/* Chat Window */}
      {open && (
        <div style={{
          width: 400,
          height: 580,
          background: C.surface,
          border: `1px solid ${C.border2}`,
          borderRadius: 20,
          boxShadow: "0 16px 48px rgba(0, 0, 0, 0.7)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          backdropFilter: "blur(20px)",
          animation: "fadeIn 0.25s ease-out"
        }}>
          {/* Header */}
          <div style={{
            padding: "16px 20px",
            background: "linear-gradient(135deg, #151929, #0f1120)",
            borderBottom: `1.5px solid ${C.border}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #f97316, #8b5cf6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                🤖
              </div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 800, color: C.text }}>Commuter Assistant</div>
                <div style={{ fontSize: 11, color: C.green, display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.green }} /> All modes • Online
                </div>
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              style={{
                background: "none",
                border: "none",
                color: C.muted,
                cursor: "pointer",
                padding: 4,
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}
            >
              <Ic n="x" s={18} />
            </button>
          </div>

          {/* Messages */}
          <div
            ref={scrollRef}
            style={{
              flex: 1,
              padding: "20px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 16
            }}
          >
            {messages.map((m, idx) => (
              <div key={idx} style={{
                display: "flex",
                justifyContent: m.sender === "user" ? "flex-end" : "flex-start",
                alignItems: "flex-end",
                gap: 8
              }}>
                {m.sender === "bot" && (
                  <div style={{ fontSize: 16, marginBottom: 4 }}>🤖</div>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: "80%" }}>
                  <div style={{
                    padding: "12px 16px",
                    borderRadius: m.sender === "user" ? "18px 18px 2px 18px" : "18px 18px 18px 2px",
                    background: m.sender === "user" ? "linear-gradient(135deg, #f97316, #ea580c)" : C.card,
                    border: m.sender === "user" ? "none" : `1px solid ${C.border}`,
                    color: C.text,
                    fontSize: 13,
                    lineHeight: 1.5,
                    whiteSpace: "pre-line",
                    boxShadow: m.sender === "user" ? "0 4px 12px rgba(249, 115, 22, 0.2)" : "none"
                  }}>
                    {m.text}
                  </div>

                  {m.sender === "bot" && m.embedded_data && m.embedded_data.type === "comparison" && (
                    <>
                      <ComparisonDashboard data={m.embedded_data} onSelectRoute={(mode) => handleSelectRoute(mode, m.embedded_data)} />
                      
                      {/* Explore nearby category buttons row */}
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                        {[
                          { label: "🏛️ Tourist Spots", cat: "attraction" },
                          { label: "🍔 Restaurants", cat: "restaurant" },
                          { label: "☕ Cafes", cat: "cafe" },
                          { label: "🏨 Hotels", cat: "hotel" },
                          { label: "🛍️ Shopping", cat: "mall" },
                          { label: "🏥 Hospitals", cat: "hospital" }
                        ].map((item) => (
                          <button
                            key={item.cat}
                            onClick={() => {
                              const query = `Explore ${item.cat} near ${m.embedded_data.destination}`;
                              sendMessage(query);
                            }}
                            style={{
                              padding: "6px 12px",
                              background: "#1e293b",
                              border: "1px solid #334155",
                              borderRadius: 20,
                              color: "#e2e8f0",
                              fontSize: 10.5,
                              fontWeight: 700,
                              cursor: "pointer",
                              transition: "all 0.2s",
                              fontFamily: "inherit"
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.background = "#273549"}
                            onMouseLeave={(e) => e.currentTarget.style.background = "#1e293b"}
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>

                      {/* Display places if this is a combined travel + nearby query */}
                      {m.embedded_data.places && m.embedded_data.places.length > 0 && (
                        <NearbyPlacesDashboard
                          data={{
                            places: m.embedded_data.places,
                            location: m.embedded_data.destination,
                            is_live: !m.embedded_data.is_estimated
                          }}
                          onSelectPlace={(p) => handleSelectPlace(p, m.embedded_data)}
                        />
                      )}
                    </>
                  )}

                  {m.sender === "bot" && m.embedded_data && m.embedded_data.type === "nearby_places" && (
                    <NearbyPlacesDashboard data={m.embedded_data} onSelectPlace={(p) => handleSelectPlace(p, m.embedded_data)} />
                  )}

                  {/* Embedded cards for different intents */}
                  {m.sender === "bot" && m.embedded_data && m.embedded_data.type !== "comparison" && m.embedded_data.type !== "nearby_places" && m.intent !== "ride_cost" && m.intent !== "fuel_cost" && m.intent !== "nearest_stops" && m.intent !== "traffic_query" && (
                    <div
                      onClick={() => handleCardClick(m)}
                      style={{
                        background: `${MC[m.embedded_data.mode]?.color || C.accent}14`,
                        border: `1.5px solid ${(MC[m.embedded_data.mode]?.color || C.accent)}44`,
                        borderRadius: 12,
                        padding: 12,
                        cursor: "pointer",
                        display: "flex",
                        flexDirection: "column",
                        gap: 4,
                        transition: "all 0.2s",
                        marginTop: 4,
                        boxShadow: "0 4px 12px rgba(0,0,0,0.15)"
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = "translateY(-2px)";
                        e.currentTarget.style.borderColor = MC[m.embedded_data.mode]?.color || C.accent;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = "none";
                        e.currentTarget.style.borderColor = `${(MC[m.embedded_data.mode]?.color || C.accent)}44`;
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: 11, fontWeight: 800, color: MC[m.embedded_data.mode]?.color || C.accent, textTransform: "uppercase" }}>
                          {MC[m.embedded_data.mode]?.label || "Recommended Option"}
                        </span>
                        <span style={{ fontSize: 12, fontWeight: 900, color: C.text }}>
                          ₹{m.embedded_data.cost}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, fontWeight: 700, color: C.text }}>
                        {m.parameters?.source || m.embedded_data.from_stop || "Trip"} → {m.parameters?.destination || m.embedded_data.to_stop || "Destination"}
                      </div>
                      <div style={{ fontSize: 11, color: C.muted, display: "flex", justifyContent: "space-between" }}>
                        <span>⏱️ {m.embedded_data.time} mins</span>
                        {m.embedded_data.transfers !== undefined && (
                          <span>🔄 {m.embedded_data.transfers} transfer(s)</span>
                        )}
                      </div>
                      <div style={{ fontSize: 10, color: C.accent, fontWeight: 800, textAlign: "right", marginTop: 4 }}>
                        Click to draw route on map 🗺️
                      </div>
                    </div>
                  )}

                  {/* Ride cost card */}
                  {m.sender === "bot" && m.intent === "ride_cost" && m.embedded_data && (
                    <div style={{
                      background: "#1a1530",
                      border: "1.5px solid #8b5cf644",
                      borderRadius: 12,
                      padding: 12,
                      marginTop: 4,
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: "#8b5cf6", textTransform: "uppercase", marginBottom: 6 }}>Ride-Hailing Estimate</div>
                      <div style={{ fontSize: 12, color: C.text, fontWeight: 700, marginBottom: 4 }}>
                        {m.parameters?.source} → {m.parameters?.destination}
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
                        {[["ola", "Ola", "#f5c518"], ["uber", "Uber", "#e0e0e0"], ["namma_yatri", "Namma Yatri", "#22c55e"], ["rapido", "Rapido", "#3b82f6"]].map(([pkey, label, clr]) =>
                          m.embedded_data.providers?.[pkey] && (
                            <div key={pkey} style={{ background: clr + "18", borderRadius: 8, padding: "6px 8px", border: `1px solid ${clr}33` }}>
                              <div style={{ fontSize: 10, fontWeight: 800, color: clr }}>{label}</div>
                              <div style={{ fontSize: 11, color: C.text }}>₹{m.embedded_data.providers[pkey][0]?.fare_min}–{m.embedded_data.providers[pkey][0]?.fare_max}</div>
                            </div>
                          )
                        )}
                      </div>
                      <div style={{ fontSize: 10, color: C.muted, marginTop: 6 }}>~{m.embedded_data.distance_km?.toFixed(1)} km • ~{m.embedded_data.duration_min && parseInt(m.embedded_data.duration_min)} min drive</div>
                    </div>
                  )}

                  {/* Fuel cost card */}
                  {m.sender === "bot" && m.intent === "fuel_cost" && m.embedded_data && (
                    <div style={{
                      background: "#0f1a12",
                      border: "1.5px solid #22c55e44",
                      borderRadius: 12,
                      padding: 12,
                      marginTop: 4,
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: "#22c55e", textTransform: "uppercase", marginBottom: 6 }}>⛽ Fuel Cost Estimate</div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div>
                          <div style={{ fontSize: 18, fontWeight: 900, color: C.text }}>₹{m.embedded_data.cost}</div>
                          <div style={{ fontSize: 10, color: C.muted }}>Fuel cost</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: 14, fontWeight: 700, color: "#22c55e" }}>{m.embedded_data.fuel_litres?.toFixed(2)} L</div>
                          <div style={{ fontSize: 10, color: C.muted }}>Fuel required</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: 13, color: C.text }}>{m.embedded_data.distance_km?.toFixed(1)} km</div>
                          <div style={{ fontSize: 10, color: C.muted }}>Distance</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Nearest stops card */}
                  {m.sender === "bot" && m.intent === "nearest_stops" && m.embedded_data?.nearest && (
                    <div style={{
                      background: "#0d1624",
                      border: "1.5px solid #3b82f644",
                      borderRadius: 12,
                      padding: 12,
                      marginTop: 4,
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 800, color: "#3b82f6", textTransform: "uppercase", marginBottom: 6 }}>📍 Nearby Transit</div>
                      {m.embedded_data.nearest.bmtc?.slice(0, 2).map(([name, dist], i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: C.text, marginBottom: 3 }}>
                          <span>🚌 {name}</span>
                          <span style={{ color: C.muted }}>{dist.toFixed(2)} km</span>
                        </div>
                      ))}
                      {m.embedded_data.nearest.metro?.slice(0, 2).map(([name, dist], i) => (
                        <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: C.text, marginBottom: 3 }}>
                          <span>🚇 {name}</span>
                          <span style={{ color: C.muted }}>{dist.toFixed(2)} km</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Traffic status card */}
                  {m.sender === "bot" && m.intent === "traffic_query" && m.embedded_data?.congestion_level && (
                    <div style={{
                      background: m.embedded_data.congestion_level === "heavy" ? "#1a0a0a" : m.embedded_data.congestion_level === "moderate" ? "#1a150a" : "#0a1a12",
                      border: `1.5px solid ${m.embedded_data.congestion_level === "heavy" ? "#ef444444" : m.embedded_data.congestion_level === "moderate" ? "#f5c51844" : "#22c55e44"}`,
                      borderRadius: 12,
                      padding: 12,
                      marginTop: 4,
                      display: "flex",
                      alignItems: "center",
                      gap: 12
                    }}>
                      <div style={{ fontSize: 28 }}>{m.embedded_data.congestion_level === "heavy" ? "🔴" : m.embedded_data.congestion_level === "moderate" ? "🟡" : "🟢"}</div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 800, color: C.text }}>
                          {m.embedded_data.congestion_level === "heavy" ? "Heavy Traffic" : m.embedded_data.congestion_level === "moderate" ? "Moderate Traffic" : "Traffic Clear"}
                        </div>
                        {m.embedded_data.drive_time_min && <div style={{ fontSize: 11, color: C.muted }}>Drive time: ~{m.embedded_data.drive_time_min} mins</div>}
                        {m.embedded_data.transit_time && <div style={{ fontSize: 11, color: C.muted }}>Transit: ~{m.embedded_data.transit_time} mins</div>}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <div style={{ fontSize: 16 }}>🤖</div>
                <div style={{
                  padding: "12px 18px",
                  borderRadius: "18px 18px 18px 2px",
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  display: "flex",
                  gap: 4,
                  alignItems: "center"
                }}>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.muted, animation: "bounce 1.4s infinite ease-in-out both" }} />
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.muted, animation: "bounce 1.4s infinite ease-in-out both 0.2s" }} />
                  <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.muted, animation: "bounce 1.4s infinite ease-in-out both 0.4s" }} />
                </div>
              </div>
            )}
          </div>

          {/* Suggestion Chips */}
          <div style={{
            padding: "8px 16px",
            display: "flex",
            flexDirection: "column",
            gap: 6,
            borderTop: `1px solid ${C.border}`,
            background: "#0d0f1a"
          }}>
            <div style={{ fontSize: 10, fontWeight: 700, color: C.muted, textTransform: "uppercase", letterSpacing: "0.03em" }}>Try asking</div>
            <div style={{
              display: "flex",
              gap: 6,
              overflowX: "auto",
              paddingBottom: 4,
              whiteSpace: "nowrap",
              scrollbarWidth: "none"
            }}>
              {chips.map((c, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(c.text)}
                  style={{
                    background: C.card,
                    border: `1px solid ${C.border2}`,
                    borderRadius: 14,
                    padding: "6px 12px",
                    color: C.text,
                    fontSize: 11,
                    fontWeight: 600,
                    cursor: "pointer",
                    fontFamily: "inherit",
                    transition: "all 0.2s"
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = C.accent;
                    e.currentTarget.style.background = "#1c2238";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = C.border2;
                    e.currentTarget.style.background = C.card;
                  }}
                >
                  {c.text}
                </button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            style={{
              padding: 16,
              borderTop: `1px solid ${C.border}`,
              background: "#151929",
              display: "flex",
              gap: 8
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about routes, fares, fuel, stops, traffic..."
              style={{
                flex: 1,
                background: C.bg,
                border: `1px solid ${C.border2}`,
                borderRadius: 12,
                padding: "10px 14px",
                color: C.text,
                fontSize: 13,
                fontFamily: "inherit"
              }}
            />
            <button
              type="submit"
              style={{
                background: "linear-gradient(135deg, #f97316, #ea580c)",
                border: "none",
                borderRadius: 12,
                color: "white",
                padding: "10px 16px",
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "inherit"
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   MAIN APP
───────────────────────────────────────────────────────────── */
function AIRecommendationsPanel({
  recommendations,
  results,
  selected,
  setSelected,
  mc,
  selectedCabVehicle,
  setSelectedCabVehicle,
  selectedMultimodalOption,
  setSelectedMultimodalOption
}) {
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [cabFilter, setCabFilter] = useState("all");
  const [cabProviderFilter, setCabProviderFilter] = useState("all");

  if (!recommendations || recommendations.length === 0) return null;

  const modeColors = {
    bmtc: { color: "#7c3aed", bg: "rgba(124, 58, 237, 0.08)", icon: "bus", label: "BMTC Bus" },
    metro: { color: "#3b82f6", bg: "rgba(59, 130, 246, 0.08)", icon: "metro", label: "Namma Metro" },
    cab: { color: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)", icon: "cab", label: "Cab / Auto" },
    car: { color: "#10b981", bg: "rgba(16, 185, 129, 0.08)", icon: "car", label: "Own Vehicle" },
    multimodal: { color: "#ec4899", bg: "rgba(236, 72, 153, 0.08)", icon: "transfer", label: "Multimodal Transit" }
  };

  const getVehicleCategory = (est) => {
    const key = (est.vehicle_key || "").toLowerCase();
    const name = (est.vehicle_name || "").toLowerCase();
    if (est.parcel || est.vtype === "parcel" || key.includes("parcel")) return "parcel";
    if (est.rental || est.vtype === "rental" || key.includes("hourly") || key.includes("rental")) return "rental";
    if (est.pet || est.vtype === "pet") return "pet";
    if (est.book_any || est.vtype === "book_any" || name === "book any") return "book_any";
    if (key.includes("auto") || name.includes("auto")) return "auto";
    if (est.vtype === "scooty" || key.includes("scooty") || name.includes("scooty")) return "scooty";
    if (est.saver || est.vtype === "saver" || key.includes("saver")) return "saver";
    if (key.includes("bike") || name.includes("bike") || key.includes("moto") || name.includes("moto")) return "bike";
    if (est.vtype === "priority" || key.includes("priority")) return "priority";
    if (est.black || est.vtype === "black") return "black";
    if (
      key.includes("ac_cab") || name.includes("cab (ac)") ||
      key.includes("premier") || name.includes("premier") ||
      key.includes("prime") || name.includes("prime") ||
      key.includes("prime_plus") || name.includes("prime plus") ||
      key.includes("green") || name.includes("green") ||
      key.includes("lux") || name.includes("lux") ||
      key.includes("sedan") || name.includes("sedan") ||
      key.includes("go_ac") || name.includes("go ac") ||
      name.includes("ac cab") || name.includes("ac,")
    ) return "ac_cab";
    if (key.includes("xl") || name.includes("xl") || key.includes("suv") || name.includes("suv")) return "other";
    return "cab";
  };

  const PROVIDER_STYLES = {
    namma_yatri: { bg: "#eab308", text: "#000", label: "Namma Yatri" },
    uber: { bg: "#374151", text: "#fff", label: "Uber" },
    ola: { bg: "#84cc16", text: "#000", label: "Ola" },
    rapido: { bg: "#ea580c", text: "#fff", label: "Rapido" },
  };

  const SPECIAL_BADGES = {
    parcel: { label: "PARCEL", color: "#f59e0b", icon: "📦" },
    rental: { label: "HOURLY", color: "#8b5cf6", icon: "⏱️" },
    priority: { label: "PRIORITY", color: "#06b6d4", icon: "⚡" },
    pet: { label: "PET", color: "#f472b6", icon: "🐾" },
    saver: { label: "SAVER", color: "#22c55e", icon: "💰" },
    black: { label: "BLACK", color: "#a3a3a3", icon: "💎" },
    scooty: { label: "SCOOTY", color: "#fb923c", icon: "🛵" },
    book_any: { label: "BOOK ANY", color: "#eab308", icon: "⚡🚗" },
  };

  const categories = [
    { id: "all", label: "All Types", icon: "🌐" },
    { id: "auto", label: "Auto", icon: "🛺" },
    { id: "book_any", label: "Book Any", icon: "⚡🚗" },
    { id: "cab", label: "Cab", icon: "🚗" },
    { id: "ac_cab", label: "AC Cab", icon: "❄️" },
    { id: "bike", label: "Bike", icon: "🏍️" },
    { id: "scooty", label: "Scooty", icon: "🛵" },
    { id: "priority", label: "Priority", icon: "⚡" },
    { id: "black", label: "Black", icon: "💎" },
    { id: "pet", label: "Pet", icon: "🐾" },
    { id: "saver", label: "Saver", icon: "💰" },
    { id: "rental", label: "Hourly", icon: "⏱️" },
    { id: "parcel", label: "Parcel", icon: "📦" },
    { id: "other", label: "Other", icon: "🚙" },
  ];

  return (
    <div style={{
      background: "#ffffff",
      border: `1.5px solid #ede9fe`,
      borderRadius: 24,
      padding: 24,
      marginBottom: 24,
      boxShadow: "rgba(124, 58, 237, 0.04) 0 10px 30px",
      animation: "fadeIn 0.5s ease-out both"
    }}>
      {/* Title */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: "linear-gradient(135deg, #7c3aed, #ec4899)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "rgba(124, 58, 237, 0.2) 0 4px 10px"
          }}>
            <span style={{ fontSize: 18 }}>🤖</span>
          </div>
          <div>
            <div style={{ fontWeight: 900, fontSize: 16, color: "#1e1b24", letterSpacing: "-0.02em", lineHeight: "1.1" }}>U-Transit AI Smart Ranker</div>
            <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 700, marginTop: 3 }}>Explainable AI & Top-K Routing</div>
          </div>
        </div>
        <div style={{ background: "rgba(124, 58, 237, 0.08)", color: "#7c3aed", padding: "6px 12px", borderRadius: 10, fontSize: 11, fontWeight: 700 }}>
          ✨ Gemini Powered
        </div>
      </div>

      {/* List of recommendations */}
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {recommendations.slice(0, 4).map((rec, idx) => {
          const config = modeColors[rec.mode] || { color: C.accent, bg: "rgba(124, 58, 237, 0.08)", icon: "bus", label: rec.mode };
          const isSelected = selected === rec.mode;
          const isExpanded = expandedIndex === idx;

          // Find actual time & cost from results
          const actualData = results[rec.mode] || {};
          const time = actualData.time || 0;
          const cost = actualData.cost || 0;
          const transfers = actualData.transfers || 0;

          const providerOptions = [
            { id: "all", label: "All Providers", icon: "🌐", color: config.color },
            { id: "namma_yatri", label: "Namma Yatri", icon: "🛺", color: "#eab308" },
            { id: "ola", label: "Ola", icon: "🚗", color: "#84cc16" },
            { id: "uber", label: "Uber", icon: "🚗", color: "#e2e8f0" },
            { id: "rapido", label: "Rapido", icon: "🏍️", color: "#ea580c" },
          ];

          return (
            <div
              key={rec.mode}
              style={{
                background: "#ffffff",
                border: `1.5px solid ${isSelected ? "#7c3aed" : "#eef0f6"}`,
                borderRadius: 20,
                padding: "16px 20px",
                transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
                cursor: "pointer",
                boxShadow: isSelected ? "0 10px 25px -5px rgba(124, 58, 237, 0.08), 0 8px 10px -6px rgba(124, 58, 237, 0.08)" : "none",
                animation: "fadeIn 0.5s ease-out both",
                animationDelay: `${idx * 0.08}s`
              }}
              onClick={() => setSelected(rec.mode)}
              onMouseEnter={e => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.borderColor = isSelected ? "#7c3aed" : "rgba(124, 58, 237, 0.3)";
                e.currentTarget.style.boxShadow = "0 12px 24px -10px rgba(124, 58, 237, 0.15)";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.borderColor = isSelected ? "#7c3aed" : "#eef0f6";
                e.currentTarget.style.boxShadow = isSelected ? "0 10px 25px -5px rgba(124, 58, 237, 0.08)" : "none";
              }}
            >
              {/* Main row */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                  {/* Rank badge */}
                  <div style={{
                    width: 28, height: 28, borderRadius: "50%",
                    background: idx === 0 ? "linear-gradient(135deg, #fef08a, #fef9c3)" : "#f3f4f6",
                    color: idx === 0 ? "#ca8a04" : "#4b5563",
                    border: `1px solid ${idx === 0 ? "#fde047" : "#e5e7eb"}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontWeight: 900, fontSize: 12, flexShrink: 0
                  }}>
                    #{idx + 1}
                  </div>

                  {/* Mode Icon Container */}
                  <div style={{
                    width: 44, height: 44, borderRadius: 12,
                    background: config.bg,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0
                  }}>
                    <Ic n={config.icon} s={22} c={config.color} sw={2} />
                  </div>

                  {/* Details Block */}
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontWeight: 900, fontSize: 15, color: "#1e1b24" }}>
                        {config.label}
                      </span>
                      <span style={{
                        background: `${config.color}15`,
                        color: config.color,
                        padding: "3px 8px",
                        borderRadius: 6,
                        fontSize: 9.5,
                        fontWeight: 800,
                        textTransform: "uppercase",
                        letterSpacing: "0.02em"
                      }}>
                        {rec.score}% MATCH
                      </span>
                    </div>

                    {/* Stats List */}
                    <div style={{ display: "flex", gap: 16, color: "#64748b", fontSize: 12, marginTop: 6, fontWeight: 600, alignItems: "center" }}>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>💰 ₹{cost}</span>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>🕒 {time} mins</span>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>🎯 {transfers} transfer(s)</span>
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>🌿 {rec.emissions || 0}g CO₂</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedIndex(isExpanded ? null : idx);
                    }}
                    style={{
                      background: "none", border: "none", color: C.muted,
                      fontSize: 12, fontWeight: 700, cursor: "pointer",
                      padding: "4px 8px", borderRadius: 6, display: "flex",
                      alignItems: "center", gap: 4, fontFamily: "inherit",
                      transition: "color 0.2s"
                    }}
                    onMouseEnter={e => e.currentTarget.style.color = "#1e1b24"}
                    onMouseLeave={e => e.currentTarget.style.color = C.muted}
                  >
                    <span>Show Details</span>
                    <span style={{ 
                      display: "inline-block", 
                      transition: "transform 0.2s ease",
                      transform: isExpanded ? "rotate(180deg)" : "none" 
                    }}>▾</span>
                  </button>

                  {/* Circular selection button */}
                  <div
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelected(rec.mode);
                    }}
                    style={{
                      width: 26, height: 26, borderRadius: "50%",
                      background: isSelected ? "#7c3aed" : "#ffffff",
                      border: `2px solid ${isSelected ? "#7c3aed" : "#d1d5db"}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      cursor: "pointer", transition: "all 0.2s"
                    }}
                  >
                    {isSelected ? (
                      <Ic n="arrow" s={10} c="white" sw={3} />
                    ) : (
                      <div style={{ width: 6, height: 6, borderRadius: "50%", background: "transparent" }} />
                    )}
                  </div>
                </div>
              </div>

              {/* Explanation Card */}
              <div style={{
                marginTop: 12,
                fontSize: 12.5,
                lineHeight: "18px",
                color: "#4b5563",
                background: "#ffffff",
                padding: "10px 14px",
                borderRadius: 12,
                border: "1px solid #f1f1f5",
                borderLeft: `4px solid ${config.color || C.accent}`,
                fontWeight: 500
              }}>
                <strong>Why recommended:</strong> {rec.explanation}
              </div>

              {/* Inline cab option details (rendered inside ranker card if expanded and mode is cab) */}
              {isExpanded && rec.mode === "cab" && actualData.all_estimates && (
                <div onClick={e => e.stopPropagation()} style={{
                  marginTop: 14,
                  padding: "14px 16px",
                  borderTop: `1px solid ${C.border}`,
                  background: C.bg + "33",
                  borderRadius: 14
                }}>
                  <div style={{ fontSize: 11, fontWeight: 800, color: C.muted, marginBottom: 10, letterSpacing: "0.05em" }}>
                    AVAILABLE VEHICLES & PROVIDERS
                  </div>

                  {/* Category Filter Pills */}
                  <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 6, marginBottom: 8, scrollbarWidth: "none" }}>
                    {categories.map(cat => {
                      const count = actualData.all_estimates.filter(est =>
                        (cat.id === "all" || getVehicleCategory(est) === cat.id) &&
                        (cabProviderFilter === "all" || est.provider_key === cabProviderFilter)
                      ).length;

                      if (count === 0 && cat.id !== "all") return null;

                      const isCatActive = cabFilter === cat.id;
                      return (
                        <button
                          key={cat.id}
                          onClick={() => setCabFilter(cat.id)}
                          style={{
                            background: isCatActive ? config.color + "22" : C.surface,
                            border: `1.5px solid ${isCatActive ? config.color : C.border2}`,
                            borderRadius: 20,
                            padding: "6px 12px",
                            color: isCatActive ? config.color : C.muted,
                            fontSize: 11,
                            fontWeight: 700,
                            cursor: "pointer",
                            whiteSpace: "nowrap",
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                            transition: "all 0.15s",
                            fontFamily: "inherit"
                          }}
                        >
                          <span>{cat.icon}</span>
                          <span>{cat.label}</span>
                          <span style={{
                            fontSize: 9,
                            background: isCatActive ? config.color + "44" : C.border2,
                            color: isCatActive ? config.color : C.muted,
                            borderRadius: 10,
                            padding: "1px 5px",
                            marginLeft: 2
                          }}>{count}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Provider Filter Pills */}
                  <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 10, marginBottom: 12, scrollbarWidth: "none" }}>
                    {providerOptions.map(prov => {
                      const count = actualData.all_estimates.filter(est =>
                        (prov.id === "all" || est.provider_key === prov.id) &&
                        (cabFilter === "all" || getVehicleCategory(est) === cabFilter)
                      ).length;

                      if (count === 0 && prov.id !== "all") return null;

                      const isProvActive = cabProviderFilter === prov.id;
                      const activeColor = prov.color;
                      return (
                        <button
                          key={prov.id}
                          onClick={() => setCabProviderFilter(prov.id)}
                          style={{
                            background: isProvActive ? activeColor + "22" : C.surface,
                            border: `1.5px solid ${isProvActive ? activeColor : C.border2}`,
                            borderRadius: 20,
                            padding: "6px 12px",
                            color: isProvActive ? activeColor : C.muted,
                            fontSize: 11,
                            fontWeight: 700,
                            cursor: "pointer",
                            whiteSpace: "nowrap",
                            display: "flex",
                            alignItems: "center",
                            gap: 4,
                            transition: "all 0.15s",
                            fontFamily: "inherit"
                          }}
                        >
                          <span>{prov.icon}</span>
                          <span>{prov.label}</span>
                          <span style={{
                            fontSize: 9,
                            background: isProvActive ? activeColor + "44" : C.border2,
                            color: isProvActive ? activeColor : C.muted,
                            borderRadius: 10,
                            padding: "1px 5px",
                            marginLeft: 2
                          }}>{count}</span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Vehicle list */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 8, maxHeight: 220, overflowY: "auto", paddingRight: 4 }}>
                    {actualData.all_estimates.filter(est => {
                      const matchesType = cabFilter === "all" || getVehicleCategory(est) === cabFilter;
                      const matchesProvider = cabProviderFilter === "all" || est.provider_key === cabProviderFilter;
                      return matchesType && matchesProvider;
                    }).map((est, eIdx) => {
                      const isVehSelected = selectedCabVehicle &&
                        selectedCabVehicle.provider_key === est.provider_key &&
                        selectedCabVehicle.vehicle_key === est.vehicle_key;

                      const pStyle = PROVIDER_STYLES[est.provider_key] || { bg: C.surface, text: C.text, label: est.provider };
                      const isUnavailable = est.is_vehicle_available === false;
                      const specialBadge = SPECIAL_BADGES[getVehicleCategory(est)] || null;

                      return (
                        <button
                          key={eIdx}
                          onClick={() => {
                            if (isUnavailable) return;
                            setSelectedCabVehicle(est);
                            setSelected("cab");
                          }}
                          style={{
                            background: isUnavailable ? C.surface + "88" : isVehSelected ? C.surface : C.card,
                            border: `1.5px solid ${isUnavailable ? C.border : isVehSelected ? config.color : C.border}`,
                            borderRadius: 12,
                            padding: "10px 14px",
                            cursor: isUnavailable ? "not-allowed" : "pointer",
                            width: "100%",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            transition: "all 0.15s",
                            opacity: isUnavailable ? 0.55 : 1,
                            boxShadow: isVehSelected ? `0 4px 16px ${config.color}15` : "none",
                            fontFamily: "inherit"
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                            <div style={{ fontSize: 22 }}>{est.icon || "🚗"}</div>
                            <div>
                              <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                                <span style={{ fontSize: 13, fontWeight: 800 }}>{est.vehicle_name}</span>
                                <span style={{
                                  fontSize: 8,
                                  background: pStyle.bg,
                                  color: pStyle.text,
                                  padding: "1px 5px",
                                  borderRadius: 4,
                                  fontWeight: 700
                                }}>{pStyle.label.toUpperCase()}</span>
                                {specialBadge && (
                                  <span style={{
                                    fontSize: 8,
                                    background: specialBadge.color + "18",
                                    color: specialBadge.color,
                                    padding: "1px 5px",
                                    borderRadius: 4,
                                    fontWeight: 700
                                  }}>{specialBadge.icon} {specialBadge.label}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <div style={{ fontSize: 14, fontWeight: 900, color: isVehSelected ? config.color : C.text }}>
                              ₹{est.cost}
                            </div>
                            <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                              ⏱ {est.time} min
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Inline multimodal option details (rendered inside ranker card if expanded and mode is multimodal) */}
              {isExpanded && rec.mode === "multimodal" && actualData.all_options && (
                <div onClick={e => e.stopPropagation()} style={{
                  marginTop: 14,
                  padding: "14px 16px",
                  borderTop: `1px solid ${C.border}`,
                  background: C.bg + "33",
                  borderRadius: 14
                }}>
                  <div style={{ fontSize: 11, fontWeight: 800, color: C.muted, marginBottom: 10, letterSpacing: "0.05em" }}>
                    SELECT MULTIMODAL COMBINATION
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, maxHeight: 220, overflowY: "auto", paddingRight: 4 }}>
                    {actualData.all_options.map((opt, oidx) => {
                      const isOptSelected = selectedMultimodalOption && selectedMultimodalOption.combination_type === opt.combination_type;
                      return (
                        <button
                          key={oidx}
                          onClick={() => {
                            setSelectedMultimodalOption(opt);
                            setSelected("multimodal");
                          }}
                          style={{
                            background: isOptSelected ? config.color + "14" : C.surface,
                            border: `1.5px solid ${isOptSelected ? config.color : C.border2}`,
                            borderRadius: 10,
                            padding: "10px 14px",
                            width: "100%",
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            transition: "all 0.15s",
                            boxShadow: isOptSelected ? `0 4px 16px ${config.color}15` : "none",
                            fontFamily: "inherit",
                            cursor: "pointer"
                          }}
                        >
                          <div style={{ textAlign: "left" }}>
                            <div style={{ fontSize: 13, fontWeight: 800, color: isOptSelected ? config.color : C.text }}>
                              {opt.combination_label}
                            </div>
                            <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                              {opt.route_summary}
                            </div>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <div style={{ fontSize: 14, fontWeight: 900, color: isOptSelected ? config.color : C.text }}>₹{opt.cost}</div>
                            <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>⏱ {opt.time} min</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Collapsible Utility score breakdown */}
              {isExpanded && (
                <div style={{
                  marginTop: 14,
                  paddingTop: 12,
                  borderTop: "1px solid #eef0f6",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                  animation: "fadeIn 0.2s ease-out"
                }} onClick={(e) => e.stopPropagation()}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 4, letterSpacing: "0.05em" }}>RECOMMENDATION CRITERIA BREAKDOWN</div>
                  {[
                    { label: "⚡ Speed suitability", score: rec.details?.time_score || 0, color: "#3b82f6" },
                    { label: "💰 Cost / Economy", score: rec.details?.cost_score || 0, color: "#10b981" },
                    { label: "🎯 Comfort & Transfers", score: rec.details?.comfort_score || 0, color: "#8b5cf6" },
                    { label: "🌿 Carbon footprint rating", score: rec.details?.eco_score || 0, color: "#059669" },
                    { label: "⛈️ Weather resilience", score: rec.details?.weather_score || 0, color: "#ea580c" }
                  ].map(item => (
                    <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <div style={{ width: 150, fontSize: 11, color: "#4b5563", fontWeight: 600 }}>{item.label}</div>
                      <div style={{ flex: 1, height: 6, background: "#f3f4f6", borderRadius: 3, position: "relative" }}>
                        <div style={{
                          width: `${item.score}%`,
                          height: "100%",
                          background: item.color,
                          borderRadius: 3,
                          transition: "width 0.4s ease-out"
                        }} />
                      </div>
                      <div style={{ width: 30, fontSize: 11, color: "#1e1b24", fontWeight: 700, textAlign: "right" }}>{item.score}%</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LandingPage({ onLoginClick, onSignUpClick }) {
  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  const services = [
    { name: "Bus", desc: "Best coverage", price: "₹ 25 - 50", icon: "bus", color: "#3b82f6", bg: "rgba(59, 130, 246, 0.08)" },
    { name: "Metro", desc: "Fast & reliable", price: "₹ 30 - 60", icon: "metro", color: "#8b5cf6", bg: "rgba(139, 92, 246, 0.08)" },
    { name: "Cabs", desc: "Door to door", price: "₹ 200 - 450", icon: "cab", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.08)" },
    { name: "Personal Vehicle", desc: "Drive your way", price: "₹ 120 - 250*", note: "Toll & Fuel", icon: "car", color: "#10b981", bg: "rgba(16, 185, 129, 0.08)" },
    { name: "Multi-Modal", desc: "Best of all", price: "Save time & money", icon: "transfer", color: "#ec4899", bg: "rgba(236, 72, 153, 0.08)" },
  ];

  const whyChooseUs = [
    { title: "Real-time Updates", desc: "Live tracking of buses, metros and traffic conditions.", icon: "clock", color: "#8b5cf6", bg: "#f5f3ff" },
    { title: "Smart Suggestions", desc: "AI-powered route suggestions for time & cost savings.", icon: "sparkles", color: "#ec4899", bg: "#fdf2f8" },
    { title: "Multi-Modal Options", desc: "Compare and choose the best from multiple transport modes.", icon: "transfer", color: "#10b981", bg: "#ecfdf5" },
    { title: "Fare Estimation", desc: "Get accurate fare estimates across all transport options.", icon: "now", color: "#f59e0b", bg: "#fffbeb" },
    { title: "Easy & Accessible", desc: "User-friendly interface for a seamless travel experience.", icon: "user", color: "#3b82f6", bg: "#eff6ff" },
  ];

  const stats = [
    { val: "10M+", label: "Happy Travelers", icon: "users" },
    { val: "5000+", label: "BMTC Buses", icon: "bus" },
    { val: "2", label: "Metro Lines", icon: "metro" },
    { val: "1000+", label: "Daily Routes", icon: "route" },
    { val: "24/7", label: "AI Support", icon: "chat" },
  ];

  return (
    <div style={{ background: "#f8fafc", color: "#1e293b", fontFamily: "'Plus Jakarta Sans', 'Outfit', sans-serif", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      
      {/* Header */}
      <header style={{
        background: "#ffffff",
        borderBottom: "1px solid #f1f5f9",
        padding: "0 40px",
        height: 76,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxShadow: "0 1px 3px rgba(0,0,0,0.02)"
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => scrollToSection("home")}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 14,
            background: "linear-gradient(135deg, #7c3aed, #ec4899)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "rgba(124, 58, 237, 0.25) 0 8px 16px"
          }}>
            <Ic n="bus" s={20} c="white" sw={2.2} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, color: "#1e1b24", letterSpacing: "-0.02em", lineHeight: "1.2" }}>Bengaluru</div>
            <div style={{ fontSize: 11, color: "#64748b", fontWeight: 600 }}>Transport Navigator</div>
            <div style={{ fontSize: 9, color: "#7c3aed", fontWeight: 700, letterSpacing: "0.05em", marginTop: 2 }}>SMART. CONNECTED.</div>
          </div>
        </div>

        {/* Navigation Links */}
        <nav style={{ display: "flex", alignItems: "center", gap: 28, marginLeft: "auto", marginRight: 40 }}>
          {["Home", "Features", "Routes", "Services", "About Us", "Contact"].map((item) => {
            const sectionMap = {
              "Home": "home",
              "Features": "features",
              "Routes": "services",
              "Services": "services",
              "About Us": "about",
              "Contact": "footer"
            };
            const id = sectionMap[item];
            return (
              <button
                key={item}
                onClick={() => scrollToSection(id)}
                style={{
                  background: "none",
                  border: "none",
                  fontSize: 14,
                  fontWeight: 600,
                  color: item === "Home" ? "#7c3aed" : "#64748b",
                  cursor: "pointer",
                  padding: "8px 4px",
                  borderBottom: item === "Home" ? "2px solid #7c3aed" : "2px solid transparent",
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.currentTarget.style.color = "#7c3aed"; }}
                onMouseLeave={e => { if (item !== "Home") e.currentTarget.style.color = "#64748b"; }}
              >
                {item}
              </button>
            );
          })}
        </nav>

        {/* Authentication Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={onLoginClick}
            style={{
              background: "none",
              border: "1.5px solid #e2e8f0",
              borderRadius: 12,
              padding: "10px 20px",
              color: "#1e293b",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 8,
              transition: "all 0.2s"
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "#7c3aed"; e.currentTarget.style.color = "#7c3aed"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "#e2e8f0"; e.currentTarget.style.color = "#1e293b"; }}
          >
            <Ic n="user" s={14} c="currentColor" /> Login
          </button>
          <button
            onClick={onSignUpClick}
            style={{
              background: "#7c3aed",
              border: "none",
              borderRadius: 12,
              padding: "11px 22px",
              color: "#ffffff",
              fontWeight: 700,
              fontSize: 13,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 8,
              boxShadow: "rgba(124, 58, 237, 0.25) 0 4px 12px",
              transition: "all 0.2s"
            }}
            onMouseEnter={e => { e.currentTarget.style.opacity = 0.95; e.currentTarget.style.transform = "translateY(-1px)"; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "none"; }}
          >
            <Ic n="users" s={14} c="#ffffff" /> Sign Up
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section id="home" style={{
        background: "linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%)",
        padding: "60px 40px",
        position: "relative",
        overflow: "hidden",
        borderBottom: "1px solid #f1f5f9"
      }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1.2fr", gap: 40, maxWidth: 1300, margin: "0 auto", alignItems: "center" }}>
          
          {/* Left Text and Buttons */}
          <div style={{ zIndex: 2 }}>
            <h1 style={{
              fontSize: 48,
              fontWeight: 900,
              color: "#1e1b24",
              lineHeight: 1.15,
              margin: 0,
              letterSpacing: "-0.04em",
              fontFamily: "'Outfit', sans-serif"
            }}>
              Smart Routes.<br />
              <span style={{ color: "#7c3aed", background: "linear-gradient(135deg, #7c3aed 0%, #ec4899 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Better Journeys.</span>
            </h1>
            <p style={{
              color: "#64748b",
              fontSize: 16,
              lineHeight: 1.6,
              margin: "24px 0 32px 0",
              fontWeight: 500
            }}>
              Your all-in-one solution for navigating Bengaluru.<br />
              Find the best routes across bus, metro, cabs and more.
            </p>
            <div style={{ display: "flex", gap: 16 }}>
              <button
                onClick={onSignUpClick}
                style={{
                  background: "#7c3aed",
                  border: "none",
                  color: "#ffffff",
                  borderRadius: 14,
                  padding: "16px 28px",
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  boxShadow: "rgba(124, 58, 237, 0.35) 0 10px 20px",
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.currentTarget.style.opacity = 0.95; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "none"; }}
              >
                Explore Services <Ic n="grid" s={14} c="#ffffff" />
              </button>
              <button
                onClick={onLoginClick}
                style={{
                  background: "#ffffff",
                  border: "2px solid #7c3aed",
                  color: "#7c3aed",
                  borderRadius: 14,
                  padding: "14px 28px",
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "rgba(124, 58, 237, 0.04)"; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#ffffff"; e.currentTarget.style.transform = "none"; }}
              >
                View All Routes <Ic n="route" s={14} c="#7c3aed" />
              </button>
            </div>
          </div>

          {/* Right Image Graphic & Overlay Card */}
          <div style={{ position: "relative", height: 420, display: "flex", alignItems: "center", justifyContent: "center" }}>
            {/* The Cityscape Hero Image */}
            <div style={{
              width: "100%",
              height: "100%",
              borderRadius: 24,
              overflow: "hidden",
              position: "relative",
              boxShadow: "0 20px 40px rgba(0,0,0,0.06)",
              border: "1px solid #ede9fe"
            }}>
              <img src={heroImg} alt="Bengaluru Cityscape" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>

            {/* Floating Info Card */}
            <div style={{
              position: "absolute",
              right: -30,
              top: "50%",
              transform: "translateY(-50%)",
              background: "#ffffff",
              borderRadius: 20,
              width: 240,
              padding: "24px 20px",
              boxShadow: "0 20px 50px rgba(26,22,37,0.1), 0 1px 3px rgba(0,0,0,0.02)",
              border: "1px solid #ede9fe",
              display: "flex",
              flexDirection: "column",
              gap: 16,
              zIndex: 3
            }}>
              {[
                { label: "Live Tracking", sub: "Real-time vehicle updates", icon: "gps", color: "#3b82f6", bg: "#eff6ff" },
                { label: "Best Routes", sub: "Fastest & economical", icon: "route", color: "#8b5cf6", bg: "#f5f3ff" },
                { label: "Multiple Modes", sub: "All transport in one place", icon: "grid", color: "#ec4899", bg: "#fdf2f8" },
                { label: "AI Assistant", sub: "24/7 travel support", icon: "chat", color: "#10b981", bg: "#ecfdf5" },
              ].map(item => (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 10, background: item.bg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <Ic n={item.icon} s={15} c={item.color} sw={2.2} />
                  </div>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 800, color: "#1e293b" }}>{item.label}</div>
                    <div style={{ fontSize: 10, color: "#64748b", marginTop: 2, fontWeight: 500 }}>{item.sub}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Transit Services Section */}
      <section id="services" style={{ padding: "80px 40px", background: "#ffffff" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          
          <h2 style={{ fontSize: 24, fontWeight: 900, color: "#1e1b24", textAlign: "center", marginBottom: 40, fontFamily: "'Outfit', sans-serif", letterSpacing: "-0.02em" }}>
            Explore Transit Options
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 20 }}>
            {services.map(s => (
              <div
                key={s.name}
                onClick={onLoginClick}
                style={{
                  background: "#ffffff",
                  border: "1px solid #f1f5f9",
                  borderRadius: 20,
                  padding: "24px 20px",
                  boxShadow: "rgba(0, 0, 0, 0.01) 0 10px 30px",
                  transition: "all 0.25s ease",
                  cursor: "pointer",
                  position: "relative",
                  display: "flex",
                  flexDirection: "column"
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.transform = "translateY(-4px)";
                  e.currentTarget.style.borderColor = s.color + "40";
                  e.currentTarget.style.boxShadow = "rgba(0, 0, 0, 0.05) 0 15px 35px";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.borderColor = "#f1f5f9";
                  e.currentTarget.style.boxShadow = "rgba(0, 0, 0, 0.01) 0 10px 30px";
                }}
              >
                <div style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  background: s.bg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: 16
                }}>
                  <Ic n={s.icon} s={20} c={s.color} sw={2.2} />
                </div>
                <div style={{ fontSize: 15, fontWeight: 800, color: "#1e1b24" }}>{s.name}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 4, fontWeight: 500 }}>{s.desc}</div>
                
                <div style={{ marginTop: 24, fontSize: 13, fontWeight: 800, color: "#1e1b24" }}>
                  {s.price}
                  {s.note && <span style={{ fontSize: 10, color: "#64748b", fontWeight: 500, display: "block", marginTop: 2 }}>{s.note}</span>}
                </div>

                <div style={{
                  position: "absolute",
                  bottom: 20,
                  right: 20,
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  background: "#f8fafc",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <Ic n="arrow" s={10} c={s.color} sw={2.5} />
                </div>
              </div>
            ))}
          </div>

          {/* Stats Bar Ribbon */}
          <div style={{
            marginTop: 60,
            background: "linear-gradient(135deg, rgba(124, 58, 237, 0.03) 0%, rgba(236, 72, 153, 0.03) 100%)",
            border: "1px solid rgba(124, 58, 237, 0.08)",
            borderRadius: 24,
            padding: "24px 40px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 20
          }}>
            {stats.map(item => (
              <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <Ic n={item.icon} s={16} c="#7c3aed" sw={2.2} />
                <span style={{ fontSize: 14, fontWeight: 500, color: "#475569" }}>
                  <strong style={{ fontSize: 16, fontWeight: 800, color: "#1e1b24", marginRight: 4 }}>{item.val}</strong> {item.label}
                </span>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* Why Choose Us Features Section */}
      <section id="features" style={{ padding: "80px 40px", background: "#f8fafc", borderTop: "1px solid #f1f5f9" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          
          <h2 style={{ fontSize: 24, fontWeight: 900, color: "#1e1b24", textAlign: "center", marginBottom: 40, fontFamily: "'Outfit', sans-serif", letterSpacing: "-0.02em" }}>
            Why Choose Us?
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 20 }}>
            {whyChooseUs.map(f => (
              <div key={f.title} style={{
                background: "#ffffff",
                border: "1px solid #ede9fe",
                borderRadius: 20,
                padding: "24px 20px",
                boxShadow: "rgba(0,0,0,0.01) 0 10px 30px",
                display: "flex",
                flexDirection: "column",
                gap: 12
              }}>
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: 12,
                  background: f.bg,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}>
                  <Ic n={f.icon} s={18} c={f.color} sw={2.2} />
                </div>
                <div style={{ fontSize: 14, fontWeight: 800, color: "#1e1b24" }}>{f.title}</div>
                <div style={{ fontSize: 11, color: "#64748b", lineHeight: 1.5, fontWeight: 500 }}>{f.desc}</div>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* About Us & Move Bengaluru Forward Section */}
      <section id="about" style={{ padding: "80px 40px", background: "#ffffff", borderTop: "1px solid #f1f5f9" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 30 }}>
          
          {/* Card 1: About Us */}
          <div style={{
            background: "#ffffff",
            border: "1px solid #ede9fe",
            borderRadius: 24,
            padding: "36px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.01)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between"
          }}>
            <div>
              <h2 style={{ fontSize: 18, fontWeight: 800, color: "#1e1b24", margin: "0 0 16px 0" }}>About Us</h2>
              <p style={{ fontSize: 13, color: "#64748b", lineHeight: 1.6, fontWeight: 500, margin: 0 }}>
                Bengaluru Transport Navigator is an initiative to make public transportation simple, smart and accessible for everyone.
                Our mission is to connect Bengaluru, one journey at a time.
              </p>
            </div>
            <button
              onClick={onSignUpClick}
              style={{
                marginTop: 28,
                background: "none",
                border: "1.5px solid #7c3aed",
                borderRadius: 12,
                padding: "10px 20px",
                color: "#7c3aed",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
                fontFamily: "inherit",
                alignSelf: "start",
                display: "flex",
                alignItems: "center",
                gap: 8,
                transition: "all 0.2s"
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "rgba(124, 58, 237, 0.04)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "none"; }}
            >
              Learn More About Us <Ic n="arrow" s={12} c="#7c3aed" sw={2.5} />
            </button>
          </div>

          {/* Card 2: Move Bengaluru Forward */}
          <div style={{
            background: "linear-gradient(135deg, #7c3aed 0%, #ec4899 100%)",
            borderRadius: 24,
            padding: "36px",
            color: "#ffffff",
            position: "relative",
            overflow: "hidden",
            boxShadow: "rgba(124, 58, 237, 0.2) 0 10px 30px"
          }}>
            <div style={{ maxWidth: "60%", zIndex: 2, position: "relative" }}>
              <h2 style={{ fontSize: 18, fontWeight: 800, color: "#ffffff", margin: "0 0 8px 0" }}>Move Bengaluru Forward</h2>
              <p style={{ fontSize: 12, opacity: 0.9, lineHeight: 1.5, fontWeight: 500, margin: 0 }}>
                Smart choices. Better cities. Join us in making commutes efficient.
              </p>
            </div>
            {/* Landscape background clip */}
            <div style={{
              position: "absolute",
              bottom: 0,
              right: 0,
              width: "50%",
              height: "70%",
              opacity: 0.8,
              pointerEvents: "none",
              overflow: "hidden",
              borderBottomRightRadius: 24
            }}>
              <img src={heroImg} alt="Bengaluru" style={{ width: "100%", height: "100%", objectFit: "contain", transform: "scale(1.3)", transformOrigin: "bottom right" }} />
            </div>
          </div>

        </div>
      </section>

      {/* Footer */}
      <footer id="footer" style={{
        background: "#0f172a",
        color: "#94a3b8",
        padding: "48px 40px 32px 40px",
        borderTop: "1px solid #1e293b",
        marginTop: "auto"
      }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 24, paddingBottom: 28, borderBottom: "1px solid #1e293b" }}>
            
            {/* Logo */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{
                width: 38,
                height: 38,
                borderRadius: 10,
                background: "linear-gradient(135deg, #7c3aed, #ec4899)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center"
              }}>
                <Ic n="bus" s={18} c="white" sw={2.2} />
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 14, color: "#ffffff", letterSpacing: "-0.01em", lineHeight: "1.2" }}>Bengaluru</div>
                <div style={{ fontSize: 10, color: "#94a3b8", fontWeight: 600 }}>Transport Navigator</div>
              </div>
            </div>

            {/* Links */}
            <div style={{ display: "flex", gap: 24 }}>
              {["Privacy Policy", "Terms of Use", "FAQs", "Help Center"].map(link => (
                <a key={link} href="#" onClick={e => e.preventDefault()} style={{ fontSize: 12, color: "#94a3b8", textDecoration: "none", fontWeight: 600, transition: "color 0.2s" }} onMouseEnter={e => { e.currentTarget.style.color = "#ffffff"; }} onMouseLeave={e => { e.currentTarget.style.color = "#94a3b8"; }}>
                  {link}
                </a>
              ))}
            </div>

            {/* Social Links */}
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: "#475569" }}>Follow Us</span>
              {["facebook", "twitter", "instagram", "youtube"].map(s => (
                <a key={s} href="#" onClick={e => e.preventDefault()} style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "#1e293b",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#7c3aed"; e.currentTarget.style.transform = "translateY(-2px)"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#1e293b"; e.currentTarget.style.transform = "none"; }}
                >
                  <Ic n={s} s={13} c="#ffffff" sw={2.2} />
                </a>
              ))}
            </div>

          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 24, fontSize: 11, color: "#475569", fontWeight: 600 }}>
            <span>© {new Date().getFullYear()} Bengaluru Transport Navigator. All rights reserved.</span>
            <span>Made with ❤️ for Bengaluru</span>
          </div>

        </div>
      </footer>

    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [user, setUser] = useState(localStorage.getItem("username") || null);
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState("login");

  const [page, setPage] = useState("dashboard");
  const [src, setSrc] = useState("");
  const [dst, setDst] = useState("");
  const [time, setTime] = useState("");
  const [pref, setPref] = useState("cost");
  const [results, setResults] = useState(null);
  const [garageOpen, setGarageOpen] = useState(false);
  const [gloveboxOpen, setGloveboxOpen] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [selected, setSelected] = useState(null);
  const [selectedCabVehicle, setSelectedCabVehicle] = useState(null);
  const [selectedMultimodalOption, setSelectedMultimodalOption] = useState(null);
  const [view, setView] = useState("cards");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stops, setStops] = useState({ all: [], bmtc: [], metro: [] });
  const [showAllBuses, setShowAllBuses] = useState(false);
  const [showRouteSearch, setShowRouteSearch] = useState(false);
  const [showTimetable, setShowTimetable] = useState(false);
  const [mapView, setMapView] = useState("gmap"); // "gmap" | "linear"
  const [activeSegmentIndex, setActiveSegmentIndex] = useState(null);

  // Saved vehicles logic
  const [userVehicles, setUserVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState("");

  const [saving, setSaving] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState("");

  const [mapsLoaded, setMapsLoaded] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [useOsm, setUseOsm] = useState(() => {
    if (localStorage.getItem("force_osm") === "true") return true;
    if (localStorage.getItem("force_osm") === "false") return false;
    return true; // Default to OSM until config is loaded
  });

  useEffect(() => {
    const initGmaps = (key) => {
      window.gm_authFailure = () => {
        console.warn("Google Maps authentication failed globally. Falling back to OpenStreetMap.");
        window._osmActive = true;
        window.dispatchEvent(new Event("osm_fallback"));
      };

      if (window.google) { setMapsLoaded(true); return; }
      if (document.getElementById("gmaps-script")) {
        const s = document.getElementById("gmaps-script");
        const handleLoad = () => setMapsLoaded(true);
        s.addEventListener("load", handleLoad);
        return () => s.removeEventListener("load", handleLoad);
      }
      if (!key || key === "YOUR_GOOGLE_MAPS_API_KEY") {
        console.warn("No Google Maps API Key provided globally. Falling back to OpenStreetMap.");
        window._osmActive = true;
        window.dispatchEvent(new Event("osm_fallback"));
        return;
      }
      const s = document.createElement("script");
      s.id = "gmaps-script";
      s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places`;
      s.async = true;
      s.onload = () => setMapsLoaded(true);
      s.onerror = () => {
        console.warn("Google Maps script load failed. Falling back to OpenStreetMap.");
        window._osmActive = true;
        window.dispatchEvent(new Event("osm_fallback"));
      };
      document.head.appendChild(s);
    };

    const handleFallback = () => {
      setUseOsm(true);
    };
    window.addEventListener("osm_fallback", handleFallback);

    fetch(`${API_BASE}/api/config`)
      .then(r => r.json())
      .then(data => {
        if (data.google_maps_api_key) {
          window._backendGmapsKey = data.google_maps_api_key;
        }
        const key = getGoogleMapsKey();
        if (key && key !== "YOUR_GOOGLE_MAPS_API_KEY" && localStorage.getItem("force_osm") !== "true") {
          setUseOsm(false);
          initGmaps(key);
        } else {
          setUseOsm(true);
        }
      })
      .catch(err => {
        console.warn("Could not fetch API config:", err);
        const key = getGoogleMapsKey();
        if (key && key !== "YOUR_GOOGLE_MAPS_API_KEY" && localStorage.getItem("force_osm") !== "true") {
          setUseOsm(false);
          initGmaps(key);
        } else {
          setUseOsm(true);
        }
      });

    return () => window.removeEventListener("osm_fallback", handleFallback);
  }, []);

  // Reset active segment navigation index when selected plan or vehicle changes
  useEffect(() => {
    setActiveSegmentIndex(null);
  }, [selected, selectedCabVehicle, selectedMultimodalOption]);

  useEffect(() => {
    apiStops().then(setStops);
  }, []);

  useEffect(() => {
    if (token) {
      apiGetVehicles(token).then(setUserVehicles).catch(e => {
        console.error(e);
        if (e.message === "Unauthorized") onLogout();
      });
    } else {
      setUserVehicles([]);
      setSelectedVehicle("");
    }
  }, [token, page]);

  const nowTime = () => {
    const n = new Date();
    return `${String(n.getHours()).padStart(2, "0")}:${String(n.getMinutes()).padStart(2, "0")}`;
  };

  const triggerSearch = async (source, destination, customTime = null, prefOverride = null) => {
    if (!source.trim() || !destination.trim()) return;
    setSrc(source);
    setDst(destination);
    if (customTime) setTime(customTime);
    setLoading(true); setError(null); setShowAllBuses(false);
    try {
      const res = await apiCompare(source, destination, customTime || time || nowTime(), prefOverride || pref, selectedVehicle);
      setResults(res.results);
      setRecommendations(res.recommendations || []);

      const topMode = res.recommendations && res.recommendations.length > 0 ? res.recommendations[0].mode : null;
      setSelected(topMode);

      setSelectedCabVehicle(res.results?.cab?.all_estimates?.[0] || null);
      setSelectedMultimodalOption(res.results?.multimodal?.all_options?.[0] || null);
      setView("cards");
      setPage("results");

      if (token) {
        apiSaveJourney(token, {
          from_stop: source,
          to_stop: destination,
          mode: "search",
          cost: 0,
          duration: 0,
          distance: 0.0,
          date: new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
          is_saved: false,
          custom_name: null
        }).catch(console.error);
      }
    } catch (e) {
      setError(`Backend unreachable: ${e.message}. Run: uvicorn backend.main:app --reload --port 8000`);
    } finally { setLoading(false); }
  };

  const search = () => triggerSearch(src, dst);

  const handleSaveJourney = async () => {
    if (!token || !selectedData) return;
    const nameInput = prompt("Enter an optional name for this saved route (e.g., Office, Home, College):");
    if (nameInput === null) return; // User clicked Cancel
    const customName = nameInput.trim();

    setSaving(true);
    setSaveSuccessMsg("");
    try {
      await apiSaveJourney(token, {
        from_stop: src,
        to_stop: dst,
        mode: selected,
        cost: selectedData.cost,
        duration: selectedData.time,
        distance: selectedData.distance,
        date: new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
        is_saved: true,
        custom_name: customName || null
      });
      setSaveSuccessMsg("Journey saved!");
      setTimeout(() => setSaveSuccessMsg(""), 3000);
    } catch (err) {
      alert("Failed to save: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  const onLoginSuccess = (username, userToken) => {
    localStorage.setItem("username", username);
    localStorage.setItem("token", userToken);
    setUser(username);
    setToken(userToken);
    setPage("dashboard");
    setShowAuth(false);
  };

  const onLogout = () => {
    localStorage.removeItem("username");
    localStorage.removeItem("token");
    setUser(null);
    setToken(null);
    setResults(null);
    setRecommendations([]);
    setPage("dashboard");
    setShowAuth(false);
  };

  const selectedData = (() => {
    if (!results || !selected) return null;
    if (selected === "cab" && selectedCabVehicle) {
      return {
        ...results.cab,
        ...selectedCabVehicle,
        segments: selectedCabVehicle.segments,
        guide: selectedCabVehicle.guide,
        cost: selectedCabVehicle.cost,
        time: selectedCabVehicle.time,
        distance: selectedCabVehicle.distance,
      };
    }
    if (selected === "multimodal" && selectedMultimodalOption) {
      return {
        ...results.multimodal,
        ...selectedMultimodalOption,
        segments: selectedMultimodalOption.segments,
        guide: selectedMultimodalOption.guide,
        cost: selectedMultimodalOption.cost,
        time: selectedMultimodalOption.time,
        distance: selectedMultimodalOption.distance,
      };
    }
    return results[selected];
  })();
  const prefs = [
    { k: "cost", e: "💰", l: "Cheapest" },
    { k: "time", e: "⚡", l: "Fastest" },
    { k: "convenience", e: "🎯", l: "Comfortable" },
  ];

  if (!token) {
    if (showAuth) {
      return (
        <AuthScreen 
          onLoginSuccess={onLoginSuccess} 
          onBackToHome={() => setShowAuth(false)} 
          initialMode={authMode} 
        />
      );
    }
    return (
      <LandingPage 
        onLoginClick={() => { setAuthMode("login"); setShowAuth(true); }} 
        onSignUpClick={() => { setAuthMode("signup"); setShowAuth(true); }} 
      />
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'Plus Jakarta Sans', 'Outfit', sans-serif", color: C.text, display: "flex" }}>
      {/* SIDEBAR */}
      <aside style={{
        width: 280,
        background: "#252238",
        borderRight: "1px solid rgba(255, 255, 255, 0.06)",
        display: "flex",
        flexDirection: "column",
        position: "fixed",
        top: 0,
        bottom: 0,
        left: 0,
        zIndex: 100,
        boxShadow: "rgba(0, 0, 0, 0.15) 2px 0 12px 0"
      }}>
        {/* Brand/Logo */}
        <div style={{ padding: "24px 28px 20px", display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 14,
            background: "linear-gradient(135deg, #7c3aed, #ec4899)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "rgba(124, 58, 237, 0.25) 0 8px 16px"
          }}>
            <Ic n="bus" s={20} c="white" sw={2.2} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, color: "#ffffff", letterSpacing: "-0.02em", lineHeight: "1.2" }}>Bengaluru</div>
            <div style={{ fontSize: 11, color: "#8e8a9f", fontWeight: 600 }}>Transport Navigator</div>
            <div style={{ fontSize: 9, color: "#a855f7", fontWeight: 700, letterSpacing: "0.05em", marginTop: 2 }}>SMART. CONNECTED.</div>
          </div>
        </div>

        {/* Sidebar Nav Categories */}
        <div style={{ flex: 1, overflowY: "auto", padding: "0 12px 20px", display: "flex", flexDirection: "column", gap: 16, scrollbarWidth: "none" }}>
          
          {/* MAIN */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#534f6d", textTransform: "uppercase", letterSpacing: "0.08em", padding: "10px 16px 6px" }}>Main</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { id: "dashboard", icon: "home", label: "Home" },
                { id: "plan", icon: "mappin", label: "Plan Journey" },
                { id: "search_routes", icon: "route", label: "Search Routes" },
                { id: "timetable", icon: "clock", label: "Timetable" },
                { id: "map_settings", icon: "sparkles", label: "Map Settings" }
              ].map(n => {
                const isActive = (n.id === "dashboard" && page === "dashboard") || (n.id === "plan" && page === "plan" && !showRouteSearch && !showTimetable);
                const isRouteSearchActive = n.id === "search_routes" && page === "plan" && showRouteSearch;
                const isTimetableActive = n.id === "timetable" && page === "plan" && showTimetable;
                const isItemActive = isActive || isRouteSearchActive || isTimetableActive;

                return (
                  <button
                    key={n.id}
                    onClick={() => {
                      if (n.id === "dashboard") { setPage("dashboard"); }
                      else if (n.id === "plan") { setPage("plan"); setShowRouteSearch(false); setShowTimetable(false); }
                      else if (n.id === "search_routes") { setPage("plan"); setShowRouteSearch(true); setShowAllBuses(false); setShowTimetable(false); }
                      else if (n.id === "timetable") { setPage("plan"); setShowTimetable(true); setShowAllBuses(false); setShowRouteSearch(false); }
                      else if (n.id === "map_settings") { setShowSettings(true); }
                    }}
                    style={{
                      background: isItemActive ? "linear-gradient(90deg, rgba(124, 58, 237, 0.16) 0%, rgba(124, 58, 237, 0.04) 100%)" : "none",
                      border: "none",
                      borderRadius: 12,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      color: isItemActive ? "#ffffff" : "#8e8a9f",
                      fontWeight: isItemActive ? 700 : 600,
                      fontSize: 13.5,
                      padding: "10px 16px",
                      width: "100%",
                      textAlign: "left",
                      fontFamily: "inherit",
                      borderLeft: isItemActive ? "4px solid #a855f7" : "4px solid transparent",
                      transition: "all 0.15s ease"
                    }}
                    onMouseEnter={e => {
                      if (!isItemActive) {
                        e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                        e.currentTarget.style.color = "#ffffff";
                      }
                    }}
                    onMouseLeave={e => {
                      if (!isItemActive) {
                        e.currentTarget.style.background = "none";
                        e.currentTarget.style.color = "#8e8a9f";
                      }
                    }}
                  >
                    <Ic n={n.icon} s={15} c={isItemActive ? "#a855f7" : "#8e8a9f"} />
                    <span>{n.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* TOOLS & SERVICES */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#534f6d", textTransform: "uppercase", letterSpacing: "0.08em", padding: "10px 16px 6px" }}>Tools & Services</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { id: "favourites", icon: "star", label: "Favourites", right: <span style={{ background: "#7c3aed", color: "#ffffff", borderRadius: 10, fontSize: 9, fontWeight: 800, padding: "2px 6px", marginLeft: "auto" }}>3</span> },
                { id: "fare_calculator", icon: "table", label: "Fare Calculator" },
                { id: "stops_info", icon: "gps", label: "Stops Info", sub: "Nearest bus stops" },
                { id: "route_lookup", icon: "route", label: "Route Lookup" },
                { id: "alerts_updates", icon: "bell", label: "Alerts & Updates", sub: "Service & traffic alerts" },
                { id: "weather_alerts", icon: "sparkles", label: "Weather Alerts", sub: "Rain & forecast alerts" }
              ].map(n => {
                return (
                  <button
                    key={n.id}
                    onClick={() => {
                      if (n.id === "favourites") {
                        setPage("dashboard");
                        setTimeout(() => {
                          const el = document.getElementById("saved-places-card");
                          if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
                        }, 100);
                      } else if (n.id === "fare_calculator") {
                        setPage("plan");
                      } else if (n.id === "stops_info") {
                        setPage("plan");
                      } else if (n.id === "route_lookup") {
                        setPage("plan");
                        setShowRouteSearch(true);
                      } else if (n.id === "alerts_updates" || n.id === "weather_alerts") {
                        setPage("dashboard");
                        setTimeout(() => {
                          const el = document.getElementById("travel-alerts-card");
                          if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
                        }, 100);
                      }
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      borderRadius: 12,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      color: "#8e8a9f",
                      fontWeight: 600,
                      fontSize: 13.5,
                      padding: "8px 16px",
                      width: "100%",
                      textAlign: "left",
                      fontFamily: "inherit",
                      borderLeft: "4px solid transparent",
                      transition: "all 0.15s ease"
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                      e.currentTarget.style.color = "#ffffff";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "none";
                      e.currentTarget.style.color = "#8e8a9f";
                    }}
                  >
                    <Ic n={n.icon} s={15} c="#8e8a9f" />
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%" }}>
                        <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{n.label}</span>
                        {n.right || null}
                      </div>
                      {n.sub && <span style={{ fontSize: 9.5, color: "#534f6d", fontWeight: 500, marginTop: 2 }}>{n.sub}</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* MY SPACE */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#534f6d", textTransform: "uppercase", letterSpacing: "0.08em", padding: "10px 16px 6px" }}>My Space</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { id: "my_garage", icon: "car", label: "My Garage", onAdd: () => setGarageOpen(true) },
                { id: "digital_glovebox", icon: "folder", label: "Digital Glovebox", onAdd: () => setGloveboxOpen(true) }
              ].map(n => {
                return (
                  <div
                    key={n.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "4px 8px 4px 16px",
                      borderRadius: 12,
                      transition: "all 0.15s ease"
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = "rgba(255, 255, 255, 0.04)";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "none";
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1, cursor: "pointer" }} onClick={() => {
                      setPage("dashboard");
                      setTimeout(() => {
                        const el = document.getElementById(n.id === "my_garage" ? "my-garage-card" : "digital-glovebox-card");
                        if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
                      }, 100);
                    }}>
                      <Ic n={n.icon} s={15} c="#8e8a9f" />
                      <span style={{ fontSize: 13.5, color: "#8e8a9f", fontWeight: 600 }}>{n.label}</span>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); n.onAdd(); }}
                      style={{
                        background: "none",
                        border: "1px solid #c084fc",
                        borderRadius: 6,
                        color: "#c084fc",
                        fontSize: 9.5,
                        fontWeight: 800,
                        padding: "3px 6px",
                        cursor: "pointer",
                        transition: "all 0.15s"
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = "#a855f7";
                        e.currentTarget.style.color = "#ffffff";
                        e.currentTarget.style.borderColor = "#a855f7";
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = "none";
                        e.currentTarget.style.color = "#c084fc";
                        e.currentTarget.style.borderColor = "#c084fc";
                      }}
                    >
                      + Add
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          {/* OTHER */}
          <div>
            <div style={{ fontSize: 10, fontWeight: 800, color: "#534f6d", textTransform: "uppercase", letterSpacing: "0.08em", padding: "10px 16px 6px" }}>Other</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { id: "help_support", icon: "chat", label: "Help & Support", sub: "FAQs & contact" },
                { id: "settings", icon: "logout", label: "Settings" }
              ].map(n => {
                return (
                  <button
                    key={n.id}
                    onClick={() => {
                      if (n.id === "help_support") {
                        // Open Chatbot
                        const widget = document.getElementById("chatbot-toggle-btn");
                        if (widget) widget.click();
                      } else if (n.id === "settings") {
                        setShowSettings(true);
                      }
                    }}
                    style={{
                      background: "none",
                      border: "none",
                      borderRadius: 12,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      color: C.muted,
                      fontWeight: 600,
                      fontSize: 13.5,
                      padding: "8px 16px",
                      width: "100%",
                      textAlign: "left",
                      fontFamily: "inherit",
                      borderLeft: "4px solid transparent",
                      transition: "all 0.15s ease"
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = "#f9f9fc";
                      e.currentTarget.style.color = "#1e1b24";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = "none";
                      e.currentTarget.style.color = C.muted;
                    }}
                  >
                    <Ic n={n.icon} s={15} c={C.muted} />
                    <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
                      <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{n.label}</span>
                      {n.sub && <span style={{ fontSize: 9.5, color: "#94a3b8", fontWeight: 500, marginTop: 2 }}>{n.sub}</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Cityscape graphic at bottom of sidebar */}
        <div style={{
          margin: "16px",
          padding: "20px 16px 16px 16px",
          background: "linear-gradient(135deg, #302b47 0%, #1f1c2e 100%)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: 20,
          color: "#ffffff",
          position: "relative",
          overflow: "hidden",
          boxShadow: "rgba(0, 0, 0, 0.2) 0 4px 12px",
          height: 110,
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between"
        }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 900, color: "#ffffff", lineHeight: "1.2" }}>Move Bengaluru</div>
            <div style={{ fontSize: 13, fontWeight: 900, color: "#c084fc", lineHeight: "1.2", marginTop: 2 }}>Forward</div>
          </div>
          
          <div style={{ fontSize: 10, color: "#b3afcb", fontWeight: 600, maxWidth: "60%", lineHeight: "1.3" }}>
            Plan smart. Save time. Reduce carbon footprint.
          </div>

          <div style={{
            position: "absolute",
            bottom: 0,
            right: 0,
            width: "45%",
            height: "80%",
            opacity: 0.7,
            pointerEvents: "none",
            overflow: "hidden"
          }}>
            <img src={heroImg} alt="Bengaluru Cityscape" style={{ width: "100%", height: "100%", objectFit: "contain", transform: "scale(1.2)", transformOrigin: "bottom right" }} />
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT CONTAINER */}
      <div style={{ flex: 1, marginLeft: 280, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* TOP HEADER */}
        <header style={{
          height: 70,
          background: "#ffffff",
          borderBottom: `1px solid ${C.border}`,
          padding: "0 40px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          zIndex: 90
        }}>
          {/* Greeting depending on page */}
          <div>
            <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>Welcome Back</div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "#1e1b24", marginTop: 2 }}>{user} 👋</div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* Weather Card */}
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: 12, 
              background: "#f8fafc", 
              border: "1px solid #f1f5f9", 
              padding: "8px 16px", 
              borderRadius: 16 
            }}>
              <span style={{ fontSize: 18 }}>☀️</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "#1e1b24", lineHeight: 1.1 }}>27°C</div>
                <div style={{ fontSize: 10, color: C.muted, fontWeight: 600, marginTop: 2 }}>Partly Cloudy</div>
              </div>
            </div>

            {/* Date/Time Card */}
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              gap: 12, 
              background: "#f8fafc", 
              border: "1px solid #f1f5f9", 
              padding: "8px 16px", 
              borderRadius: 16 
            }}>
              <span style={{ fontSize: 18 }}>🕒</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "#1e1b24", lineHeight: 1.1 }}>{nowTime()}</div>
                <div style={{ fontSize: 10, color: C.muted, fontWeight: 600, marginTop: 2 }}>
                  {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                </div>
              </div>
            </div>
            
            {/* Logout Button */}
            <button
              onClick={onLogout}
              style={{
                background: "rgba(239, 68, 68, 0.08)",
                border: "none",
                borderRadius: 14,
                width: 42,
                height: 42,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                transition: "all 0.2s"
              }}
              onMouseEnter={e => { e.currentTarget.style.background = "#fee2e2"; e.currentTarget.style.transform = "scale(1.04)"; }}
              onMouseLeave={e => { e.currentTarget.style.background = "rgba(239, 68, 68, 0.08)"; e.currentTarget.style.transform = "none"; }}
              title="Logout"
            >
              <Ic n="logout" s={16} c={C.red} sw={2.2} />
            </button>
          </div>
        </header>

        {/* MAIN BODY AREA */}
        <main style={{ padding: "40px", flex: 1, minHeight: "calc(100vh - 70px)", boxSizing: "border-box" }}>

        {/* DASHBOARD */}
        {page === "dashboard" && (
          <Dashboard
            token={token}
            username={user}
            onPlan={() => setPage("plan")}
            onSelectRoute={(from_stop, to_stop) => {
              setSrc(from_stop);
              setDst(to_stop);
              setPage("plan");
            }}
            onLogout={onLogout}
            garageOpen={garageOpen}
            setGarageOpen={setGarageOpen}
            gloveboxOpen={gloveboxOpen}
            setGloveboxOpen={setGloveboxOpen}
          />
        )}

        {/* PLAN */}
        {page === "plan" && (
          <div style={{ display: "grid", gridTemplateColumns: "420px 1fr", gap: 20, alignItems: "start" }}>
            <div>
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 24, fontWeight: 900, letterSpacing: "-0.03em" }}>Plan your journey</div>
                <div style={{ fontSize: 13, color: C.muted, marginTop: 4 }}>BMTC · Metro · Namma Yatri · Personal Vehicle</div>
              </div>

              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 18, padding: 20, marginBottom: 14 }}>
                {/* Stop inputs */}
                <StopInput value={src} onChange={setSrc} placeholder="From — stop or area…" dot={C.green} options={stops.all} showGps={true} />
                <div style={{ display: "flex", justifyContent: "center", margin: "6px 0" }}>
                  <button onClick={() => { setSrc(dst); setDst(src); }} style={{ width: 30, height: 30, borderRadius: 8, background: C.surface, border: `1px solid ${C.border2}`, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Ic n="swap" s={14} c={C.muted} />
                  </button>
                </div>
                <StopInput value={dst} onChange={setDst} placeholder="To — stop or area…" dot={C.red} options={stops.all} />

                {/* Time */}
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, marginBottom: 8, letterSpacing: "0.05em" }}>DEPARTURE TIME</div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input type="time" value={time} onChange={e => setTime(e.target.value)}
                      style={{ flex: 1, background: C.surface, border: `1px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}
                    />
                    <button onClick={() => setTime(nowTime())} style={{ background: C.accent + "18", border: `1px solid ${C.accent}44`, color: C.accent, borderRadius: 10, padding: "10px 14px", fontSize: 12, fontWeight: 800, cursor: "pointer", display: "flex", alignItems: "center", gap: 5, fontFamily: "inherit", whiteSpace: "nowrap" }}>
                      <Ic n="now" s={13} c={C.accent} /> Now
                    </button>
                  </div>
                </div>

                {/* Preference */}
                <div style={{ marginTop: 14 }}>
                  <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, marginBottom: 8, letterSpacing: "0.05em" }}>PREFERENCE</div>
                  <div style={{ display: "flex", gap: 6 }}>
                    {prefs.map(p => (
                      <button key={p.k} onClick={() => { setPref(p.k); if (results && src && dst) triggerSearch(src, dst, time || null, p.k); }} style={{ flex: 1, padding: "9px 4px", background: pref === p.k ? C.accent + "20" : C.surface, border: `1.5px solid ${pref === p.k ? C.accent : C.border2}`, borderRadius: 10, color: pref === p.k ? C.accent : C.muted, fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit" }}>
                        {p.e} {p.l}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Vehicle Selection dropdown */}
                <div style={{ marginTop: 14 }}>
                  <div style={{ fontSize: 11, color: C.muted, fontWeight: 700, marginBottom: 8, letterSpacing: "0.05em" }}>VEHICLE (FOR OWN VEHICLE COST ESTIMATE)</div>
                  <select value={selectedVehicle} onChange={e => setSelectedVehicle(e.target.value)} style={{ width: "100%", background: C.surface, border: `1.5px solid ${C.border2}`, borderRadius: 10, color: C.text, padding: "10px 12px", fontSize: 13, outline: "none", fontFamily: "inherit" }}>
                    <option value="">Default Vehicle (ICE Car)</option>
                    {userVehicles.map(v => (
                      <option key={v.id} value={`custom: ${v.name} | ${v.fuel_type} | ${v.efficiency}`}>
                        🚗 {v.name} ({v.fuel_type} · {v.efficiency} {v.fuel_type === "EV" ? "km/kWh" : "km/L"})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Error */}
                {error && (
                  <div style={{ marginTop: 12, background: C.red + "18", border: `1px solid ${C.red}44`, borderRadius: 10, padding: "10px 12px", display: "flex", gap: 8, alignItems: "flex-start" }}>
                    <Ic n="alert" s={14} c={C.red} />
                    <div style={{ fontSize: 12, color: C.red }}>{error}</div>
                  </div>
                )}

                {/* Main search button */}
                <button onClick={search} disabled={loading || !src || !dst} style={{ width: "100%", marginTop: 18, background: loading || !src || !dst ? C.dim : `linear-gradient(135deg, ${C.accent}, #ea580c)`, border: "none", color: "white", borderRadius: 12, padding: "14px", fontSize: 15, fontWeight: 800, cursor: loading ? "wait" : !src || !dst ? "not-allowed" : "pointer", boxShadow: src && dst ? `0 4px 24px ${C.accent}40` : "none", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontFamily: "inherit" }}>
                  {loading ? (
                    <><div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid white", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />Comparing options…</>
                  ) : (
                    <><Ic n="arrow" s={18} c="white" sw={2.5} />Compare All Options</>
                  )}
                </button>

                {/* Secondary BMTC actions */}
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button onClick={() => { if (!src || !dst) return; setShowAllBuses(!showAllBuses); setShowRouteSearch(false); setShowTimetable(false); }} style={{ flex: 1, background: showAllBuses ? MC.bmtc.color + "20" : C.surface, border: `1px solid ${showAllBuses ? MC.bmtc.color : C.border2}`, borderRadius: 10, padding: "9px 8px", fontSize: 12, fontWeight: 700, color: showAllBuses ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                    <Ic n="list" s={13} c={showAllBuses ? MC.bmtc.color : C.muted} /> See All Buses
                  </button>
                  <button onClick={() => { setShowRouteSearch(!showRouteSearch); setShowAllBuses(false); setShowTimetable(false); }} style={{ flex: 1, background: showRouteSearch ? MC.bmtc.color + "20" : C.surface, border: `1px solid ${showRouteSearch ? MC.bmtc.color : C.border2}`, borderRadius: 10, padding: "9px 8px", fontSize: 12, fontWeight: 700, color: showRouteSearch ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                    <Ic n="route" s={13} c={showRouteSearch ? MC.bmtc.color : C.muted} /> Route Lookup
                  </button>
                  <button onClick={() => { setShowTimetable(!showTimetable); setShowAllBuses(false); setShowRouteSearch(false); }} style={{ flex: 1, background: showTimetable ? C.accent + "20" : C.surface, border: `1px solid ${showTimetable ? C.accent : C.border2}`, borderRadius: 10, padding: "9px 8px", fontSize: 12, fontWeight: 700, color: showTimetable ? C.accent : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                    <Ic n="clock" s={13} c={showTimetable ? C.accent : C.muted} /> Timetable
                  </button>
                </div>
              </div>

              {/* All Buses Panel */}
              {showAllBuses && src && dst && (
                <AllBusesPanel src={src} dst={dst} time={time} onClose={() => setShowAllBuses(false)} />
              )}

              {/* Route Search Panel */}
              {showRouteSearch && <RouteSearchPanel />}

              {/* Timetable Panel */}
              {showTimetable && <TimetablePanel results={results} onClose={() => setShowTimetable(false)} stops={stops} src={src} dst={dst} time={time} />}
            </div>

            {/* Map */}
            <div style={{ height: "calc(100vh - 120px)", position: "sticky", top: 72 }}>
              <GoogleMap src={src} dst={dst} segments={null} activeMode={null} activeSegmentIndex={null} setActiveSegmentIndex={() => { }} useOsm={useOsm} setUseOsm={setUseOsm} />
            </div>
          </div>
        )}

        {/* RESULTS */}
        {page === "results" && results && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", gap: 20, alignItems: "start" }}>
            <div>
              {/* Header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
                <div>
                  <div style={{ fontSize: 13, color: C.muted }}>Best routes for</div>
                  <div style={{ fontSize: 20, fontWeight: 900, letterSpacing: "-0.02em" }}>{src} → {dst}</div>
                  <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>Departs {time || nowTime()} · Preference: {pref}</div>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <button onClick={() => setPage("plan")} style={{ background: "none", border: `1px solid ${C.border2}`, borderRadius: 8, color: C.muted, padding: "7px 12px", fontSize: 12, cursor: "pointer", fontFamily: "inherit" }}>← Edit</button>
                  <button onClick={() => { setShowAllBuses(!showAllBuses); setShowRouteSearch(false); setShowTimetable(false); }} style={{ background: showAllBuses ? MC.bmtc.color + "20" : C.card, border: `1px solid ${showAllBuses ? MC.bmtc.color : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: showAllBuses ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                    <Ic n="list" s={13} c={showAllBuses ? MC.bmtc.color : C.muted} /> See All Buses
                  </button>
                  <button onClick={() => { setShowRouteSearch(!showRouteSearch); setShowAllBuses(false); setShowTimetable(false); }} style={{ background: showRouteSearch ? MC.bmtc.color + "20" : C.card, border: `1px solid ${showRouteSearch ? MC.bmtc.color : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: showRouteSearch ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                    <Ic n="route" s={13} c={showRouteSearch ? MC.bmtc.color : C.muted} /> Route Lookup
                  </button>
                  <button onClick={() => { setShowTimetable(!showTimetable); setShowAllBuses(false); setShowRouteSearch(false); }} style={{ background: showTimetable ? C.accent + "20" : C.card, border: `1px solid ${showTimetable ? C.accent : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: showTimetable ? C.accent : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                    <Ic n="clock" s={13} c={showTimetable ? C.accent : C.muted} /> Timetable
                  </button>
                  {[{ v: "cards", icon: "grid", label: "Cards" }, { v: "compare", icon: "table", label: "Compare" }].map(b => (
                    <button key={b.v} onClick={() => setView(b.v)} style={{ background: view === b.v ? C.accent : C.card, border: `1px solid ${view === b.v ? C.accent : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: view === b.v ? "white" : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                      <Ic n={b.icon} s={13} c={view === b.v ? "white" : C.muted} /> {b.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* See All Buses inline */}
              {showAllBuses && <AllBusesPanel src={src} dst={dst} time={time} onClose={() => setShowAllBuses(false)} />}
              {showRouteSearch && <div style={{ marginBottom: 16 }}><RouteSearchPanel /></div>}
              {showTimetable && <TimetablePanel results={results} onClose={() => setShowTimetable(false)} stops={stops} src={src} dst={dst} time={time} />}

              {view === "cards" ? (
                <>
                  <AIRecommendationsPanel
                    recommendations={recommendations}
                    results={results}
                    selected={selected}
                    setSelected={setSelected}
                    mc={MC}
                    selectedCabVehicle={selectedCabVehicle}
                    setSelectedCabVehicle={setSelectedCabVehicle}
                    selectedMultimodalOption={selectedMultimodalOption}
                    setSelectedMultimodalOption={setSelectedMultimodalOption}
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginTop: 20 }}>
                    {results && Object.keys(results).map(m => {
                      const cardData = (m === "cab" && selectedCabVehicle) ? {
                        ...results.cab,
                        ...selectedCabVehicle,
                        segments: selectedCabVehicle.segments,
                        guide: selectedCabVehicle.guide,
                        cost: selectedCabVehicle.cost,
                        time: selectedCabVehicle.time,
                        distance: selectedCabVehicle.distance,
                      } : (m === "multimodal" && selectedMultimodalOption) ? {
                        ...results.multimodal,
                        ...selectedMultimodalOption,
                        segments: selectedMultimodalOption.segments,
                        guide: selectedMultimodalOption.guide,
                        cost: selectedMultimodalOption.cost,
                        time: selectedMultimodalOption.time,
                        distance: selectedMultimodalOption.distance,
                      } : results[m];
                      return (
                        <ResultCard
                          key={m}
                          modeKey={m}
                          data={cardData}
                          selected={selected}
                          onSelect={setSelected}
                          selectedCabVehicle={selectedCabVehicle}
                          setSelectedCabVehicle={setSelectedCabVehicle}
                          selectedMultimodalOption={selectedMultimodalOption}
                          setSelectedMultimodalOption={setSelectedMultimodalOption}
                        />
                      );
                    })}
                  </div>
                </>
              ) : (
                <CompareTable results={{
                  ...results,
                  cab: selectedCabVehicle ? {
                    ...results.cab,
                    ...selectedCabVehicle,
                    segments: selectedCabVehicle.segments,
                    guide: selectedCabVehicle.guide,
                    cost: selectedCabVehicle.cost,
                    time: selectedCabVehicle.time,
                    distance: selectedCabVehicle.distance,
                  } : results.cab,
                  multimodal: selectedMultimodalOption ? {
                    ...results.multimodal,
                    ...selectedMultimodalOption,
                    segments: selectedMultimodalOption.segments,
                    guide: selectedMultimodalOption.guide,
                    cost: selectedMultimodalOption.cost,
                    time: selectedMultimodalOption.time,
                    distance: selectedMultimodalOption.distance,
                  } : results.multimodal
                }} />
              )}

              {/* CTA */}
              {selectedData?.available && (
                <div style={{ marginTop: 20, background: `linear-gradient(135deg, ${MC[selected].color}18, ${MC[selected].color}06)`, border: `1.5px solid ${MC[selected].color}44`, borderRadius: 16, padding: "18px 22px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <div>
                    <div style={{ fontSize: 12, color: C.muted }}>You selected</div>
                    <div style={{ fontSize: 18, fontWeight: 900 }}>{MC[selected].label}</div>
                    <div style={{ fontSize: 13, color: MC[selected].color, marginTop: 2 }}>
                      {selectedData.time} min · ₹{selectedData.cost} · {selectedData.transfers} transfer(s) · {selectedData.distance} km
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {saveSuccessMsg && (
                      <span style={{ fontSize: 12, color: C.green, fontWeight: 700 }}>
                        {saveSuccessMsg}
                      </span>
                    )}
                    <button onClick={handleSaveJourney} disabled={saving} style={{ background: "none", border: `1px solid ${C.border2}`, borderRadius: 10, padding: "10px 16px", color: C.muted, fontSize: 12, cursor: saving ? "wait" : "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5 }}>
                      <Ic n="save" s={13} c={C.muted} /> {saving ? "Saving..." : "Save"}
                    </button>
                    <button style={{ background: MC[selected].color, border: "none", borderRadius: 10, padding: "10px 22px", color: "white", fontSize: 13, fontWeight: 700, cursor: "pointer", fontFamily: "inherit", boxShadow: `0 4px 20px ${MC[selected].color}44`, display: "flex", alignItems: "center", gap: 6 }}>
                      <Ic n="share" s={14} c="white" /> Start Navigation
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Map + Guide */}
            <div style={{ position: "sticky", top: 72 }}>
              {selectedData?.available && (
                <div style={{ display: "flex", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 3, marginBottom: 12, gap: 4 }}>
                  <button onClick={() => setMapView("gmap")} style={{
                    flex: 1, background: mapView === "gmap" ? C.card : "transparent",
                    border: "none", borderRadius: 9, color: mapView === "gmap" ? C.accent : C.muted,
                    padding: "7px 0", fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit",
                    transition: "all 0.2s"
                  }}>🗺️ Google Map</button>
                  <button onClick={() => setMapView("linear")} style={{
                    flex: 1, background: mapView === "linear" ? C.card : "transparent",
                    border: "none", borderRadius: 9, color: mapView === "linear" ? C.accent : C.muted,
                    padding: "7px 0", fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit",
                    transition: "all 0.2s"
                  }}>🛤️ Linear Route Map</button>
                </div>
              )}

              {mapView === "linear" && selectedData ? (
                <LinearRouteMap segments={selectedData?.segments} activeMode={selected} />
              ) : (
                <GoogleMap
                  src={src}
                  dst={dst}
                  segments={selectedData?.segments}
                  activeMode={selected}
                  guide={selectedData?.guide}
                  activeSegmentIndex={activeSegmentIndex}
                  setActiveSegmentIndex={setActiveSegmentIndex}
                  useOsm={useOsm}
                  setUseOsm={setUseOsm}
                />
              )}
              {selectedData?.available && (
                <div style={{ marginTop: 14, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 12, letterSpacing: "0.05em" }}>STEP-BY-STEP GUIDE</div>
                  <TravelGuide
                    guide={selectedData.guide}
                    color={MC[selected].color}
                    activeSegmentIndex={activeSegmentIndex}
                    setActiveSegmentIndex={setActiveSegmentIndex}
                    segments={selectedData?.segments}
                    setMapView={setMapView}
                  />
                </div>
              )}
            </div>
          </div>
        )}
        </main>
      </div>
      <ChatbotWidget triggerSearch={triggerSearch} setSelected={setSelected} setSrc={setSrc} setDst={setDst} src={src} />

      {/* SETTINGS MODAL */}
      {showSettings && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(8, 9, 15, 0.75)", backdropFilter: "blur(8px)",
          display: "flex", alignItems: "center", justifyContent: "center",
          zIndex: 1000
        }} onClick={() => setShowSettings(false)}>
          <div style={{
            background: C.surface, border: `1px solid ${C.border}`,
            borderRadius: 20, width: 440, padding: 28,
            boxShadow: "0 20px 40px rgba(0,0,0,0.5)",
            display: "flex", flexDirection: "column", gap: 20
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontWeight: 800, fontSize: 16 }}>Map Configuration</div>
              <button onClick={() => setShowSettings(false)} style={{ background: "none", border: "none", color: C.muted, cursor: "pointer", fontSize: 16 }}>✕</button>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: C.muted }}>MAP ENGINE PREFERENCE</label>
              <div style={{ display: "flex", gap: 8, background: C.bg, padding: 4, borderRadius: 12, border: `1px solid ${C.border2}` }}>
                <button onClick={() => {
                  localStorage.setItem("force_osm", "true");
                  setUseOsm(true);
                }} style={{
                  flex: 1, padding: "8px 0", borderRadius: 8, border: "none",
                  background: useOsm ? C.card : "transparent",
                  color: useOsm ? C.accent : C.muted,
                  fontWeight: 700, fontSize: 12, cursor: "pointer"
                }}>OpenStreetMap (Leaflet)</button>
                <button onClick={() => {
                  localStorage.setItem("force_osm", "false");
                  setUseOsm(false);
                  const key = getGoogleMapsKey();
                  if (key && key !== "YOUR_GOOGLE_MAPS_API_KEY") {
                    window.dispatchEvent(new Event("osm_fallback"));
                  }
                }} style={{
                  flex: 1, padding: "8px 0", borderRadius: 8, border: "none",
                  background: !useOsm ? C.card : "transparent",
                  color: !useOsm ? C.accent : C.muted,
                  fontWeight: 700, fontSize: 12, cursor: "pointer"
                }}>Google Maps</button>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 11, fontWeight: 700, color: C.muted }}>GOOGLE MAPS API KEY</label>
              <input
                type="password"
                placeholder="AIzaSy..."
                defaultValue={localStorage.getItem("gmaps_api_key") || ""}
                onChange={(e) => {
                  const val = e.target.value.trim();
                  if (val) {
                    localStorage.setItem("gmaps_api_key", val);
                  } else {
                    localStorage.removeItem("gmaps_api_key");
                  }
                }}
                style={{
                  background: C.bg, border: `1px solid ${C.border2}`, borderRadius: 10,
                  padding: "10px 14px", color: C.text, fontSize: 13, outline: "none", fontFamily: "inherit"
                }}
              />
              <div style={{ fontSize: 10, color: C.muted }}>
                Leave empty to use environment variables or backend default key.
              </div>
            </div>

            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button onClick={() => setShowSettings(false)} style={{ flex: 1, padding: "10px 0", borderRadius: 10, background: "none", border: `1px solid ${C.border2}`, color: C.muted, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>Close</button>
              <button onClick={() => {
                window.location.reload();
              }} style={{ flex: 1, padding: "10px 0", borderRadius: 10, background: C.accent, border: "none", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>Save & Reload</button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px) scale(0.95); }
          to { opacity: 1; transform: none; }
        }
        * { box-sizing: border-box; }
        input::placeholder { color: #94a3b8; }
        input[type="time"]::-webkit-calendar-picker-indicator { opacity: 0.6; }
        select { -webkit-appearance: none; -moz-appearance: none; appearance: none; background-image: url("data:image/svg+xml;utf8,<svg fill='%236b7a99' height='24' viewBox='0 0 24 24' width='24' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/><path d='M0 0h24v24H0z' fill='none'/></svg>"); background-repeat: no-repeat; background-position: right 10px center; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
      `}</style>
    </div>
  );
}
