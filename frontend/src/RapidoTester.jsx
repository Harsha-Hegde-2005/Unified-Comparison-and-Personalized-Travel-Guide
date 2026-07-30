import React, { useState, useEffect, useRef } from "react";

export default function RapidoTester({ C, API_BASE }) {
  const [srcInput, setSrcInput] = useState("");
  const [srcCoords, setSrcCoords] = useState(null); // { lat, lng, name }
  const [srcPredictions, setSrcPredictions] = useState([]);
  const [showSrcMenu, setShowSrcMenu] = useState(false);

  const [dstInput, setDstInput] = useState("");
  const [dstCoords, setDstCoords] = useState(null); // { lat, lng, name }
  const [dstPredictions, setDstPredictions] = useState([]);
  const [showDstMenu, setShowDstMenu] = useState(false);

  const [time, setTime] = useState("");
  const [weather, setWeather] = useState("clear");
  const [loading, setLoading] = useState(false);
  const [estimates, setEstimates] = useState([]);
  const [error, setError] = useState(null);

  const autocompleteServiceRef = useRef(null);

  useEffect(() => {
    // Initialize current time in HH:MM format
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, "0");
    const mm = String(now.getMinutes()).padStart(2, "0");
    setTime(`${hh}:${mm}`);
  }, []);

  const getAutocompleteService = () => {
    if (window.google && !autocompleteServiceRef.current) {
      autocompleteServiceRef.current = new window.google.maps.places.AutocompleteService();
    }
    return autocompleteServiceRef.current;
  };

  const handleAutocompleteChange = (val, isSrc) => {
    if (isSrc) {
      setSrcInput(val);
      if (!val) {
        setSrcPredictions([]);
        return;
      }
    } else {
      setDstInput(val);
      if (!val) {
        setDstPredictions([]);
        return;
      }
    }

    const service = getAutocompleteService();
    if (!service) return;

    service.getPlacePredictions(
      {
        input: val,
        locationBias: {
          radius: 25000,
          center: { lat: 12.9716, lng: 77.5946 },
        },
        componentRestrictions: { country: "in" },
      },
      (predictions, status) => {
        if (window.google && status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          const list = predictions.slice(0, 5);
          if (isSrc) {
            setSrcPredictions(list);
            setShowSrcMenu(true);
          } else {
            setDstPredictions(list);
            setShowDstMenu(true);
          }
        } else {
          if (isSrc) setSrcPredictions([]);
          else setDstPredictions([]);
        }
      }
    );
  };

  const selectPlace = (p, isSrc) => {
    if (!window.google) return;
    const dummyDiv = document.createElement("div");
    const service = new window.google.maps.places.PlacesService(dummyDiv);

    service.getDetails(
      {
        placeId: p.place_id,
        fields: ["geometry", "name"],
      },
      (place, status) => {
        if (status === window.google.maps.places.PlacesServiceStatus.OK && place && place.geometry && place.geometry.location) {
          const loc = place.geometry.location;
          const lat = loc.lat();
          const lng = loc.lng();
          const name = p.structured_formatting.main_text || place.name || p.description;

          if (isSrc) {
            setSrcCoords({ lat, lng, name });
            setSrcInput(`${name} (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
            setSrcPredictions([]);
            setShowSrcMenu(false);
          } else {
            setDstCoords({ lat, lng, name });
            setDstInput(`${name} (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
            setDstPredictions([]);
            setShowDstMenu(false);
          }
        } else {
          alert("Could not fetch location coordinates. Fallback to geocoder.");
          // Geocoder Fallback
          const geocoder = new window.google.maps.Geocoder();
          geocoder.geocode({ placeId: p.place_id }, (results, status) => {
            if (status === "OK" && results && results[0]) {
              const loc = results[0].geometry.location;
              const lat = loc.lat();
              const lng = loc.lng();
              const name = p.structured_formatting.main_text || p.description;
              if (isSrc) {
                setSrcCoords({ lat, lng, name });
                setSrcInput(`${name} (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
                setSrcPredictions([]);
                setShowSrcMenu(false);
              } else {
                setDstCoords({ lat, lng, name });
                setDstInput(`${name} (${lat.toFixed(5)}, ${lng.toFixed(5)})`);
                setDstPredictions([]);
                setShowDstMenu(false);
              }
            } else {
              alert("Geocoder fallback failed too. Please try again.");
            }
          });
        }
      }
    );
  };

  const handleFetchFares = async (e) => {
    e.preventDefault();
    if (!srcCoords || !dstCoords) {
      alert("Please select both source and destination from the dropdown suggestions.");
      return;
    }

    setLoading(true);
    setError(null);
    setEstimates([]);

    try {
      const res = await fetch(`${API_BASE}/api/cab/estimate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          src_lat: srcCoords.lat,
          src_lng: srcCoords.lng,
          dst_lat: dstCoords.lat,
          dst_lng: dstCoords.lng,
          time: time,
          provider: "rapido",
          weather: weather,
        }),
      });

      if (!res.ok) {
        throw new Error(`Server returned error: ${res.status}`);
      }

      const data = await res.json();
      const rapido = data.results?.rapido || {};
      if (rapido.error) {
        setError(rapido.error);
      } else {
        setEstimates(rapido.estimates || []);
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "20px", color: C.text }}>
      {/* Header card */}
      <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: "16px", padding: "24px", marginBottom: "24px" }}>
        <h2 style={{ fontSize: "20px", fontWeight: "900", marginBottom: "8px", color: C.accent, display: "flex", alignItems: "center", gap: 10 }}>
          🛺 Rapido Pricing Tester
        </h2>
        <p style={{ fontSize: "13px", color: C.muted, marginBottom: "20px" }}>
          Verify and validate Rapido calibrated cab and bike fare estimates. Uses live Google Autocomplete for address resolution.
        </p>

        <form onSubmit={handleFetchFares} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Source Address Selection */}
          <div style={{ position: "relative" }}>
            <label style={{ fontSize: "11px", fontWeight: "700", color: C.muted, textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
              Source
            </label>
            <input
              type="text"
              value={srcInput}
              onChange={(e) => handleAutocompleteChange(e.target.value, true)}
              onFocus={() => setShowSrcMenu(true)}
              placeholder="Search source location..."
              style={{
                width: "100%",
                background: C.surface,
                border: `1px solid ${C.border2}`,
                borderRadius: "10px",
                padding: "10px 14px",
                color: C.text,
                fontSize: "13px",
                outline: "none",
                fontFamily: "inherit",
              }}
            />
            {showSrcMenu && srcPredictions.length > 0 && (
              <div style={{ position: "absolute", top: "100%", left: 0, right: 0, background: C.card, border: `1px solid ${C.border}`, borderRadius: "10px", zIndex: 10, marginTop: "4px", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)" }}>
                {srcPredictions.map((p) => (
                  <div
                    key={p.place_id}
                    onClick={() => selectPlace(p, true)}
                    style={{ padding: "10px 14px", cursor: "pointer", borderBottom: `1px solid ${C.border}`, fontSize: "12px", hover: { background: C.surface } }}
                    onMouseEnter={(e) => (e.target.style.background = C.surface)}
                    onMouseLeave={(e) => (e.target.style.background = "none")}
                  >
                    📍 {p.description}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Destination Address Selection */}
          <div style={{ position: "relative" }}>
            <label style={{ fontSize: "11px", fontWeight: "700", color: C.muted, textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
              Destination
            </label>
            <input
              type="text"
              value={dstInput}
              onChange={(e) => handleAutocompleteChange(e.target.value, false)}
              onFocus={() => setShowDstMenu(false || true)}
              placeholder="Search destination location..."
              style={{
                width: "100%",
                background: C.surface,
                border: `1px solid ${C.border2}`,
                borderRadius: "10px",
                padding: "10px 14px",
                color: C.text,
                fontSize: "13px",
                outline: "none",
                fontFamily: "inherit",
              }}
            />
            {showDstMenu && dstPredictions.length > 0 && (
              <div style={{ position: "absolute", top: "100%", left: 0, right: 0, background: C.card, border: `1px solid ${C.border}`, borderRadius: "10px", zIndex: 10, marginTop: "4px", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)" }}>
                {dstPredictions.map((p) => (
                  <div
                    key={p.place_id}
                    onClick={() => selectPlace(p, false)}
                    style={{ padding: "10px 14px", cursor: "pointer", borderBottom: `1px solid ${C.border}`, fontSize: "12px" }}
                    onMouseEnter={(e) => (e.target.style.background = C.surface)}
                    onMouseLeave={(e) => (e.target.style.background = "none")}
                  >
                    📍 {p.description}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Time & Weather */}
          <div style={{ display: "flex", gap: "16px" }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "11px", fontWeight: "700", color: C.muted, textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                Time of Journey
              </label>
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                style={{
                  width: "100%",
                  background: C.surface,
                  border: `1px solid ${C.border2}`,
                  borderRadius: "10px",
                  padding: "10px 14px",
                  color: C.text,
                  fontSize: "13px",
                  outline: "none",
                  fontFamily: "inherit",
                }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "11px", fontWeight: "700", color: C.muted, textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                Weather Condition
              </label>
              <select
                value={weather}
                onChange={(e) => setWeather(e.target.value)}
                style={{
                  width: "100%",
                  background: C.surface,
                  border: `1px solid ${C.border2}`,
                  borderRadius: "10px",
                  padding: "10px 14px",
                  color: C.text,
                  fontSize: "13px",
                  outline: "none",
                  fontFamily: "inherit",
                }}
              >
                <option value="clear">☀️ Clear / Sunny</option>
                <option value="light rain">🌧️ Light Rain / Drizzle</option>
                <option value="heavy rain">⛈️ Heavy Rain / Thunderstorm</option>
                <option value="storm">🌪️ Severe Storm / Flooding</option>
              </select>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              background: `linear-gradient(135deg, ${C.accent}, #ea580c)`,
              color: "white",
              border: "none",
              borderRadius: "10px",
              padding: "12px",
              fontWeight: "700",
              fontSize: "14px",
              cursor: "pointer",
              fontFamily: "inherit",
              marginTop: "8px",
              boxShadow: "0 4px 15px -3px rgba(249, 115, 22, 0.4)",
              transition: "transform 0.1s ease",
            }}
            onMouseDown={(e) => (e.target.style.transform = "scale(0.98)")}
            onMouseUp={(e) => (e.target.style.transform = "scale(1)")}
          >
            {loading ? "Calculating fares..." : "Get Rapido Estimates"}
          </button>
        </form>
      </div>

      {/* Error display */}
      {error && (
        <div style={{ padding: "14px", borderRadius: "10px", background: "#ef444422", border: "1px solid #ef444455", color: "#ef4444", fontSize: "13px", marginBottom: "20px" }}>
          ⚠️ <strong>Error:</strong> {error}
        </div>
      )}

      {/* Estimates Display */}
      {estimates.length > 0 && (
        <div>
          <h3 style={{ fontSize: "14px", fontWeight: "700", color: C.muted, textTransform: "uppercase", marginBottom: "12px", letterSpacing: "0.05em" }}>
            Available Rapido Fares
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {estimates.map((est) => (
              <div
                key={est.vehicle_key}
                style={{
                  background: C.card,
                  border: `1px solid ${C.border}`,
                  borderRadius: "12px",
                  padding: "16px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  transition: "border-color 0.2s ease, transform 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = C.accent;
                  e.currentTarget.style.transform = "translateY(-1px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = C.border;
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                  <div style={{ fontSize: "24px" }}>{est.icon || "🚗"}</div>
                  <div>
                    <div style={{ fontWeight: "800", fontSize: "14px" }}>{est.vehicle_name}</div>
                    <div style={{ fontSize: "12px", color: C.muted }}>{est.description}</div>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontWeight: "900", fontSize: "16px", color: C.green }}>{est.fare_display}</div>
                  <div style={{ fontSize: "11px", color: C.muted }}>
                    👥 Cap: {est.capacity} | {est.is_night ? "🌙 Night Active" : "☀️ Day Rate"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && estimates.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px", border: `1px dashed ${C.border}`, borderRadius: "16px" }}>
          <span style={{ fontSize: "28px" }}>🗺️</span>
          <p style={{ fontSize: "13px", color: C.muted, marginTop: "10px" }}>Select a source and destination to query fares.</p>
        </div>
      )}
    </div>
  );
}
