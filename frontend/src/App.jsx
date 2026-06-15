import { useState, useEffect, useRef, useCallback } from "react";

/* ─────────────────────────────────────────────────────────────
   CONFIG
───────────────────────────────────────────────────────────── */
const API_BASE = "http://localhost:8000";
const GOOGLE_MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "YOUR_GOOGLE_MAPS_API_KEY"; // replace with your key

/* ─────────────────────────────────────────────────────────────
   DESIGN TOKENS
───────────────────────────────────────────────────────────── */
const C = {
  bg: "#08090f", surface: "#0f1120", card: "#151929",
  border: "#1e2440", border2: "#252d4a",
  text: "#e8ecf5", muted: "#6b7a99", dim: "#2a3250",
  accent: "#f97316", metro: "#8b5cf6",
  green: "#22c55e", red: "#ef4444", yellow: "#f59e0b",
};

const MC = {
  bmtc:  { label: "BMTC Bus",    short: "BUS",   color: "#f97316", bg: "#1a0f06", icon: "bus",   line: "Ordinary · Vajra · AC" },
  metro: { label: "Namma Metro", short: "METRO",  color: "#8b5cf6", bg: "#100c1a", icon: "metro", line: "Green · Purple · Yellow" },
  cab:   { label: "Cab / Auto",  short: "CAB",   color: "#f59e0b", bg: "#1a1200", icon: "cab",   line: "Namma Yatri · Ola · Uber · Rapido" },
  car:   { label: "Own Vehicle", short: "CAR",   color: "#10b981", bg: "#051510", icon: "car",   line: "Fuel + Parking est." },
};

/* ─────────────────────────────────────────────────────────────
   ICONS
───────────────────────────────────────────────────────────── */
const P = {
  bus:      "M8 6v6m8-6v6M3 16h18M5 4h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V6a2 2 0 012-2zM7 20h2m6 0h2",
  metro:    "M3 7h18M3 12h18M5 7V5a2 2 0 012-2h10a2 2 0 012 2v2M5 17v2a2 2 0 002 2h10a2 2 0 002-2v-2",
  cab:      "M5 17H3a2 2 0 01-2-2V9a2 2 0 012-2h3l2-4h4l2 4h3a2 2 0 012 2v6a2 2 0 01-2 2h-2M7.5 20.5a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm9 0a1.5 1.5 0 100-3 1.5 1.5 0 000 3z",
  car:      "M19 17H5M5 17a2 2 0 01-2-2V9a2 2 0 012-2h3l2-3h4l2 3h3a2 2 0 012 2v6a2 2 0 01-2 2",
  walk:     "M13 4a1 1 0 100-2 1 1 0 000 2zm-3 15l1-5 2 2v5h2v-6l-2-2 1-4m-2-3l-3 1v4H5v-5l5-2",
  transfer: "M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4",
  clock:    "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-6v-4l2.5-2.5",
  mappin:   "M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0118 0zM12 13a3 3 0 100-6 3 3 0 000 6z",
  swap:     "M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4",
  chevron:  "M6 9l6 6 6-6",
  check:    "M20 6L9 17l-5-5",
  arrow:    "M5 12h14M12 5l7 7-7 7",
  now:      "M13 2L3 14h9l-1 8 10-12h-9l1-8z",
  save:     "M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2zM17 21v-8H7v8M7 3v5h8",
  home:     "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9z",
  grid:     "M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z",
  table:    "M3 3h18M3 9h18M3 15h18M9 3v18M15 3v18",
  trend:    "M23 6l-9.5 9.5-5-5L1 18",
  share:    "M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8M16 6l-4-4-4 4M12 2v13",
  info:     "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-7v-4m0-4h.01",
  alert:    "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4m0 4h.01",
  search:   "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  x:        "M18 6L6 18M6 6l12 12",
  list:     "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
  route:    "M3 12h18M3 6h18M3 18h18",
};

