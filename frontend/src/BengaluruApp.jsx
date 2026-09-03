import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

const T = {
  primary:   "#6C3BF5",
  primaryDk: "#5328D1",
  grad:      "linear-gradient(135deg,#6C3BF5 0%,#9333EA 100%)",
  bg:        "#F7F8FC",
  white:     "#FFFFFF",
  text:      "#1A1A2E",
  muted:     "#6B7280",
  green:     "#10B981",
  orange:    "#F97316",
  blue:      "#2563EB",
  violet:    "#7C3AED",
  cabOr:     "#EA580C",
  carGr:     "#16A34A",
  pink:      "#DB2777",
  red:       "#EF4444",
  sidebar:   "linear-gradient(180deg,#1E1458 0%,#6C3BF5 55%,#9333EA 100%)",
  sideAct:   "rgba(255,255,255,0.18)",
  sideHov:   "rgba(255,255,255,0.08)",
};

const MC = {
  bmtc:      { label:"Bus",              color:T.blue,   bg:"#EFF6FF", ibg:"#DBEAFE", icon:"🚌", desc:"Best coverage",          fare:"₹ 25 – 50"  },
  metro:     { label:"Metro",            color:T.violet, bg:"#F5F3FF", ibg:"#EDE9FE", icon:"🚇", desc:"Fast & reliable",         fare:"₹ 30 – 60"  },
  cab:       { label:"Cabs",             color:T.cabOr,  bg:"#FFF7ED", ibg:"#FED7AA", icon:"🚕", desc:"Door to door",            fare:"₹ 200 – 450" },
  car:       { label:"Personal Vehicle", color:T.carGr,  bg:"#F0FDF4", ibg:"#BBF7D0", icon:"🚗", desc:"Drive your way\nToll & Fuel", fare:"₹ 120 - 250*" },
  multimodal:{ label:"Multi-Modal",      color:T.pink,   bg:"#FDF2F8", ibg:"#FBCFE8", icon:"🔄", desc:"Best of all\nSave time & money", fare:"" },
};

const PATHS = {
  home:    "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
  plan:    "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
  stops:   "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z",
  search:  "M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
  trips:   "M20 6h-2.18c.07-.44.18-.88.18-1.34C18 2.54 15.56 1 12 1S6 2.54 6 4.66c0 .46.11.9.18 1.34H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2z",
  fav:     "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
  fare:    "M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z",
  alert:   "M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z",
  settings:"M19.14 12.94c.04-.3.06-.61.06-.94s-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.56-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.07.63-.07.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z",
  help:    "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z",
  arrow:   "M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z",
  swap:    "M6.99 11L3 15l3.99 4v-3H14v-2H6.99v-3zM21 9l-3.99-4v3H10v2h7.01v3L21 9z",
  clock:   "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z",
  send:    "M2.01 21L23 12 2.01 3 2 10l15 2-15 2z",
  back:    "M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z",
  pin:     "M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z",
  bus:     "M4 16c0 .88.39 1.67 1 2.22V20c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h8v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1.78c.61-.55 1-1.34 1-2.22V6c0-3.5-3.58-4-8-4s-8 .5-8 4v10zm3.5 1c-.83 0-1.5-.67-1.5-1.5S6.67 14 7.5 14s1.5.67 1.5 1.5S8.33 17 7.5 17zm9 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm1.5-6H6V6h12v5z",
};

function Ic({ n, s = 20, c = "currentColor" }) {
  const d = PATHS[n];
  if (!d) return null;
  return <svg width={s} height={s} viewBox="0 0 24 24" fill={c}><path d={d} /></svg>;
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function apiCompare(src, dst, time, pref = "cost") {
  return apiFetch("/api/compare", {
    method: "POST",
    body: JSON.stringify({ source: src, destination: dst, time: time || null, preference: pref }),
  });
}

async function apiStops() {
  try {
    const [b, m] = await Promise.all([
      fetch(`${API_BASE}/api/bmtc/stops`).then(r => r.json()),
      fetch(`${API_BASE}/api/metro/stations`).then(r => r.json()),
    ]);
    const bmtc = b.stops || [];
    const metro = (m.stations || []).map(s => s.endsWith(" Metro Station") ? s : `${s} Metro Station`);
    return { bmtc, metro, all: [...new Set([...bmtc, ...metro])].sort() };
  } catch { return { all: [], bmtc: [], metro: [] }; }
}

async function apiChat(message, history = []) {
  try {
    return await apiFetch("/api/chat", { method: "POST", body: JSON.stringify({ message, history }) });
  } catch {
    try {
      return await apiFetch("/api/chatbot/query", { method: "POST", body: JSON.stringify({ message, history }) });
    } catch {
      return { response: "I'm your Bengaluru Transport Assistant. How can I help you plan your journey today?" };
    }
  }
}

async function apiSearchRoutes(query) {
  try {
    return await apiFetch(`/api/bmtc/route-search?query=${encodeURIComponent(query)}`);
  } catch {
    return { routes: ["500D", "500C", "G-2", "K-1", "V-335E", "MF-12"] };
  }
}

function RouteMap({ src, dst, segments, height = 300 }) {
  const divRef = useRef(null);
  const mapRef = useRef(null);
  const [ready, setReady] = useState(!!window.L);

  useEffect(() => {
    if (window.L) { setReady(true); return; }
    if (!document.getElementById("lf-css")) {
      const l = document.createElement("link");
      l.id = "lf-css"; l.rel = "stylesheet";
      l.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
      document.head.appendChild(l);
    }
    if (!document.getElementById("lf-js")) {
      const s = document.createElement("script");
      s.id = "lf-js"; s.async = true;
      s.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
      s.onload = () => setReady(true);
      document.head.appendChild(s);
    }
  }, []);

  useEffect(() => {
    if (!ready || !divRef.current) return;
    if (mapRef.current) { try { mapRef.current.remove(); } catch {} mapRef.current = null; }
    divRef.current.innerHTML = "";

    const map = window.L.map(divRef.current, { zoomControl: true, attributionControl: false }).setView([12.935, 77.620], 11);
    mapRef.current = map;

    window.L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      maxZoom: 19, subdomains: "abcd"
    }).addTo(map);

    const mkIcon = (col, size = 16) => window.L.divIcon({
      html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${col};border:3px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.3)"></div>`,
      iconSize: [size, size], iconAnchor: [size / 2, size / 2], className: ""
    });

    const routeCoords = [
      [12.9767, 77.5713], [12.9627, 77.5750], [12.9560, 77.5900],
      [12.9476, 77.5815], [12.9344, 77.6170], [12.9211, 77.6369], [12.8458, 77.6606]
    ];

    window.L.polyline(routeCoords, { color: "#6C3BF5", weight: 5, opacity: 0.9 }).addTo(map);
    window.L.marker(routeCoords[0], { icon: mkIcon(T.green, 16) }).addTo(map).bindPopup(src || "Majestic");
    window.L.marker(routeCoords[routeCoords.length - 1], { icon: mkIcon(T.red, 18) }).addTo(map).bindPopup(dst || "Electronic City");
    map.fitBounds([routeCoords[0], routeCoords[routeCoords.length - 1]], { padding: [30, 30] });

    return () => { try { mapRef.current?.remove(); } catch {} mapRef.current = null; };
  }, [ready, src, dst]);

  return (
    <div style={{ position: "relative", height, borderRadius: 16, overflow: "hidden", background: "#E8EFF7" }}>
      <div ref={divRef} style={{ width: "100%", height: "100%" }} />
      {!ready && (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "#F1F5F9" }}>
          <span style={{ fontSize: 12, color: T.muted }}>Loading map…</span>
        </div>
      )}
    </div>
  );
}

function StopInput({ value, onChange, placeholder, dot, options = [] }) {
  const [open, setOpen] = useState(false);
  const filtered = value.length > 0
    ? options.filter(s => s.toLowerCase().includes(value.toLowerCase()) && s !== value).slice(0, 8)
    : [];

  return (
    <div style={{ position: "relative" }}>
      <div style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", width: 10, height: 10, borderRadius: "50%", background: dot, zIndex: 2 }} />
      <input
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 180)}
        placeholder={placeholder}
        style={{ width: "100%", boxSizing: "border-box", background: "#F8F9FC", border: "1.5px solid #E5E7EB", borderRadius: 12, color: T.text, padding: "11px 12px 11px 30px", fontSize: 13, outline: "none" }}
      />
      {open && filtered.length > 0 && (
        <div style={{ position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0, background: T.white, border: "1px solid #E5E7EB", borderRadius: 12, zIndex: 400, boxShadow: "0 8px 32px rgba(0,0,0,.12)", maxHeight: 200, overflowY: "auto" }}>
          {filtered.map(s => (
            <div key={s} onMouseDown={() => { onChange(s); setOpen(false); }}
              style={{ padding: "9px 12px", cursor: "pointer", fontSize: 12, color: T.text, borderBottom: "1px solid #F3F4F6" }}>
              <Ic n="pin" s={12} c={T.muted} /> &nbsp;{s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const NAV = [
  { id:"home",     label:"Home",           ico:"home"     },
  { id:"plan",     label:"Plan Journey",   ico:"plan"     },
  { id:"stops",    label:"Explore Stops",  ico:"stops"    },
  { id:"search",   label:"Search Routes",  ico:"search"   },
  { id:"trips",    label:"My Trips",       ico:"trips"    },
  { id:"fav",      label:"Favourites",     ico:"fav"      },
  { id:"fare",     label:"Fare Guide",     ico:"fare"     },
  { id:"alert",    label:"Alerts & Updates", ico:"alert"  },
  { id:"settings", label:"Settings",       ico:"settings" },
  { id:"help",     label:"Help & Support", ico:"help"     },
];

function Sidebar({ page, onNav }) {
  return (
    <aside style={{ width: 220, height: "100vh", background: T.sidebar, position: "fixed", top: 0, left: 0, zIndex: 200, display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "20px 18px 16px", borderBottom: "1px solid rgba(255,255,255,.12)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <div style={{ width: 42, height: 42, borderRadius: 14, background: "rgba(255,255,255,.18)", border: "2px solid rgba(255,255,255,.3)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Ic n="bus" s={22} c="#fff" />
          </div>
          <div>
            <div style={{ color: "#fff", fontWeight: 800, fontSize: 14, lineHeight: 1.2 }}>Bengaluru</div>
            <div style={{ color: "rgba(255,255,255,.85)", fontSize: 10.5, fontWeight: 600 }}>Transport Navigator</div>
            <div style={{ color: "rgba(255,255,255,.5)", fontSize: 9, marginTop: 1 }}>Smart. Connected. Bengaluru.</div>
          </div>
        </div>
      </div>
      <nav style={{ flex: 1, padding: "12px 10px", display: "flex", flexDirection: "column", gap: 2, overflowY: "auto" }}>
        {NAV.map(n => {
          const active = page === n.id;
          return (
            <button key={n.id} onClick={() => onNav(n.id)}
              style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", borderRadius: 12, background: active ? T.sideAct : "transparent", border: "none", cursor: "pointer", color: active ? "#fff" : "rgba(255,255,255,.75)", fontWeight: active ? 700 : 500, fontSize: 13, textAlign: "left", width: "100%" }}>
              <Ic n={n.ico} s={17} c={active ? "#fff" : "rgba(255,255,255,.75)"} />
              {n.label}
            </button>
          );
        })}
      </nav>
      <div style={{ padding: "14px 16px 20px", borderTop: "1px solid rgba(255,255,255,.12)" }}>
        <div style={{ color: "rgba(255,255,255,.9)", fontSize: 12, fontWeight: 700, marginBottom: 2 }}>Moving Bengaluru Forward</div>
        <div style={{ color: "rgba(255,255,255,.5)", fontSize: 10, lineHeight: 1.4 }}>Your all-in-one guide to bus, metro, cabs and more.</div>
      </div>
    </aside>
  );
}

/* ─────────────────────────────────────────────────────────────
   HOME PAGE (Exactly matches uploaded image)
───────────────────────────────────────────────────────────── */
function HomePage({ stops, onNav, onSearch }) {
  const [src, setSrc] = useState("Majestic (Kempegowda Bus Station)");
  const [dst, setDst] = useState("Electronic City");
  const [time, setTime] = useState("");
  const [chatMsg, setChatMsg] = useState("");
  const [chatHistory, setChatHistory] = useState([
    { sender: "bot", text: "How can I help you today?" }
  ]);

  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

  const handleMiniChat = async (text) => {
    const q = text || chatMsg;
    if (!q.trim()) return;
    setChatMsg("");
    setChatHistory(prev => [...prev, { sender: "user", text: q }]);
    try {
      const res = await apiChat(q);
      setChatHistory(prev => [...prev, { sender: "bot", text: res.text || res.response || "Here is what I found for you." }]);
    } catch {
      setChatHistory(prev => [...prev, { sender: "bot", text: "I'm currently unable to connect to the backend server." }]);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, padding: "20px 28px", maxWidth: 1240, margin: "0 auto" }}>
      {/* Top Greeting & Weather/Clock */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: T.text }}>Good Morning! 👋</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: T.muted }}>Where will your journey take you today?</p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, background: "#FFF7ED", border: "1px solid #FED7AA", borderRadius: 20, padding: "6px 14px" }}>
            <span>☀️</span><span style={{ fontSize: 12, fontWeight: 700, color: T.cabOr }}>27°C</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, background: "#F5F3FF", border: "1px solid #DDD6FE", borderRadius: 20, padding: "6px 14px" }}>
            <Ic n="clock" s={14} c={T.violet} /><span style={{ fontSize: 12, fontWeight: 700, color: T.violet }}>{timeStr}</span>
          </div>
          <div style={{ position: "relative", width: 36, height: 36, borderRadius: "50%", background: "#F3F4F6", border: "1.5px solid #E5E7EB", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Ic n="alert" s={16} c={T.muted} />
            <div style={{ position: "absolute", top: 4, right: 4, width: 7, height: 7, borderRadius: "50%", background: T.red, border: "2px solid #fff" }} />
          </div>
        </div>
      </div>

      {/* HERO BANNER - Vidhana Soudha + Bus + Metro + Auto */}
      <div style={{ borderRadius: 24, overflow: "hidden", height: 200, position: "relative", background: "linear-gradient(135deg,#EEF2FF,#F5F3FF,#FFF7ED)" }}>
        <img src="/hero.png" alt="Bengaluru Transit" style={{ width: "100%", height: "100%", objectFit: "cover" }}
          onError={e => { e.target.style.display = "none"; }} />
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 48, paddingBottom: 16, pointerEvents: "none" }}>
          {[["🚌","BMTC Bus",T.blue],["🚇","Metro Train",T.violet],["🛺","Auto-Rickshaw",T.carGr]].map(([em, label, col]) => (
            <div key={label} style={{ textAlign: "center", filter: "drop-shadow(0 4px 6px rgba(0,0,0,0.15))" }}>
              <div style={{ fontSize: 48 }}>{em}</div>
              <div style={{ fontSize: 9.5, color: col, fontWeight: 800, background: "#ffffffdd", borderRadius: 6, padding: "2px 8px", marginTop: 2 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* PLAN YOUR JOURNEY CARD */}
      <div style={{ background: T.white, borderRadius: 20, padding: "20px 24px", boxShadow: "0 4px 20px rgba(108,59,245,.06)", border: "1px solid #F0EEFF" }}>
        <div style={{ fontSize: 16, fontWeight: 800, color: T.text, marginBottom: 14 }}>Plan Your Journey</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 38px 1fr auto", gap: 12, alignItems: "end" }}>
          <div>
            <div style={{ fontSize: 11, color: T.muted, fontWeight: 700, marginBottom: 6 }}>FROM</div>
            <StopInput value={src} onChange={setSrc} placeholder="Starting point…" dot={T.green} options={stops.all} />
          </div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <button onClick={() => { const t = src; setSrc(dst); setDst(t); }}
              style={{ width: 36, height: 36, borderRadius: 10, background: "#F5F3FF", border: "1.5px solid #DDD6FE", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Ic n="swap" s={16} c={T.violet} />
            </button>
          </div>
          <div>
            <div style={{ fontSize: 11, color: T.muted, fontWeight: 700, marginBottom: 6 }}>TO</div>
            <StopInput value={dst} onChange={setDst} placeholder="Destination…" dot={T.red} options={stops.all} />
          </div>
          <button onClick={() => onSearch(src, dst, time)}
            style={{ background: T.grad, border: "none", color: "#fff", borderRadius: 12, padding: "12px 22px", fontSize: 14, fontWeight: 700, cursor: "pointer", display: "flex", alignItems: "center", gap: 8, boxShadow: "0 4px 16px rgba(108,59,245,.3)", height: 44 }}>
            <Ic n="search" s={16} c="#fff" /> Find Best Route
          </button>
        </div>
      </div>

      {/* 5 TRANSPORT MODE CARDS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 14 }}>
        {Object.entries(MC).map(([key, m]) => (
          <button key={key} onClick={() => onSearch(src, dst, time)}
            style={{ background: T.white, border: `1.5px solid ${m.bg}`, borderRadius: 18, padding: "16px 12px", cursor: "pointer", textAlign: "center", boxShadow: "0 2px 10px rgba(0,0,0,.02)" }}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: m.ibg, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 10px", fontSize: 26 }}>{m.icon}</div>
            <div style={{ fontSize: 13, fontWeight: 800, color: T.text, marginBottom: 2 }}>{m.label}</div>
            <div style={{ fontSize: 10, color: T.muted, marginBottom: 6, whiteSpace: "pre-line" }}>{m.desc}</div>
            {m.fare && <div style={{ fontSize: 11, color: m.color, fontWeight: 700 }}>{m.fare}</div>}
          </button>
        ))}
      </div>

      {/* AI BANNER */}
      <div style={{ background: "linear-gradient(135deg,#F5F3FF,#EEF2FF)", borderRadius: 18, padding: "16px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", border: "1px solid #DDD6FE" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 36 }}>🤖</span>
          <div>
            <div style={{ fontSize: 15, fontWeight: 800, color: T.text }}>Need help planning your trip?</div>
            <div style={{ fontSize: 12, color: T.muted, marginTop: 2 }}>Ask our AI Assistant for routes, fares, timings and more.</div>
          </div>
        </div>
        <button onClick={() => onNav("assistant")}
          style={{ background: T.grad, border: "none", color: "#fff", borderRadius: 12, padding: "10px 20px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
          Chat with Assistant →
        </button>
      </div>

      {/* 4-COLUMN GRID BELOW (Matching image 1 bottom row layout) */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 340px", gap: 16, alignItems: "start" }}>
        {/* Saved Places */}
        <div style={{ background: T.white, borderRadius: 18, padding: "18px", border: "1px solid #F0F0F8" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ fontSize: 16 }}>⭐</span><span style={{ fontSize: 13, fontWeight: 800, color: T.text }}>Saved Places</span></div>
            <span style={{ fontSize: 10, color: T.primary, fontWeight: 700, cursor: "pointer" }}>View All</span>
          </div>
          {[["🏠","Home","Electronic City"],["💼","Work","Manyata Tech Park"]].map(([ico,lbl,sub]) => (
            <div key={lbl} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid #F9FAFB" }}>
              <span style={{ fontSize: 16 }}>{ico}</span>
              <div><div style={{ fontSize: 12, fontWeight: 700, color: T.text }}>{lbl}</div><div style={{ fontSize: 10, color: T.muted }}>{sub}</div></div>
            </div>
          ))}
        </div>

        {/* Recent Searches */}
        <div style={{ background: T.white, borderRadius: 18, padding: "18px", border: "1px solid #F0F0F8" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ fontSize: 16 }}>🕐</span><span style={{ fontSize: 13, fontWeight: 800, color: T.text }}>Recent Searches</span></div>
            <span style={{ fontSize: 10, color: T.primary, fontWeight: 700, cursor: "pointer" }}>View All</span>
          </div>
          {[["Majestic","Electronic City"],["Silk Board","Yeshwanthpur"]].map(([f,t]) => (
            <div key={f} onClick={() => { setSrc(f); setDst(t); }} style={{ cursor: "pointer", padding: "8px 0", borderBottom: "1px solid #F9FAFB", fontSize: 12, color: T.text }}>
              {f} → {t}
            </div>
          ))}
        </div>

        {/* Travel Alerts */}
        <div style={{ background: T.white, borderRadius: 18, padding: "18px", border: "1px solid #F0F0F8" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ fontSize: 16 }}>⚠️</span><span style={{ fontSize: 13, fontWeight: 800, color: T.text }}>Travel Alerts</span></div>
            <span style={{ fontSize: 10, color: T.primary, fontWeight: 700, cursor: "pointer" }}>View All</span>
          </div>
          <div style={{ fontSize: 11, color: T.text, fontWeight: 600 }}>Traffic congestion on</div>
          <div style={{ fontSize: 12, color: T.red, fontWeight: 800, marginTop: 2 }}>Outer Ring Road</div>
        </div>

        {/* AI Assistant Mini Widget (Positioned at bottom right as in uploaded image!) */}
        <div style={{ background: T.white, borderRadius: 18, padding: "18px", border: "1px solid #F0F0F8", boxShadow: "0 2px 10px rgba(0,0,0,.03)", display: "flex", flexDirection: "column", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 22 }}>🤖</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 800, color: T.text }}>AI Assistant</div>
              <div style={{ fontSize: 10, color: T.green, fontWeight: 600 }}>• Online</div>
            </div>
          </div>
          <div style={{ maxHeight: 110, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6, fontSize: 11 }}>
            {chatHistory.map((m, i) => (
              <div key={i} style={{ alignSelf: m.sender === "user" ? "flex-end" : "flex-start", background: m.sender === "user" ? T.grad : "#F3F4F6", color: m.sender === "user" ? "#fff" : T.text, padding: "6px 10px", borderRadius: 10, maxWidth: "85%" }}>
                {m.text}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {["Best route to Airport", "Next bus from Majestic", "Fare from Silk Board", "Show metro map"].map(chip => (
              <button key={chip} onClick={() => handleMiniChat(chip)}
                style={{ padding: "4px 8px", background: "#F5F3FF", border: "1px solid #DDD6FE", borderRadius: 12, fontSize: 10, color: T.violet, cursor: "pointer" }}>
                {chip}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <input value={chatMsg} onChange={e => setChatMsg(e.target.value)} onKeyDown={e => e.key === "Enter" && handleMiniChat()}
              placeholder="Type your message..."
              style={{ flex: 1, padding: "8px 12px", background: "#F8F9FC", border: "1px solid #E5E7EB", borderRadius: 16, fontSize: 11, outline: "none" }} />
            <button onClick={() => handleMiniChat()} style={{ width: 32, height: 32, borderRadius: "50%", background: T.grad, border: "none", color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Ic n="send" s={14} c="#fff" />
            </button>
          </div>
        </div>
      </div>

      {/* SMART TIP */}
      <div style={{ background: T.white, borderRadius: 16, padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", border: "1px solid #F0F0F8" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 18 }}>🌿</span>
          <span style={{ fontSize: 12.5, color: T.muted }}><strong style={{ color: T.carGr }}>Smart Tip</strong> — Travel off-peak to save time and fare. Buses are more frequent between 9 AM – 11 AM.</span>
        </div>
        <Ic n="arrow" s={16} c={T.muted} />
      </div>

      {/* BMTC MONTHLY PASS */}
      <div style={{ background: "linear-gradient(135deg,#EEF2FF,#DDD6FE)", borderRadius: 18, padding: "18px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", border: "1px solid #C4B5FD" }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 800, color: T.primaryDk }}>Save more with BMTC Monthly Pass</div>
          <div style={{ fontSize: 12, color: T.violet, marginTop: 2 }}>Unlimited travel. Affordable. Hassle-free.</div>
        </div>
        <button style={{ background: T.grad, border: "none", color: "#fff", borderRadius: 10, padding: "9px 18px", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
          Know More →
        </button>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   ROUTE DETAILS / RESULTS PAGE (With Interactive Leaflet Map & Options)
───────────────────────────────────────────────────────────── */
function RouteDetailsPage({ apiResults, src, dst, time, pref, onBack }) {
  const [selectedKey, setSelectedKey] = useState("bmtc");
  const [showFullTimings, setShowFullTimings] = useState(false);

  const results = apiResults?.results || {};
  const bmtcData = results.bmtc || {};
  const metroData = results.metro || {};
  const multiData = results.multimodal || {};
  const cabData = results.cab || {};
  const carData = results.car || {};

  const CARDS = [
    { key: "bmtc", label: bmtcData.all_direct?.[0] ? `${bmtcData.all_direct[0]} Direct Bus` : "Direct Bus", fare: `₹${bmtcData.cost || 35}`, time: `${bmtcData.time || 70} min`, stops: `${bmtcData.stops || 23} stops`, walk: "5 min walk", color: T.blue, ico: "🚌", data: bmtcData },
    { key: "metro", label: "Metro Purple Line", fare: `₹${metroData.cost || 45}`, time: `${metroData.time || 55} min`, stops: `${metroData.stations_crossed || 14} stations`, walk: "8 min walk", color: T.violet, ico: "🚇", data: metroData },
    { key: "multimodal", label: "Bus + Metro", fare: `₹${multiData.cost || 40}`, time: `${multiData.time || 65} min`, stops: "1 change", walk: "7 min walk", color: T.pink, ico: "🔄", data: multiData },
    { key: "cab", label: "Cab (One way)", fare: `₹${cabData.cost || 320}`, time: `${cabData.time || 45} min`, stops: "Door to door", walk: "0 min", color: T.cabOr, ico: "🚕", data: cabData },
    { key: "car", label: "Personal Vehicle", fare: `₹${carData.cost || 150}*`, time: `${carData.time || 40} min`, stops: `${carData.distance || 28} km`, walk: "Toll & Fuel", color: T.carGr, ico: "🚗", data: carData },
  ];

  const activeCard = CARDS.find(c => c.key === selectedKey) || CARDS[0];

  const STOPS_TIMELINE = activeCard.data?.segments?.[0]?.stops
    ? activeCard.data.segments[0].stops.map((s, idx) => ({
        name: s,
        time: idx === 0 ? (activeCard.data.departure || "10:30 AM") : (activeCard.data.arrival || "11:40 AM"),
        type: idx === 0 ? "Start" : idx === activeCard.data.segments[0].stops.length - 1 ? "End Point" : "Stop",
        color: idx === 0 ? T.green : idx === activeCard.data.segments[0].stops.length - 1 ? T.red : T.primary
      }))
    : [
        { name: src || "Majestic (Kempegowda Bus Station)", time: "10:30 AM", type: "Start", color: T.green },
        { name: "Corporation", time: "10:35 AM", type: "Stop", color: T.primary },
        { name: "Shivajinagar", time: "10:38 AM", type: "Stop", color: T.primary },
        { name: "Madiwala", time: "10:50 AM", type: "Stop", color: T.primary },
        { name: "BTM Layout", time: "11:00 AM", type: "Stop", color: T.primary },
        { name: "Silk Board", time: "11:10 AM", type: "Stop", color: T.primary },
        { name: dst || "Electronic City", time: "11:40 AM", type: "End Point", color: T.red },
      ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 400px", height: "100%" }}>
      <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 16, overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button onClick={onBack} style={{ width: 36, height: 36, borderRadius: "50%", background: "#F3F4F6", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Ic n="back" s={18} c={T.text} />
          </button>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: T.text }}>Route Details</h2>
            <div style={{ fontSize: 12, color: T.muted }}>{src} → {dst}</div>
          </div>
        </div>

        <div style={{ background: "linear-gradient(135deg,#FF7E5F,#FEB47B)", borderRadius: 20, padding: "20px", color: "#fff", boxShadow: "0 6px 20px rgba(255,126,95,.3)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ background: "#ffffff33", padding: "4px 10px", borderRadius: 8, fontSize: 13, fontWeight: 800 }}>{activeCard.label.split(' ')[0]}</span>
              <span style={{ fontSize: 15, fontWeight: 700 }}>{activeCard.label}</span>
            </div>
            <div style={{ fontSize: 22, fontWeight: 900 }}>{activeCard.fare}</div>
          </div>
          <div style={{ display: "flex", gap: 16, fontSize: 12, background: "#ffffff22", borderRadius: 12, padding: "10px 14px" }}>
            <div><strong>🕒 {activeCard.time}</strong> Total Time</div>
            <div><strong>🚌 {activeCard.stops}</strong></div>
            <div><strong>🚶 {activeCard.walk}</strong></div>
          </div>
        </div>

        <div style={{ background: T.white, borderRadius: 20, padding: "20px", border: "1px solid #F0F0F8" }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: T.text, marginBottom: 16 }}>Stops on this route</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {STOPS_TIMELINE.map((s, i) => (
              <div key={i} style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "8px 0" }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ width: 14, height: 14, borderRadius: "50%", background: s.color, border: "3px solid #fff" }} />
                  {i < STOPS_TIMELINE.length - 1 && <div style={{ width: 2, height: 26, background: "#E5E7EB", marginTop: 2 }} />}
                </div>
                <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: T.text }}>{s.name}</div>
                    <div style={{ fontSize: 10, color: s.color, fontWeight: 600 }}>{s.type}</div>
                  </div>
                  <div style={{ fontSize: 12, color: T.muted, fontWeight: 600 }}>{s.time}</div>
                </div>
              </div>
            ))}
          </div>
          <button onClick={() => setShowFullTimings(!showFullTimings)}
            style={{ width: "100%", marginTop: 16, background: "#FFF7ED", border: "1.5px solid #FED7AA", color: T.cabOr, borderRadius: 12, padding: "11px", fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
            📅 {showFullTimings ? "Hide Full Timings" : "View Full Timings"}
          </button>
        </div>
      </div>

      <div style={{ padding: "20px 24px 20px 0", display: "flex", flexDirection: "column", gap: 16, overflowY: "auto" }}>
        <div style={{ background: T.white, borderRadius: 20, padding: "16px", border: "1px solid #F0F0F8" }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: T.text, marginBottom: 10 }}>Interactive Map</div>
          <RouteMap src={src} dst={dst} segments={activeCard.data?.segments} height={240} />
        </div>
        <div style={{ background: T.white, borderRadius: 20, padding: "16px", border: "1px solid #F0F0F8" }}>
          <div style={{ fontSize: 14, fontWeight: 800, color: T.text, marginBottom: 12 }}>Alternative Options</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {CARDS.map(c => (
              <div key={c.key} onClick={() => setSelectedKey(c.key)}
                style={{ padding: "12px 14px", borderRadius: 14, border: `1.5px solid ${selectedKey === c.key ? c.color : "#F0F0F8"}`, background: selectedKey === c.key ? "#F8F9FC" : T.white, cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <span style={{ fontSize: 20 }}>{c.ico}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 800, color: T.text }}>{c.label}</div>
                    <div style={{ fontSize: 10, color: T.muted }}>{c.time} · {c.stops}</div>
                  </div>
                </div>
                <div style={{ fontSize: 14, fontWeight: 900, color: T.green }}>{c.fare}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PlanJourneyPage({ stops, onResults }) {
  const [src, setSrc] = useState("Majestic (Kempegowda Bus Station)");
  const [dst, setDst] = useState("Electronic City");
  const [date, setDate] = useState("2026-05-29");
  const [time, setTime] = useState("");
  const [pref, setPref] = useState("cost");

  const doSearch = async () => {
    try {
      const res = await apiCompare(src, dst, time, pref);
      onResults(res, src, dst, time, pref);
    } catch {
      onResults(null, src, dst, time, pref);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "28px auto", padding: "0 20px" }}>
      <div style={{ background: "linear-gradient(135deg,#0072FF,#00C6FF)", borderRadius: "20px 20px 0 0", padding: "20px 24px", color: "#fff", display: "flex", justifyContent: "space-between" }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Plan Journey</div>
        <span style={{ fontSize: 20 }}>🗺️</span>
      </div>
      <div style={{ background: T.white, borderRadius: "0 0 20px 20px", padding: "24px", border: "1px solid #F0F0F8" }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: T.muted, fontWeight: 700, marginBottom: 6 }}>FROM</div>
          <StopInput value={src} onChange={setSrc} placeholder="Starting point…" dot={T.green} options={stops.all} />
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: 16 }}>
          <button onClick={() => { const t = src; setSrc(dst); setDst(t); }}
            style={{ width: 36, height: 36, borderRadius: 10, background: "#F5F3FF", border: "1.5px solid #DDD6FE", cursor: "pointer" }}>
            <Ic n="swap" s={18} c={T.violet} />
          </button>
        </div>
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: T.muted, fontWeight: 700, marginBottom: 6 }}>TO</div>
          <StopInput value={dst} onChange={setDst} placeholder="Destination…" dot={T.red} options={stops.all} />
        </div>
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, color: T.muted, fontWeight: 700, marginBottom: 6 }}>JOURNEY DATE</div>
          <input type="date" value={date} onChange={e => setDate(e.target.value)}
            style={{ width: "100%", padding: "12px", background: "#F8F9FC", border: "1.5px solid #E5E7EB", borderRadius: 12, fontSize: 14, outline: "none" }} />
        </div>
        <button onClick={doSearch}
          style={{ width: "100%", background: T.grad, border: "none", color: "#fff", borderRadius: 14, padding: "15px", fontSize: 15, fontWeight: 800, cursor: "pointer" }}>
          Find Best Route
        </button>
      </div>
    </div>
  );
}

function ExploreStopsPage({ stops }) {
  const [q, setQ] = useState("");
  const shown = stops.all.length > 0 && q.length > 0
    ? stops.all.filter(s => s.toLowerCase().includes(q.toLowerCase())).slice(0, 10).map((name, i) => ({
        name, dist: `${(i + 1) * 120} m`, type: name.includes("Metro") ? "Metro Station" : "Bus Stop"
      }))
    : [
        { name: "Majestic (Kempegowda Bus Station)", dist: "80 m", type: "Major Terminal" },
        { name: "Kempegowda Metro Station", dist: "150 m", type: "Metro Interchange" },
        { name: "Corporation", dist: "320 m", type: "Major Stop" },
        { name: "Shivajinagar Bus Station", dist: "500 m", type: "Major Terminal" },
        { name: "MG Road Metro Station", dist: "650 m", type: "Purple Line Metro" },
      ];

  return (
    <div style={{ maxWidth: 650, margin: "28px auto", padding: "0 20px" }}>
      <div style={{ background: "linear-gradient(135deg,#00A896,#028090)", borderRadius: "20px 20px 0 0", padding: "20px 24px", color: "#fff", display: "flex", justifyContent: "space-between" }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Explore Stops & Stations</div>
        <span style={{ fontSize: 20 }}>📍</span>
      </div>
      <div style={{ background: T.white, borderRadius: "0 0 20px 20px", padding: "24px", border: "1px solid #F0F0F8" }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Search bus stop or metro station…"
          style={{ width: "100%", padding: "12px 16px", background: "#F8F9FC", border: "1.5px solid #E5E7EB", borderRadius: 12, fontSize: 14, outline: "none", marginBottom: 20 }} />
        <div style={{ fontSize: 13, fontWeight: 800, color: T.text, marginBottom: 14 }}>Nearby Stops & Stations</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {shown.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid #F9FAFB" }}>
              <div style={{ width: 12, height: 12, borderRadius: "50%", background: s.type.includes("Metro") ? T.violet : "#00A896" }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: T.text }}>{s.name}</div>
                <div style={{ fontSize: 10, color: s.type.includes("Metro") ? T.violet : "#00A896", fontWeight: 600 }}>{s.type}</div>
              </div>
              <div style={{ fontSize: 12, color: T.muted }}>{s.dist}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SearchRoutesPage({ onSearch }) {
  const [query, setQuery] = useState("");
  const [routes, setRoutes] = useState([
    { num: "500D", via: "Silk Board → Hebbal → Electronic City", freq: "Every 5 min", type: "Volvo AC" },
    { num: "500C", via: "Banashankari → Silk Board → ITPL", freq: "Every 8 min", type: "Ordinary" },
    { num: "G-2", via: "Majestic → MG Road → Hope Farm", freq: "Every 10 min", type: "Vayu Vajra" },
    { num: "K-1", via: "Yeshwanthpur → Corporation → Electronic City", freq: "Every 12 min", type: "Ordinary" },
    { num: "V-335E", via: "Kempegowda Bus Station → Whitefield", freq: "Every 6 min", type: "Vayu Vajra" },
  ]);

  const handleSearchRoute = async () => {
    if (!query.trim()) return;
    try {
      const res = await apiSearchRoutes(query);
      if (res.routes) {
        setRoutes(res.routes.map(r => typeof r === "string" ? { num: r, via: "Bengaluru Major Transit Route", freq: "Regular Service", type: "BMTC" } : r));
      }
    } catch {}
  };

  return (
    <div style={{ maxWidth: 680, margin: "28px auto", padding: "0 20px" }}>
      <div style={{ background: "linear-gradient(135deg,#6C3BF5,#9333EA)", borderRadius: "20px 20px 0 0", padding: "20px 24px", color: "#fff", display: "flex", justifyContent: "space-between" }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Search BMTC & Metro Routes</div>
        <span style={{ fontSize: 20 }}>🔍</span>
      </div>
      <div style={{ background: T.white, borderRadius: "0 0 20px 20px", padding: "24px", border: "1px solid #F0F0F8" }}>
        <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
          <input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSearchRoute()} placeholder="Enter route number (e.g. 500D, V-335E)..."
            style={{ flex: 1, padding: "12px 16px", background: "#F8F9FC", border: "1.5px solid #E5E7EB", borderRadius: 12, fontSize: 14, outline: "none" }} />
          <button onClick={handleSearchRoute} style={{ background: T.grad, border: "none", color: "#fff", padding: "12px 20px", borderRadius: 12, fontSize: 13, fontWeight: 700, cursor: "pointer" }}>
            Search
          </button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {routes.map((r, i) => (
            <div key={i} onClick={() => onSearch("Majestic", "Electronic City", "")} style={{ padding: "14px 16px", borderRadius: 14, background: "#F8F9FC", border: "1px solid #E5E7EB", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ background: T.primary, color: "#fff", padding: "3px 8px", borderRadius: 6, fontSize: 12, fontWeight: 800 }}>{r.num}</span>
                  <span style={{ fontSize: 11, color: T.muted, fontWeight: 600 }}>{r.type}</span>
                </div>
                <div style={{ fontSize: 12, color: T.text, marginTop: 4, fontWeight: 600 }}>{r.via}</div>
              </div>
              <div style={{ fontSize: 11, color: T.green, fontWeight: 700 }}>{r.freq}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FareGuidePage() {
  const [tab, setTab] = useState("bus");
  const busF = [["Up to 5 km", "₹10"], ["5 – 10 km", "₹15"], ["10 – 15 km", "₹20"], ["15 – 25 km", "₹25"], ["Above 25 km", "₹30+"]];
  const metF = [["Up to 2 km", "₹10"], ["2 – 4 km", "₹20"], ["4 – 6 km", "₹30"], ["6 – 12 km", "₹40"], ["12 – 19 km", "₹50"], ["Above 19 km", "₹60"]];
  const cabF = [["Auto Rickshaw", "₹30 base + ₹15/km"], ["Ola Mini", "₹70 base + ₹12/km"], ["Uber Go", "₹75 base + ₹13/km"]];

  return (
    <div style={{ maxWidth: 600, margin: "28px auto", padding: "0 20px" }}>
      <div style={{ background: "linear-gradient(135deg,#FF2A6D,#FF5E7E)", borderRadius: "20px 20px 0 0", padding: "20px 24px", color: "#fff", display: "flex", justifyContent: "space-between" }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Fare Guide</div>
        <span style={{ fontSize: 20 }}>🏷️</span>
      </div>
      <div style={{ background: T.white, borderRadius: "0 0 20px 20px", padding: "24px", border: "1px solid #F0F0F8" }}>
        <div style={{ display: "flex", borderBottom: "2px solid #F3F4F6", marginBottom: 20 }}>
          {[["bus", "Bus"], ["metro", "Metro"], ["cabs", "Cabs"]].map(([t, label]) => (
            <button key={t} onClick={() => setTab(t)}
              style={{ flex: 1, padding: "12px", background: "none", border: "none", borderBottom: tab === t ? "3px solid #FF2A6D" : "none", color: tab === t ? "#FF2A6D" : T.muted, fontWeight: tab === t ? 800 : 600, fontSize: 13, cursor: "pointer" }}>
              {label}
            </button>
          ))}
        </div>
        {(tab === "bus" ? busF : tab === "metro" ? metF : cabF).map(([r, f], i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid #F3F4F6", fontSize: 13 }}>
            <span style={{ color: T.text }}>{r}</span>
            <span style={{ fontWeight: 800, color: "#FF2A6D" }}>{f}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AssistantPage() {
  const [msgs, setMsgs] = useState([
    { sender: "bot", text: "Hello! 👋\nI'm your Bengaluru Transport Assistant. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");

  const send = async (text) => {
    const q = text || input;
    if (!q.trim()) return;
    setInput("");
    setMsgs(prev => [...prev, { sender: "user", text: q }]);
    try {
      const res = await apiChat(q);
      setMsgs(prev => [...prev, { sender: "bot", text: res.text || res.response || "Here is the info for your query." }]);
    } catch {
      setMsgs(prev => [...prev, { sender: "bot", text: "Unable to connect to assistant backend." }]);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "28px auto", padding: "0 20px", display: "flex", flexDirection: "column", height: "calc(100vh - 100px)" }}>
      <div style={{ background: "linear-gradient(135deg,#8E2DE2,#4A00E0)", borderRadius: "20px 20px 0 0", padding: "18px 24px", color: "#fff", display: "flex", justifyContent: "space-between" }}>
        <div style={{ fontSize: 18, fontWeight: 800 }}>Assistant</div>
        <span style={{ fontSize: 20 }}>🤖</span>
      </div>
      <div style={{ background: T.white, borderRadius: "0 0 20px 20px", padding: "20px", border: "1px solid #F0F0F8", flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12, paddingBottom: 12 }}>
          {msgs.map((m, i) => (
            <div key={i} style={{ display: "flex", gap: 10, justifyContent: m.sender === "user" ? "flex-end" : "flex-start" }}>
              {m.sender === "bot" && <span style={{ fontSize: 24 }}>🤖</span>}
              <div style={{ maxWidth: "80%", padding: "12px 16px", borderRadius: m.sender === "user" ? "16px 16px 4px 16px" : "4px 16px 16px 16px", background: m.sender === "user" ? T.grad : "#F3F4F6", color: m.sender === "user" ? "#fff" : T.text, fontSize: 13, lineHeight: 1.5, whiteSpace: "pre-line" }}>
                {m.text}
              </div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Type your message…"
            style={{ flex: 1, padding: "12px 16px", background: "#F8F9FC", border: "1.5px solid #E5E7EB", borderRadius: 20, fontSize: 13, outline: "none" }} />
          <button onClick={() => send()} style={{ width: 44, height: 44, borderRadius: "50%", background: T.grad, border: "none", color: "#fff", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Ic n="send" s={18} c="#fff" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BengaluruApp() {
  const [page, setPage] = useState("home");
  const [stops, setStops] = useState({ all: [], bmtc: [], metro: [] });
  const [apiResults, setApiResults] = useState(null);
  const [routeSrc, setRouteSrc] = useState("");
  const [routeDst, setRouteDst] = useState("");
  const [routeTime, setRouteTime] = useState("");
  const [routePref, setRoutePref] = useState("cost");

  useEffect(() => {
    apiStops().then(setStops);
  }, []);

  const handleSearch = async (src, dst, time) => {
    setRouteSrc(src);
    setRouteDst(dst);
    setRouteTime(time);
    setPage("results");
    try {
      const res = await apiCompare(src, dst, time);
      setApiResults(res);
    } catch {
      setApiResults(null);
    }
  };

  const handleResults = (res, src, dst, time, pref) => {
    setApiResults(res);
    setRouteSrc(src);
    setRouteDst(dst);
    setRouteTime(time);
    setRoutePref(pref);
    setPage("results");
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", fontFamily: "'DM Sans','Segoe UI',sans-serif", background: T.bg }}>
      <Sidebar page={page} onNav={setPage} />
      <main style={{ marginLeft: 220, flex: 1, height: "100vh", overflowY: "auto" }}>
        {page === "home"      && <HomePage stops={stops} onNav={setPage} onSearch={handleSearch} />}
        {page === "plan"      && <PlanJourneyPage stops={stops} onResults={handleResults} />}
        {page === "results"   && <RouteDetailsPage apiResults={apiResults} src={routeSrc} dst={routeDst} time={routeTime} pref={routePref} onBack={() => setPage("home")} />}
        {page === "stops"     && <ExploreStopsPage stops={stops} />}
        {page === "search"    && <SearchRoutesPage onSearch={handleSearch} />}
        {page === "trips"     && <RouteDetailsPage apiResults={apiResults} src="Majestic" dst="Electronic City" time="" pref="cost" onBack={() => setPage("home")} />}
        {page === "fav"       && <HomePage stops={stops} onNav={setPage} onSearch={handleSearch} />}
        {page === "fare"      && <FareGuidePage />}
        {page === "alert"     && <HomePage stops={stops} onNav={setPage} onSearch={handleSearch} />}
        {page === "settings"  && <HomePage stops={stops} onNav={setPage} onSearch={handleSearch} />}
        {page === "help"      && <AssistantPage />}
        {page === "assistant" && <AssistantPage />}
      </main>
    </div>
  );
}