function Ic({ n, s = 16, c = "currentColor", sw = 1.8 }) {
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none"
      stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
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
async function apiCompare(src, dst, time, pref) {
  const res = await fetch(`${API_BASE}/api/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: src, destination: dst, time: time || null, preference: pref }),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  const d = await res.json();
  return d.results;
}

async function apiAllBuses(src, dst) {
  const res = await fetch(`${API_BASE}/api/bmtc/all-buses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: src, destination: dst }),
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

async function apiStops() {
  try {
    const [b, m] = await Promise.all([
      fetch(`${API_BASE}/api/bmtc/stops`).then(r => r.json()),
      fetch(`${API_BASE}/api/metro/stations`).then(r => r.json()),
    ]);
    return {
      bmtc: b.stops || [], metro: m.stations || [],
      all: [...new Set([...(b.stops || []), ...(m.stations || [])])].sort(),
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
   GOOGLE MAPS COMPONENT
───────────────────────────────────────────────────────────── */
function GoogleMap({ src, dst, segments, activeMode }) {
  const ref = useRef(null);
  const mapRef = useRef(null);
  const [loaded, setLoaded] = useState(false);
  const coordsCacheRef = useRef({});

  useEffect(() => {
    if (window.google) { setLoaded(true); return; }
    if (document.getElementById("gmaps-script")) return;
    const s = document.createElement("script");
    s.id = "gmaps-script";
    s.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_KEY}&libraries=places`;
    s.async = true;
    s.onload = () => setLoaded(true);
    document.head.appendChild(s);
  }, []);

  useEffect(() => {
    if (!loaded || !ref.current) return;
    if (!mapRef.current) {
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
      const cache = coordsCacheRef.current;
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
        }
      }

      // Clear previous map objects
      if (window._utrsMarkers) window._utrsMarkers.forEach(m => m.setMap(null));
      window._utrsMarkers = [];

      if (window._utrsRenderers) window._utrsRenderers.forEach(r => r.setMap(null));
      window._utrsRenderers = [];

      if (window._utrsPolylines) window._utrsPolylines.forEach(p => p.setMap(null));
      window._utrsPolylines = [];

      const bounds = new window.google.maps.LatLngBounds();

      // Plot Start and Destination Markers
      let srcPos = cache[src];
      let dstPos = cache[dst];

      if (srcPos) {
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

      if (dstPos) {
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

      // Render segments
      if (segments && segments.length > 0) {
        const segmentColors = ["#f97316", "#3b82f6", "#ec4899", "#14b8a6", "#eab308", "#ef4444"];

        segments.forEach((seg, idx) => {
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
            const transitSegmentIdx = segments.filter((s, sIdx) => sIdx < idx && s.type !== "walk" && !(s.route && s.route.toLowerCase().includes("walk"))).length;
            color = segmentColors[transitSegmentIdx % segmentColors.length];
          }

          const segStops = seg.stops || [];
          const pathCoords = segStops.map(s => cache[s]).filter(Boolean);

          // Plot intermediate stop markers
          segStops.forEach(stopName => {
            const pos = cache[stopName];
            if (!pos) return;
            bounds.extend(pos);

            const isGlobalBound = stopName.toLowerCase() === (src || "").toLowerCase() || stopName.toLowerCase() === (dst || "").toLowerCase();
            if (isGlobalBound) return;

            const isTransferStop = stopName === seg.from || stopName === seg.to;
            const stopMarker = new window.google.maps.Marker({
              map,
              position: pos,
              title: stopName,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: isTransferStop ? 6 : 4,
                fillColor: isTransferStop ? color : "#fff",
                fillOpacity: 1,
                strokeColor: isTransferStop ? "#fff" : color,
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
            if (pathCoords.length > 1) {
              const poly = new window.google.maps.Polyline({
                map, path: pathCoords, strokeColor: color, strokeWeight: 4, strokeOpacity: 0.75,
                icons: [{
                  icon: { path: "M 0,-1 0,1", strokeOpacity: 1, scale: 3 },
                  offset: "0", repeat: "15px"
                }]
              });
              window._utrsPolylines.push(poly);
            } else if (seg.from && seg.to) {
              const ds = new window.google.maps.DirectionsService();
              const dr = new window.google.maps.DirectionsRenderer({
                map, suppressMarkers: true,
                polylineOptions: {
                  strokeColor: color, strokeWeight: 4, strokeOpacity: 0.75,
                  icons: [{
                    icon: { path: "M 0,-1 0,1", strokeOpacity: 1, scale: 3 },
                    offset: "0", repeat: "15px"
                  }]
                }
              });
              ds.route({
                origin: seg.from + ", Bengaluru", destination: seg.to + ", Bengaluru", travelMode: "WALKING"
              }, (res, status) => { if (status === "OK") dr.setDirections(res); });
              window._utrsRenderers.push(dr);
            }
          } else {
            // Bus, Cab, Car
            if (seg.from && seg.to) {
              const ds = new window.google.maps.DirectionsService();
              const dr = new window.google.maps.DirectionsRenderer({
                map, suppressMarkers: true,
                polylineOptions: { strokeColor: color, strokeWeight: 5, strokeOpacity: 0.85 }
              });

              let waypoints = [];
              if (segStops.length > 2) {
                const innerStops = segStops.slice(1, -1);
                const maxWaypoints = 15;
                const step = Math.ceil(innerStops.length / maxWaypoints);
                const sampled = innerStops.filter((_, sidx) => sidx % step === 0);
                waypoints = sampled.map(stopName => ({
                  location: stopName + ", Bengaluru", stopover: false
                }));
              }

              ds.route({
                origin: seg.from + ", Bengaluru",
                destination: seg.to + ", Bengaluru",
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
  }, [loaded, src, dst, segments, activeMode]);

  return (
    <div style={{ position: "relative", height: "100%", minHeight: 340, borderRadius: 16, overflow: "hidden", border: `1px solid ${C.border}` }}>
      <div ref={ref} style={{ width: "100%", height: "100%", minHeight: 340 }} />
      {!loaded && (
        <div style={{
          position: "absolute", inset: 0, background: C.surface,
          display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 10,
        }}>
          <div style={{ width: 28, height: 28, borderRadius: "50%", border: `3px solid ${C.accent}`, borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />
          <div style={{ fontSize: 12, color: C.muted }}>Loading map…</div>
        </div>
      )}
      {src && <div style={{ position: "absolute", bottom: 46, left: 12, background: C.green + "ee", borderRadius: 7, padding: "3px 9px", fontSize: 11, color: "white", fontWeight: 700, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>🟢 {src}</div>}
      {dst && <div style={{ position: "absolute", bottom: 12, left: 12, background: C.red + "ee", borderRadius: 7, padding: "3px 9px", fontSize: 11, color: "white", fontWeight: 700, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>🔴 {dst}</div>}
      {activeMode && <div style={{ position: "absolute", top: 12, right: 12, background: MC[activeMode]?.color + "dd", borderRadius: 8, padding: "4px 10px", fontSize: 11, color: "white", fontWeight: 700 }}>{MC[activeMode]?.short} Route</div>}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AUTOCOMPLETE INPUT
───────────────────────────────────────────────────────────── */
function StopInput({ value, onChange, placeholder, dot, options }) {
  const [open, setOpen] = useState(false);
  const filtered = (options || []).filter(s => s.toLowerCase().includes(value.toLowerCase()) && s !== value).slice(0, 10);
  return (
    <div style={{ position: "relative", flex: 1 }}>
      <div style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", zIndex: 2 }}>
        <div style={{ width: 10, height: 10, borderRadius: "50%", background: dot, border: `2px solid ${dot}88` }} />
      </div>
      <input value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 160)}
        placeholder={placeholder}
        style={{ width: "100%", boxSizing: "border-box", background: C.surface, border: `1.5px solid ${C.border2}`, borderRadius: 12, color: C.text, padding: "13px 14px 13px 34px", fontSize: 14, outline: "none", fontFamily: "inherit" }}
      />
      {open && filtered.length > 0 && (
        <div style={{ position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0, background: C.card, border: `1px solid ${C.border2}`, borderRadius: 10, zIndex: 200, maxHeight: 240, overflowY: "auto", boxShadow: "0 16px 48px #00000090" }}>
          {filtered.map(s => (
            <div key={s} onMouseDown={() => { onChange(s); setOpen(false); }}
              style={{ padding: "10px 14px", cursor: "pointer", fontSize: 13, color: C.text, display: "flex", alignItems: "center", gap: 8, borderBottom: `1px solid ${C.border}` }}
              onMouseEnter={e => e.currentTarget.style.background = C.surface}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}
            ><Ic n="mappin" s={12} c={C.muted} />{s}</div>
          ))}
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
function TravelGuide({ guide, color }) {
  if (!guide || guide.length === 0) return null;
  return (
    <div>
      {guide.map((step, i) => (
        <div key={i} style={{ display: "flex", gap: 12 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 34 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: color + "20", border: `1.5px solid ${color}44`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Ic n={step.icon || "arrow"} s={15} c={color} />
            </div>
            {i < guide.length - 1 && <div style={{ width: 1.5, flex: 1, background: color + "25", minHeight: 18, margin: "4px 0" }} />}
          </div>
          <div style={{ flex: 1, paddingBottom: i < guide.length - 1 ? 14 : 0 }}>
            <div style={{ fontWeight: 600, fontSize: 13, color: C.text }}>{step.text}</div>
            <div style={{ display: "flex", gap: 10, marginTop: 2, flexWrap: "wrap" }}>
              {step.duration && <span style={{ fontSize: 11, color: C.muted }}>{step.duration}</span>}
              {step.detail && <span style={{ fontSize: 11, color }}>{step.detail}</span>}
            </div>
          </div>
        </div>
      ))}
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

function AllBusesPanel({ src, dst, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all | direct | transfer | vajra
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    setLoading(true);
    setData(null);
    apiAllBuses(src.toLowerCase(), dst.toLowerCase())
      .then(setData).catch(() => setData({ direct: [], transfer: [] }))
      .finally(() => setLoading(false));
  }, [src, dst]);

  const toggleExpand = (id) => setExpandedId(expandedId === id ? null : id);

  const direct   = data?.direct   || [];
  const transfer = data?.transfer || [];

  const directVajraAvailable   = direct.some(b => isVajraBus(b.route));
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
          { k: "all",      l: `All (${direct.length + transfer.length})` },
          { k: "direct",   l: `Direct (${direct.length})` },
          { k: "transfer", l: `Transfer (${transfer.length})` },
          { k: "vajra",    l: "Vajra / AC" },
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
                    {b.departure && <div style={{ fontSize: 11, color: C.muted, marginLeft: 6 }}>{b.departure}</div>}
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
                          ["Arrival",   b.arrival   || "--"],
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
                    <div style={{ display: "flex", justifyContent: "space-between", width: "100%", marginTop: 5, fontSize: 11, color: C.muted }}>
                      <span>{opt.transfers} transfer · {opt.total_time} min · {opt.distance} km</span>
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
  const [query, setQuery]           = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop]     = useState(false);
  const [result, setResult]         = useState(null);
  const [direction, setDirection]   = useState("forward"); // forward | return
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState(null);
  const debounceRef                 = useRef(null);

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
                { k: "return",  l: "Inbound / Return" },
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
   RESULT CARD
───────────────────────────────────────────────────────────── */
function ResultCard({ modeKey, data, selected, onSelect }) {
  const [tab, setTab] = useState(null);
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
      } catch {}
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
    }}>
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
          <div style={{ fontWeight: 800, fontSize: 22, color: m.color }}>₹{data.cost}</div>
          <div style={{ fontSize: 11, color: C.muted }}>{realDuration} min</div>
        </div>
      </div>

      {/* Stats strip */}
      <div style={{ margin: "0 14px 14px", background: C.surface, borderRadius: 10, padding: "10px 14px", display: "flex", flexWrap: "wrap" }}>
        {[
          { icon: "clock",    val: `${realDuration} min` },
          { icon: "transfer", val: `${data.transfers} transfer${data.transfers !== 1 ? "s" : ""}` },
          { icon: "mappin",   val: `${data.distance} km` },
          { icon: "now",      val: `${data.departure} → ${data.arrival}` },
        ].map((s, i) => (
          <div key={i} style={{ flex: "1 1 50%", display: "flex", alignItems: "center", gap: 5, padding: "3px 0" }}>
            <Ic n={s.icon} s={11} c={C.muted} />
            <span style={{ fontSize: 12, color: C.text }}>{s.val}</span>
          </div>
        ))}
      </div>

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
    { label: "Duration",  key: "time",      lower: true,  fmt: v => `${v} min` },
    { label: "Cost",      key: "cost",      lower: true,  fmt: v => `₹${v}` },
    { label: "Transfers", key: "transfers", lower: true,  fmt: v => `${v}` },
    { label: "Distance",  key: "distance",  lower: true,  fmt: v => `${v} km` },
    { label: "Departs",   key: "departure", lower: false, fmt: v => v },
    { label: "Arrives",   key: "arrival",   lower: false, fmt: v => v },
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
function Dashboard({ onPlan }) {
  const recent = [
    { from: "Hosa Road", to: "Majestic", mode: "bmtc", cost: 28, date: "Today, 09:14" },
    { from: "Koramangala", to: "MG Road", mode: "metro", cost: 48, date: "Yesterday" },
    { from: "Electronic City", to: "Hebbal", mode: "cab", cost: 145, date: "Jun 3" },
  ];
  const stats = [
    { label: "Journeys",   val: "24",    icon: "mappin", color: MC.bmtc.color },
    { label: "Saved",      val: "₹940",  icon: "trend",  color: MC.metro.color },
    { label: "Time saved", val: "6.2 hr",icon: "clock",  color: MC.cab.color },
    { label: "Avg cost",   val: "₹52",   icon: "now",    color: MC.car.color },
  ];
  return (
    <div>
      <div style={{ background: `linear-gradient(135deg, ${MC.bmtc.color}22, ${MC.metro.color}22)`, border: `1px solid ${C.border2}`, borderRadius: 16, padding: "24px 28px", marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800, color: C.text, marginBottom: 4 }}>Welcome back 👋</div>
          <div style={{ color: C.muted, fontSize: 13 }}>Plan your next journey — BMTC · Metro · Namma Yatri · Personal Vehicle</div>
        </div>
        <button onClick={onPlan} style={{ background: `linear-gradient(135deg, ${C.accent}, #ea580c)`, border: "none", color: "white", borderRadius: 12, padding: "12px 24px", fontSize: 14, fontWeight: 700, cursor: "pointer", fontFamily: "inherit", boxShadow: `0 4px 20px ${C.accent}44`, display: "flex", alignItems: "center", gap: 8 }}>
          <Ic n="arrow" s={16} c="white" /> Plan Journey
        </button>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 24 }}>
        {stats.map(s => (
          <div key={s.label} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: "18px 16px" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: s.color + "18", border: `1px solid ${s.color}33`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
              <Ic n={s.icon} s={18} c={s.color} />
            </div>
            <div style={{ fontSize: 22, fontWeight: 800, color: C.text }}>{s.val}</div>
            <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: C.text, marginBottom: 16 }}>Recent Journeys</div>
          {recent.map((r, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: i < recent.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: MC[r.mode].bg, border: `1px solid ${MC[r.mode].color}44`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Ic n={MC[r.mode].icon} s={15} c={MC[r.mode].color} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>{r.from} → {r.to}</div>
                <div style={{ fontSize: 11, color: C.muted }}>{r.date}</div>
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: MC[r.mode].color }}>₹{r.cost}</div>
            </div>
          ))}
        </div>
        <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 16, padding: 20 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: C.text, marginBottom: 16 }}>Transport Network</div>
          {Object.entries(MC).map(([k, m]) => (
            <div key={k} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 0", borderBottom: `1px solid ${C.border}` }}>
              <div style={{ width: 30, height: 30, borderRadius: 8, background: m.bg, border: `1px solid ${m.color}44`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Ic n={m.icon} s={14} c={m.color} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{m.label}</div>
                <div style={{ fontSize: 11, color: C.muted }}>{m.line}</div>
              </div>
              <Pill color={m.color} small>{k === "bmtc" || k === "metro" ? "Live" : k === "cab" ? "Live" : "Est."}</Pill>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   MAIN APP
───────────────────────────────────────────────────────────── */
export default function App() {
  const [page, setPage]           = useState("dashboard");
  const [src, setSrc]             = useState("");
  const [dst, setDst]             = useState("");
  const [time, setTime]           = useState("");
  const [pref, setPref]           = useState("cost");
  const [results, setResults]     = useState(null);
  const [selected, setSelected]   = useState(null);
  const [view, setView]           = useState("cards");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [stops, setStops]         = useState({ all: [], bmtc: [], metro: [] });
  const [showAllBuses, setShowAllBuses] = useState(false);
  const [showRouteSearch, setShowRouteSearch] = useState(false);
  const [mapView, setMapView]           = useState("gmap"); // "gmap" | "linear"

  useEffect(() => { apiStops().then(setStops); }, []);

  const nowTime = () => {
    const n = new Date();
    return `${String(n.getHours()).padStart(2,"0")}:${String(n.getMinutes()).padStart(2,"0")}`;
  };

  const search = async () => {
    if (!src.trim() || !dst.trim()) return;
    setLoading(true); setError(null); setShowAllBuses(false);
    try {
      const res = await apiCompare(src, dst, time || nowTime(), pref);
      setResults(res);
      setSelected(null);
      setView("cards");
      setPage("results");
    } catch (e) {
      setError(`Backend unreachable: ${e.message}. Run: uvicorn unified_api:app --reload --port 8000`);
    } finally { setLoading(false); }
  };

  const selectedData = results && selected ? results[selected] : null;
  const prefs = [
    { k: "cost",        e: "💰", l: "Cheapest"    },
    { k: "time",        e: "⚡", l: "Fastest"     },
    { k: "convenience", e: "🎯", l: "Comfortable" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'DM Sans','Segoe UI',sans-serif", color: C.text }}>

      {/* NAV */}
      <nav style={{ borderBottom: `1px solid ${C.border}`, background: C.surface + "ee", backdropFilter: "blur(16px)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px", display: "flex", alignItems: "center", height: 60, gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginRight: 4 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: `linear-gradient(135deg, ${C.accent}, #ea580c)`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Ic n="bus" s={17} c="white" sw={2.2} />
            </div>
            <div>
              <div style={{ fontWeight: 900, fontSize: 15, letterSpacing: "-0.03em" }}>UTRS Bengaluru</div>
              <div style={{ fontSize: 9, color: C.muted, letterSpacing: "0.1em" }}>UNIFIED TRANSIT</div>
            </div>
          </div>
          {[
            { id: "dashboard", icon: "home",   label: "Dashboard" },
            { id: "plan",      icon: "mappin", label: "Plan Journey" },
            ...(results ? [{ id: "results", icon: "grid", label: "Results" }] : []),
          ].map(n => (
            <button key={n.id} onClick={() => setPage(n.id)} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", gap: 6, color: page === n.id ? C.accent : C.muted, fontWeight: page === n.id ? 700 : 500, fontSize: 13, padding: "4px 2px", fontFamily: "inherit", borderBottom: page === n.id ? `2px solid ${C.accent}` : "2px solid transparent" }}>
              <Ic n={n.icon} s={14} c={page === n.id ? C.accent : C.muted} />{n.label}
            </button>
          ))}
          <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
            {Object.entries(MC).map(([k, m]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 4, background: m.bg, border: `1px solid ${m.color}33`, borderRadius: 20, padding: "3px 8px" }}>
                <Ic n={m.icon} s={10} c={m.color} />
                <span style={{ fontSize: 9, color: m.color, fontWeight: 800 }}>{m.short}</span>
              </div>
            ))}
          </div>
        </div>
      </nav>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 24px" }}>

        {/* DASHBOARD */}
        {page === "dashboard" && <Dashboard onPlan={() => setPage("plan")} />}

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
                <StopInput value={src} onChange={setSrc} placeholder="From — stop or area…" dot={C.green} options={stops.all} />
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
                      <button key={p.k} onClick={() => setPref(p.k)} style={{ flex: 1, padding: "9px 4px", background: pref === p.k ? C.accent + "20" : C.surface, border: `1.5px solid ${pref === p.k ? C.accent : C.border2}`, borderRadius: 10, color: pref === p.k ? C.accent : C.muted, fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit" }}>
                        {p.e} {p.l}
                      </button>
                    ))}
                  </div>
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
                    <><div style={{ width: 16, height: 16, borderRadius: "50%", border: "2px solid white", borderTopColor: "transparent", animation: "spin 0.8s linear infinite" }} />Searching all modes…</>
                  ) : (
                    <><Ic n="arrow" s={18} c="white" sw={2.5} />Compare All Options</>
                  )}
                </button>

                {/* Secondary BMTC actions */}
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button onClick={() => { if (!src || !dst) return; setShowAllBuses(!showAllBuses); setShowRouteSearch(false); }} style={{ flex: 1, background: showAllBuses ? MC.bmtc.color + "20" : C.surface, border: `1px solid ${showAllBuses ? MC.bmtc.color : C.border2}`, borderRadius: 10, padding: "9px 8px", fontSize: 12, fontWeight: 700, color: showAllBuses ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                    <Ic n="list" s={13} c={showAllBuses ? MC.bmtc.color : C.muted} /> See All Buses
                  </button>
                  <button onClick={() => { setShowRouteSearch(!showRouteSearch); setShowAllBuses(false); }} style={{ flex: 1, background: showRouteSearch ? MC.bmtc.color + "20" : C.surface, border: `1px solid ${showRouteSearch ? MC.bmtc.color : C.border2}`, borderRadius: 10, padding: "9px 8px", fontSize: 12, fontWeight: 700, color: showRouteSearch ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", justifyContent: "center", gap: 5 }}>
                    <Ic n="route" s={13} c={showRouteSearch ? MC.bmtc.color : C.muted} /> Route Lookup
                  </button>
                </div>
              </div>

              {/* All Buses Panel */}
              {showAllBuses && src && dst && (
                <AllBusesPanel src={src} dst={dst} onClose={() => setShowAllBuses(false)} />
              )}

              {/* Route Search Panel */}
              {showRouteSearch && <RouteSearchPanel />}
            </div>

            {/* Map */}
            <div style={{ height: "calc(100vh - 120px)", position: "sticky", top: 72 }}>
              <GoogleMap src={src} dst={dst} segments={null} activeMode={null} />
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
                  <button onClick={() => { setShowAllBuses(!showAllBuses); setShowRouteSearch(false); }} style={{ background: showAllBuses ? MC.bmtc.color + "20" : C.card, border: `1px solid ${showAllBuses ? MC.bmtc.color : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: showAllBuses ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                    <Ic n="list" s={13} c={showAllBuses ? MC.bmtc.color : C.muted} /> See All Buses
                  </button>
                  <button onClick={() => { setShowRouteSearch(!showRouteSearch); setShowAllBuses(false); }} style={{ background: showRouteSearch ? MC.bmtc.color + "20" : C.card, border: `1px solid ${showRouteSearch ? MC.bmtc.color : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: showRouteSearch ? MC.bmtc.color : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                    <Ic n="route" s={13} c={showRouteSearch ? MC.bmtc.color : C.muted} /> Route Lookup
                  </button>
                  {[{ v: "cards", icon: "grid", label: "Cards" }, { v: "compare", icon: "table", label: "Compare" }].map(b => (
                    <button key={b.v} onClick={() => setView(b.v)} style={{ background: view === b.v ? C.accent : C.card, border: `1px solid ${view === b.v ? C.accent : C.border2}`, borderRadius: 8, padding: "7px 12px", fontSize: 12, color: view === b.v ? "white" : C.muted, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5, fontWeight: 600 }}>
                      <Ic n={b.icon} s={13} c={view === b.v ? "white" : C.muted} /> {b.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* See All Buses inline */}
              {showAllBuses && <AllBusesPanel src={src} dst={dst} onClose={() => setShowAllBuses(false)} />}
              {showRouteSearch && <div style={{ marginBottom: 16 }}><RouteSearchPanel /></div>}

              {view === "cards" ? (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                  {Object.keys(results).map(m => (
                    <ResultCard key={m} modeKey={m} data={results[m]} selected={selected} onSelect={setSelected} />
                  ))}
                </div>
              ) : (
                <CompareTable results={results} />
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
                  <div style={{ display: "flex", gap: 8 }}>
                    <button style={{ background: "none", border: `1px solid ${C.border2}`, borderRadius: 10, padding: "10px 16px", color: C.muted, fontSize: 12, cursor: "pointer", fontFamily: "inherit", display: "flex", alignItems: "center", gap: 5 }}>
                      <Ic n="save" s={13} c={C.muted} /> Save
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
                <GoogleMap src={src} dst={dst} segments={selectedData?.segments} activeMode={selected} />
              )}
              {selectedData?.available && (
                <div style={{ marginTop: 14, background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: C.muted, marginBottom: 12, letterSpacing: "0.05em" }}>STEP-BY-STEP GUIDE</div>
                  <TravelGuide guide={selectedData.guide} color={MC[selected].color} />
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
        input::placeholder { color: #2a3250; }
        input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(0.5); }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #252d4a; border-radius: 4px; }
      `}</style>
    </div>
  );
}
