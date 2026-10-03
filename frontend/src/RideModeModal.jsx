import React, { useState, useEffect, useRef } from "react";

import { API_BASE_URL } from "./config";

const API_BASE = API_BASE_URL;

// Helper for Text-To-Speech
const speakText = (text) => {
  if (!("speechSynthesis" in window)) return;
  try {
    window.speechSynthesis.cancel(); // Stop active speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.lang = "en-IN"; // Indian English pronunciation if available
    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.error("Speech synthesis error:", err);
  }
};

export default function RideModeModal({ isOpen, onClose, initialData = null }) {
  // Mode Selection: 'SETUP', 'TRACKING', 'SUMMARY'
  const [step, setStep] = useState("SETUP");
  const [rideType, setRideType] = useState("BUS"); // 'BUS' | 'METRO'

  // Route Data Options
  const [popularBusRoutes, setPopularBusRoutes] = useState([]);
  const [allBusRoutes, setAllBusRoutes] = useState([]);
  const [metroLines, setMetroLines] = useState({});

  // Bus Setup State
  const [selectedBusNumber, setSelectedBusNumber] = useState("");
  const [busSearchQuery, setBusSearchQuery] = useState("");
  const [busStops, setBusStops] = useState([]);
  const [busDestination, setBusDestination] = useState("");

  // Metro Setup State
  const [selectedMetroLine, setSelectedMetroLine] = useState("");
  const [metroStations, setMetroStations] = useState([]);
  const [metroOrigin, setMetroOrigin] = useState("");
  const [metroDestination, setMetroDestination] = useState("");

  // Alert Settings & Preferences
  const [notificationMode, setNotificationMode] = useState("REMINDER_AND_VOICE"); // 'REMINDER_ONLY' | 'REMINDER_AND_VOICE'
  const [alertSettings, setAlertSettings] = useState({
    threeStops: true,
    twoStops: true,
    oneStop: true,
    destination: true,
  });

  // Active Ride Live State
  const [rideSession, setRideSession] = useState(null);
  const [currentStopIndex, setCurrentStopIndex] = useState(0);
  const [userLocation, setUserLocation] = useState(null);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsError, setGpsError] = useState(null);
  const [triggeredAlerts, setTriggeredAlerts] = useState([]);
  const [activeNotification, setActiveNotification] = useState(null);
  const [offRouteWarningDismissed, setOffRouteWarningDismissed] = useState(false);
  const [rideStartTime, setRideStartTime] = useState(null);
  const [rideSummaryData, setRideSummaryData] = useState(null);

  // Polling interval reference
  const gpsIntervalRef = useRef(null);

  // Load initial bus routes and metro lines on mount
  useEffect(() => {
    fetchBusRoutes();
    fetchMetroLines();

    // Check for persisted active ride session in localStorage
    const savedSession = localStorage.getItem("bmtc_active_ride_session");
    if (savedSession) {
      try {
        const parsed = JSON.parse(savedSession);
        if (parsed && parsed.rideSession) {
          setRideSession(parsed.rideSession);
          setCurrentStopIndex(parsed.currentStopIndex || 0);
          setNotificationMode(parsed.notificationMode || "REMINDER_AND_VOICE");
          setAlertSettings(parsed.alertSettings || { threeStops: true, twoStops: true, oneStop: true, destination: true });
          setTriggeredAlerts(parsed.triggeredAlerts || []);
          setRideStartTime(parsed.rideStartTime || Date.now());
          setStep("TRACKING");
        }
      } catch (err) {
        console.error("Failed to restore ride session:", err);
      }
    }
  }, []);

  // Handle initialData passed from trip card & trigger GPS auto-detection on setup
  useEffect(() => {
    if (isOpen && step === "SETUP") {
      requestGpsLocation();
    }
    if (initialData && isOpen && step === "SETUP") {
      if (initialData.type === "METRO") {
        setRideType("METRO");
        if (initialData.line) {
          setSelectedMetroLine(initialData.line);
        }
      } else if (initialData.type === "BUS") {
        setRideType("BUS");
        if (initialData.busNumber) {
          setSelectedBusNumber(initialData.busNumber);
        }
      }
    }
  }, [initialData, isOpen, step]);

  // Compute GPS-detected nearest current stop
  const detectedCurrentStopIndex = React.useMemo(() => {
    const list = rideType === "BUS" ? busStops : metroStations;
    if (!userLocation || !list || list.length === 0) return 0;
    let minDistance = Infinity;
    let bestIdx = 0;
    list.forEach((st, idx) => {
      if (st.lat && st.lng && userLocation.lat && userLocation.lng) {
        const d = Math.hypot(st.lat - userLocation.lat, st.lng - userLocation.lng);
        if (d < minDistance) {
          minDistance = d;
          bestIdx = idx;
        }
      }
    });
    return bestIdx;
  }, [userLocation, busStops, metroStations, rideType]);

  const detectedCurrentStopObj = (rideType === "BUS" ? busStops : metroStations)[detectedCurrentStopIndex] || null;

  // Save session state to localStorage when tracking
  useEffect(() => {
    if (step === "TRACKING" && rideSession) {
      const sessionData = {
        rideSession,
        currentStopIndex,
        notificationMode,
        alertSettings,
        triggeredAlerts,
        rideStartTime,
      };
      localStorage.setItem("bmtc_active_ride_session", JSON.stringify(sessionData));
    }
  }, [step, rideSession, currentStopIndex, notificationMode, alertSettings, triggeredAlerts, rideStartTime]);

  const fetchBusRoutes = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ride/bus/routes`);
      const data = await res.json();
      setPopularBusRoutes(data.popular_routes || ["500C", "335E", "500D", "KBS-1", "KBS-3E", "500A"]);
      setAllBusRoutes(data.all_routes || data.routes || []);
    } catch (err) {
      console.error("Failed to fetch bus routes:", err);
    }
  };

  const fetchMetroLines = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/ride/metro/lines`);
      const data = await res.json();
      if (data.lines) {
        setMetroLines(data.lines);
        const lineNames = Object.keys(data.lines);
        if (lineNames.length > 0 && !selectedMetroLine) {
          setSelectedMetroLine(lineNames[0]);
          const normStations = (data.lines[lineNames[0]] || []).map((st) => ({
            ...st,
            stop_name: st.stop_name || st.name || "Station",
          }));
          setMetroStations(normStations);
          if (normStations.length > 0) {
            setMetroOrigin(normStations[0].stop_name);
            setMetroDestination(normStations[normStations.length - 1].stop_name);
          }
        }
      }
    } catch (err) {
      console.error("Failed to fetch metro lines:", err);
    }
  };

  // Fetch stops when bus number changes
  useEffect(() => {
    if (selectedBusNumber) {
      fetchBusStops(selectedBusNumber);
    }
  }, [selectedBusNumber]);

  const fetchBusStops = async (busNo) => {
    if (!busNo) return;
    try {
      const res = await fetch(`${API_BASE}/api/ride/bus/stops?route=${encodeURIComponent(busNo)}`);
      const data = await res.json();
      if (data.stops) {
        const normStops = data.stops.map((st) => ({
          ...st,
          stop_name: st.stop_name || st.name || "Stop",
        }));
        setBusStops(normStops);
        if (normStops.length > 0) {
          setBusDestination(normStops[normStops.length - 1].stop_name);
        } else {
          setBusDestination("");
        }
      }
    } catch (err) {
      console.error("Failed to fetch bus stops:", err);
    }
  };


  // Handle Metro line change
  const handleMetroLineChange = (lineName) => {
    setSelectedMetroLine(lineName);
    const stations = metroLines[lineName] || [];
    setMetroStations(stations);
    if (stations.length > 0) {
      setMetroOrigin(stations[0].stop_name);
      setMetroDestination(stations[stations.length - 1].stop_name);
    }
  };

  // Get current GPS position
  const requestGpsLocation = () => {
    if (!navigator.geolocation) {
      setGpsError("Geolocation is not supported by your browser.");
      return;
    }
    setGpsLoading(true);
    setGpsError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGpsLoading(false);
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(coords);
      },
      (err) => {
        setGpsLoading(false);
        setGpsError("Unable to acquire GPS location. You can advance stops manually.");
        console.warn("GPS error:", err);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    );
  };

  // Start Ride
  const handleStartRide = async () => {
    let stopsToUse = [];
    let destName = "";
    let vehicleName = "";

    if (rideType === "BUS") {
      if (!selectedBusNumber) {
        alert("Please select or enter a bus number.");
        return;
      }
      if (!busDestination) {
        alert("Please select a destination stop.");
        return;
      }
      stopsToUse = busStops;
      destName = busDestination;
      vehicleName = `Bus ${selectedBusNumber}`;
    } else {
      if (!selectedMetroLine) {
        alert("Please select a Metro Line.");
        return;
      }
      if (!metroDestination) {
        alert("Please select a destination station.");
        return;
      }
      stopsToUse = metroStations;
      destName = metroDestination;
      vehicleName = selectedMetroLine;
    }

    if (!stopsToUse || stopsToUse.length === 0) {
      alert("No route stops available. Please pick a valid route.");
      return;
    }

    const session = {
      rideType,
      vehicleName,
      routeId: rideType === "BUS" ? selectedBusNumber : selectedMetroLine,
      destination: destName,
      stops: stopsToUse,
      totalStopsCount: stopsToUse.length,
    };

    setRideSession(session);
    setCurrentStopIndex(detectedCurrentStopIndex || 0);
    setTriggeredAlerts([]);
    setRideStartTime(Date.now());
    setOffRouteWarningDismissed(false);
    setStep("TRACKING");

    // Perform initial stop snapping
    if (userLocation) {
      await performStopSnap(userLocation, stopsToUse, destName, detectedCurrentStopIndex || 0);
    } else {
      requestGpsLocation();
    }
  };

  // Perform GPS snapping call to API
  const performStopSnap = async (location, stops, dest, currentIndex) => {
    if (!location || !stops || stops.length === 0) return;

    try {
      const res = await fetch(`${API_BASE}/api/ride/snap-stop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_lat: location.lat,
          user_lng: location.lng,
          route_stops: stops.map((s) => ({ stop_name: s.stop_name, lat: s.lat, lng: s.lng })),
          destination_stop_name: dest,
          current_stop_index: currentIndex,
        }),
      });
      const data = await res.json();
      if (data.status === "success") {
        const snappedIdx = data.current_stop ? data.current_stop.index : currentIndex;
        setCurrentStopIndex(snappedIdx);

        // Check alerts
        checkAlertThresholds(data.remaining_stops, data.current_stop ? data.current_stop.stop_name : dest);
      }
    } catch (err) {
      console.error("Failed to snap stop:", err);
    }
  };

  // GPS Polling during active ride
  useEffect(() => {
    if (step === "TRACKING" && rideSession) {
      // Start interval polling for GPS location
      gpsIntervalRef.current = setInterval(() => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              const loc = { lat: pos.coords.latitude, lng: pos.coords.longitude };
              setUserLocation(loc);
              performStopSnap(loc, rideSession.stops, rideSession.destination, currentStopIndex);
            },
            (err) => console.warn("GPS interval warning:", err),
            { enableHighAccuracy: true, timeout: 5000 }
          );
        }
      }, 10000);
    }

    return () => {
      if (gpsIntervalRef.current) {
        clearInterval(gpsIntervalRef.current);
      }
    };
  }, [step, rideSession, currentStopIndex]);

  // Check alert thresholds and trigger voice / notification
  const checkAlertThresholds = (remainingStops, stopName) => {
    let alertKey = null;
    let title = "";
    let voiceMsg = "";

    const destLabel = rideSession ? rideSession.destination : "your destination";
    const modeLabel = rideType === "METRO" ? "station" : "stop";
    const modeLabelPlural = rideType === "METRO" ? "stations" : "stops";

    if (currentStopIndex > finalDestIdx) {
      alertKey = "PASSED_DESTINATION";
      title = `⚠️ You appear to have passed your destination (${destLabel}). You may have missed your stop!`;
      voiceMsg = `Warning: You appear to have passed your destination, ${destLabel}. Please check with the conductor or station master.`;
    } else if (remainingStops === 3 && alertSettings.threeStops) {
      alertKey = "3_STOPS";
      title = `Your destination is 3 ${modeLabelPlural} away.`;
      voiceMsg = `Your destination, ${destLabel}, is three ${modeLabelPlural} away.`;
    } else if (remainingStops === 2 && alertSettings.twoStops) {
      alertKey = "2_STOPS";
      title = `Your destination is 2 ${modeLabelPlural} away. Please prepare to get down.`;
      voiceMsg = `Your destination, ${destLabel}, is two ${modeLabelPlural} away. Please prepare to get down.`;
    } else if (remainingStops === 1 && alertSettings.oneStop) {
      alertKey = "1_STOP";
      title = `Your destination is the next ${modeLabel}. Please prepare to exit.`;
      voiceMsg = `${destLabel} is the next ${modeLabel}.`;
    } else if (remainingStops === 0 && alertSettings.destination) {
      alertKey = "DESTINATION";
      title = `You have reached your destination!`;
      voiceMsg = `You have reached ${destLabel}.`;
    }


    if (alertKey && !triggeredAlerts.includes(alertKey)) {
      setTriggeredAlerts((prev) => [...prev, alertKey]);
      setActiveNotification({ title, voiceMsg, alertKey });

      if (notificationMode === "REMINDER_AND_VOICE") {
        speakText(voiceMsg);
      }
    }
  };

  // Manual stop navigation
  const handlePrevStop = () => {
    if (currentStopIndex > 0) {
      const newIdx = currentStopIndex - 1;
      setCurrentStopIndex(newIdx);
      const remaining = calculateRemainingStops(newIdx);
      checkAlertThresholds(remaining, rideSession.stops[newIdx].stop_name);
    }
  };

  const handleNextStop = () => {
    if (rideSession && currentStopIndex < rideSession.stops.length - 1) {
      const newIdx = currentStopIndex + 1;
      setCurrentStopIndex(newIdx);
      const remaining = calculateRemainingStops(newIdx);
      checkAlertThresholds(remaining, rideSession.stops[newIdx].stop_name);

      if (remaining === 0) {
        handleFinishRide(newIdx);
      }
    }
  };

  const calculateRemainingStops = (idx) => {
    if (!rideSession || !rideSession.stops) return 0;
    const destIdx = rideSession.stops.findIndex(
      (s) => s.stop_name.toLowerCase() === rideSession.destination.toLowerCase()
    );
    const targetIdx = destIdx !== -1 ? destIdx : rideSession.stops.length - 1;
    return Math.max(0, targetIdx - idx);
  };

  // Finish Ride & Show Summary
  const handleFinishRide = (finalIdx = currentStopIndex) => {
    const elapsedMinutes = rideStartTime
      ? Math.max(1, Math.round((Date.now() - rideStartTime) / 60000))
      : 15;

    const summary = {
      rideType: rideSession.rideType,
      vehicleName: rideSession.vehicleName,
      origin: rideSession.stops[0]?.stop_name || "Origin",
      destination: rideSession.destination,
      stopsTravelled: finalIdx,
      travelTimeMinutes: elapsedMinutes,
      arrivalTime: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setRideSummaryData(summary);
    localStorage.removeItem("bmtc_active_ride_session");
    setStep("SUMMARY");
  };

  const handleStartNewRide = () => {
    localStorage.removeItem("bmtc_active_ride_session");
    setRideSession(null);
    setRideSummaryData(null);
    setTriggeredAlerts([]);
    setStep("SETUP");
  };

  if (!isOpen) return null;

  // Derive current display variables during tracking
  const stops = rideSession?.stops || [];
  const destIndex = stops.findIndex(
    (s) => s.stop_name.toLowerCase() === (rideSession?.destination || "").toLowerCase()
  );
  const finalDestIdx = destIndex !== -1 ? destIndex : stops.length - 1;

  const currentStopObj = stops[currentStopIndex] || { stop_name: "Detecting..." };
  const nextStopObj = stops[currentStopIndex + 1] || (currentStopIndex === finalDestIdx ? { stop_name: "Destination Reached" } : { stop_name: "End of Route" });
  const remainingStopsCount = Math.max(0, finalDestIdx - currentStopIndex);
  const etaMinutes = remainingStopsCount * 3; // ~3 mins per stop estimate

  // Filter bus routes based on search query
  const filteredBusRoutes = busSearchQuery
    ? allBusRoutes.filter((r) => r.toLowerCase().includes(busSearchQuery.toLowerCase()))
    : popularBusRoutes;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(10, 12, 20, 0.85)",
        backdropFilter: "blur(12px)",
        zIndex: 99999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "680px",
          maxHeight: "92vh",
          backgroundColor: "#131622",
          border: "1px solid #2d3248",
          borderRadius: "24px",
          color: "#f1f3f9",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          boxShadow: "0 24px 60px rgba(0, 0, 0, 0.6)",
          fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid #23283b",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "linear-gradient(180deg, #191e30 0%, #131622 100%)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "28px" }}>
              {rideType === "BUS" ? "🚌" : "🚇"}
            </span>
            <div>
              <h2 style={{ margin: 0, fontSize: "20px", fontWeight: "700", color: "#ffffff" }}>
                {step === "TRACKING"
                  ? `${rideSession?.vehicleName || "Live Ride"} - Tracking`
                  : step === "SUMMARY"
                  ? "Ride Completed"
                  : "Ride Mode - Live Companion"}
              </h2>
              <p style={{ margin: "2px 0 0 0", fontSize: "13px", color: "#8d95ab" }}>
                {step === "TRACKING"
                  ? "Live GPS stop snapping & turn-by-turn get-down alerts"
                  : "Select your transport mode & stay updated while traveling"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "#23283b",
              border: "none",
              color: "#a0a8c0",
              fontSize: "20px",
              width: "36px",
              height: "36px",
              borderRadius: "50%",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Scrollable Content Area */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {/* Active Notification Banner if triggered */}
          {activeNotification && (
            <div
              style={{
                backgroundColor: "#7c3aed",
                borderRadius: "16px",
                padding: "16px 20px",
                marginBottom: "20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                boxShadow: "0 8px 24px rgba(124, 58, 237, 0.4)",
                animation: "pulse 2s infinite",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                <span style={{ fontSize: "28px" }}>🔔</span>
                <div>
                  <h4 style={{ margin: 0, fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                    Destination Alert!
                  </h4>
                  <p style={{ margin: "2px 0 0 0", fontSize: "14px", color: "#e9d5ff" }}>
                    {activeNotification.title}
                  </p>
                </div>
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={() => setActiveNotification(null)}
                  style={{
                    background: "rgba(255,255,255,0.25)",
                    border: "none",
                    color: "#fff",
                    padding: "8px 14px",
                    borderRadius: "10px",
                    cursor: "pointer",
                    fontWeight: "700",
                    fontSize: "13px",
                  }}
                >
                  I'm still riding 🚌
                </button>
                <button
                  onClick={() => setActiveNotification(null)}
                  style={{
                    background: "rgba(0,0,0,0.3)",
                    border: "none",
                    color: "#d1d5db",
                    padding: "8px 12px",
                    borderRadius: "10px",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "13px",
                  }}
                >
                  Dismiss
                </button>
              </div>

            </div>
          )}

          {/* STEP 1: SETUP SCREEN */}
          {step === "SETUP" && (
            <div>
              {/* Mode Selection Tabs */}
              <div style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
                <button
                  onClick={() => setRideType("BUS")}
                  style={{
                    flex: 1,
                    padding: "16px",
                    borderRadius: "16px",
                    border: rideType === "BUS" ? "2px solid #8b5cf6" : "1px solid #2d3248",
                    backgroundColor: rideType === "BUS" ? "#1e1b4b" : "#171a29",
                    color: rideType === "BUS" ? "#c4b5fd" : "#8d95ab",
                    fontSize: "16px",
                    fontWeight: "700",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "10px",
                    transition: "all 0.2s ease",
                  }}
                >
                  <span style={{ fontSize: "22px" }}>🚌</span> BMTC Bus
                </button>
                <button
                  onClick={() => setRideType("METRO")}
                  style={{
                    flex: 1,
                    padding: "16px",
                    borderRadius: "16px",
                    border: rideType === "METRO" ? "2px solid #8b5cf6" : "1px solid #2d3248",
                    backgroundColor: rideType === "METRO" ? "#1e1b4b" : "#171a29",
                    color: rideType === "METRO" ? "#c4b5fd" : "#8d95ab",
                    fontSize: "16px",
                    fontWeight: "700",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "10px",
                    transition: "all 0.2s ease",
                  }}
                >
                  <span style={{ fontSize: "22px" }}>🚇</span> Namma Metro
                </button>
              </div>

              {/* BUS SETUP */}
              {rideType === "BUS" && (
                <div>
                  <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", color: "#d1d5db" }}>
                    Select / Enter Bus Number:
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 500C, 335E, KBS-2A..."
                    value={busSearchQuery || selectedBusNumber}
                    onChange={(e) => {
                      setBusSearchQuery(e.target.value);
                      setSelectedBusNumber(e.target.value);
                    }}
                    style={{
                      width: "100%",
                      padding: "14px 16px",
                      borderRadius: "12px",
                      backgroundColor: "#171a29",
                      border: "1px solid #2d3248",
                      color: "#fff",
                      fontSize: "16px",
                      marginBottom: "12px",
                      outline: "none",
                      boxSizing: "border-box",
                    }}
                  />

                  {/* Popular Route Badges */}
                  <div style={{ marginBottom: "20px" }}>
                    <p style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#8d95ab" }}>
                      Popular BMTC Routes:
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                      {popularBusRoutes.map((rt) => (
                        <button
                          key={rt}
                          onClick={() => {
                            setSelectedBusNumber(rt);
                            setBusSearchQuery(rt);
                          }}
                          style={{
                            padding: "6px 14px",
                            borderRadius: "20px",
                            backgroundColor: selectedBusNumber === rt ? "#7c3aed" : "#23283b",
                            border: "none",
                            color: "#fff",
                            fontSize: "13px",
                            fontWeight: "600",
                            cursor: "pointer",
                          }}
                        >
                          {rt}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* GPS Auto-Detected Current / Source Stop */}
                  <div style={{
                    backgroundColor: "#171a29",
                    border: "1px solid #10b981",
                    borderRadius: "12px",
                    padding: "12px 16px",
                    marginBottom: "16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "20px" }}>📍</span>
                      <div>
                        <div style={{ fontSize: "10px", fontWeight: "700", color: "#10b981", letterSpacing: "0.05em" }}>
                          CURRENT / SOURCE STOP (AUTO-DETECTED VIA GPS)
                        </div>
                        <div style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginTop: "2px" }}>
                          {gpsLoading
                            ? "Acquiring live GPS location..."
                            : detectedCurrentStopObj
                            ? `${detectedCurrentStopObj.stop_name} (Stop #${detectedCurrentStopIndex + 1})`
                            : "GPS Active · Snapping to route"}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={requestGpsLocation}
                      style={{
                        background: "rgba(16, 185, 129, 0.15)",
                        border: "1px solid #10b981",
                        color: "#10b981",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer"
                      }}
                    >
                      {gpsLoading ? "Detecting..." : "Refresh GPS"}
                    </button>
                  </div>

                  {/* Destination Stop Selection */}
                  <div style={{ marginBottom: "24px" }}>
                    <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", color: "#d1d5db" }}>
                      Select Destination Stop:
                    </label>
                    {busStops.length > 0 ? (
                      <select
                        value={busDestination}
                        onChange={(e) => setBusDestination(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "14px 16px",
                          borderRadius: "12px",
                          backgroundColor: "#171a29",
                          border: "1px solid #2d3248",
                          color: "#fff",
                          fontSize: "16px",
                          outline: "none",
                          boxSizing: "border-box",
                        }}
                      >
                        {busStops.map((st, i) => (
                          <option key={`${st.stop_name}-${i}`} value={st.stop_name}>
                            {i + 1}. {st.stop_name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div
                        style={{
                          padding: "14px 16px",
                          borderRadius: "12px",
                          backgroundColor: "#171a29",
                          border: "1px solid #2d3248",
                          color: "#8d95ab",
                          fontSize: "14px",
                        }}
                      >
                        {selectedBusNumber
                          ? `Fetching route stops for ${selectedBusNumber}...`
                          : "Please enter or select a bus number above to view destination stops."}
                      </div>
                    )}
                  </div>
                </div>
              )}


              {/* METRO SETUP */}
              {rideType === "METRO" && (
                <div>
                  <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", color: "#d1d5db" }}>
                    Select Metro Line:
                  </label>
                  <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
                    {Object.keys(metroLines).map((lineName) => (
                      <button
                        key={lineName}
                        onClick={() => handleMetroLineChange(lineName)}
                        style={{
                          flex: 1,
                          padding: "12px",
                          borderRadius: "12px",
                          border: selectedMetroLine === lineName ? "2px solid #a78bfa" : "1px solid #2d3248",
                          backgroundColor:
                            selectedMetroLine === lineName
                              ? lineName.includes("Purple")
                                ? "#5b21b6"
                                : lineName.includes("Green")
                                ? "#065f46"
                                : "#854d0e"
                              : "#171a29",
                          color: "#fff",
                          fontWeight: "700",
                          cursor: "pointer",
                        }}
                      >
                        {lineName}
                      </button>
                    ))}
                  </div>

                  {/* GPS Auto-Detected Current Metro Station */}
                  <div style={{
                    backgroundColor: "#171a29",
                    border: "1px solid #10b981",
                    borderRadius: "12px",
                    padding: "12px 16px",
                    marginBottom: "16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between"
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "20px" }}>📍</span>
                      <div>
                        <div style={{ fontSize: "10px", fontWeight: "700", color: "#10b981", letterSpacing: "0.05em" }}>
                          CURRENT METRO STATION (AUTO-DETECTED VIA GPS)
                        </div>
                        <div style={{ fontSize: "14px", fontWeight: "700", color: "#ffffff", marginTop: "2px" }}>
                          {gpsLoading
                            ? "Acquiring live GPS location..."
                            : detectedCurrentStopObj
                            ? `${detectedCurrentStopObj.stop_name} (Station #${detectedCurrentStopIndex + 1})`
                            : "GPS Active · Snapping to station"}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={requestGpsLocation}
                      style={{
                        background: "rgba(16, 185, 129, 0.15)",
                        border: "1px solid #10b981",
                        color: "#10b981",
                        padding: "6px 12px",
                        borderRadius: "8px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer"
                      }}
                    >
                      {gpsLoading ? "Detecting..." : "Refresh GPS"}
                    </button>
                  </div>

                  {metroStations.length > 0 && (
                    <div style={{ marginBottom: "24px" }}>
                      <label style={{ display: "block", marginBottom: "8px", fontWeight: "600", color: "#d1d5db" }}>
                        Select Destination Station:
                      </label>
                      <select
                        value={metroDestination}
                        onChange={(e) => setMetroDestination(e.target.value)}
                        style={{
                          width: "100%",
                          padding: "14px 16px",
                          borderRadius: "12px",
                          backgroundColor: "#171a29",
                          border: "1px solid #2d3248",
                          color: "#fff",
                          fontSize: "16px",
                          outline: "none",
                          boxSizing: "border-box",
                        }}
                      >
                        {metroStations.map((st, i) => (
                          <option key={`${st.stop_name}-${i}`} value={st.stop_name}>
                            {i + 1}. {st.stop_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              )}

              {/* CONFIGURATION & NOTIFICATION PREFERENCES */}
              <div
                style={{
                  backgroundColor: "#171a29",
                  borderRadius: "16px",
                  padding: "20px",
                  border: "1px solid #23283b",
                  marginBottom: "24px",
                }}
              >
                <h4 style={{ margin: "0 0 14px 0", fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                  ⚙️ Notification & Alert Preferences
                </h4>

                {/* Reminder Type Selection */}
                <div style={{ marginBottom: "16px" }}>
                  <p style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#a0a8c0" }}>
                    Notification Mode:
                  </p>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <label
                      style={{
                        flex: 1,
                        padding: "12px",
                        borderRadius: "10px",
                        backgroundColor: notificationMode === "REMINDER_ONLY" ? "#2e2a4a" : "#1e2235",
                        border: notificationMode === "REMINDER_ONLY" ? "1px solid #8b5cf6" : "1px solid transparent",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontSize: "14px",
                      }}
                    >
                      <input
                        type="radio"
                        name="notifyMode"
                        checked={notificationMode === "REMINDER_ONLY"}
                        onChange={() => setNotificationMode("REMINDER_ONLY")}
                      />
                      🔔 Reminder Only
                    </label>
                    <label
                      style={{
                        flex: 1,
                        padding: "12px",
                        borderRadius: "10px",
                        backgroundColor: notificationMode === "REMINDER_AND_VOICE" ? "#2e2a4a" : "#1e2235",
                        border: notificationMode === "REMINDER_AND_VOICE" ? "1px solid #8b5cf6" : "1px solid transparent",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        fontSize: "14px",
                      }}
                    >
                      <input
                        type="radio"
                        name="notifyMode"
                        checked={notificationMode === "REMINDER_AND_VOICE"}
                        onChange={() => setNotificationMode("REMINDER_AND_VOICE")}
                      />
                      🔊 Reminder + Voice Alert
                    </label>
                  </div>
                </div>

                {/* Get-down Alert Checklist */}
                <div>
                  <p style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#a0a8c0" }}>
                    Get-Down Alert Settings:
                  </p>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                    {[
                      { key: "threeStops", label: "3 stops/stations before" },
                      { key: "twoStops", label: "2 stops/stations before" },
                      { key: "oneStop", label: "1 stop/station before" },
                      { key: "destination", label: "At destination reached" },
                    ].map((item) => (
                      <label
                        key={item.key}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          fontSize: "13px",
                          color: "#d1d5db",
                          cursor: "pointer",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={alertSettings[item.key]}
                          onChange={(e) =>
                            setAlertSettings((prev) => ({ ...prev, [item.key]: e.target.checked }))
                          }
                        />
                        {item.label}
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Start Ride CTA */}
              <button
                onClick={handleStartRide}
                style={{
                  width: "100%",
                  padding: "18px",
                  borderRadius: "16px",
                  background: "linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)",
                  border: "none",
                  color: "#fff",
                  fontSize: "18px",
                  fontWeight: "700",
                  cursor: "pointer",
                  boxShadow: "0 10px 30px rgba(124, 58, 237, 0.4)",
                  transition: "transform 0.2s ease",
                }}
              >
                🚀 Start Ride Tracking
              </button>
            </div>
          )}

          {/* STEP 2: LIVE RIDE TRACKING SCREEN */}
          {step === "TRACKING" && rideSession && (
            <div>
              {/* TOP DASHBOARD METRICS CARDS */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(2, 1fr)",
                  gap: "14px",
                  marginBottom: "20px",
                }}
              >
                {/* Current Stop */}
                <div
                  style={{
                    backgroundColor: "#1c2136",
                    padding: "16px",
                    borderRadius: "16px",
                    borderLeft: "4px solid #10b981",
                  }}
                >
                  <span style={{ fontSize: "12px", color: "#10b981", fontWeight: "700", textTransform: "uppercase" }}>
                    📍 Current Stop
                  </span>
                  <h3 style={{ margin: "6px 0 0 0", fontSize: "18px", fontWeight: "700", color: "#fff" }}>
                    {currentStopObj.stop_name}
                  </h3>
                </div>

                {/* Next Stop */}
                <div
                  style={{
                    backgroundColor: "#1c2136",
                    padding: "16px",
                    borderRadius: "16px",
                    borderLeft: "4px solid #3b82f6",
                  }}
                >
                  <span style={{ fontSize: "12px", color: "#3b82f6", fontWeight: "700", textTransform: "uppercase" }}>
                    ➡️ Next Stop
                  </span>
                  <h3 style={{ margin: "6px 0 0 0", fontSize: "18px", fontWeight: "700", color: "#fff" }}>
                    {nextStopObj.stop_name}
                  </h3>
                </div>

                {/* Destination */}
                <div
                  style={{
                    backgroundColor: "#1c2136",
                    padding: "16px",
                    borderRadius: "16px",
                    borderLeft: "4px solid #8b5cf6",
                  }}
                >
                  <span style={{ fontSize: "12px", color: "#8b5cf6", fontWeight: "700", textTransform: "uppercase" }}>
                    🏁 Destination
                  </span>
                  <h3 style={{ margin: "6px 0 0 0", fontSize: "18px", fontWeight: "700", color: "#fff" }}>
                    {rideSession.destination}
                  </h3>
                </div>

                {/* Remaining & ETA */}
                <div
                  style={{
                    backgroundColor: "#1c2136",
                    padding: "16px",
                    borderRadius: "16px",
                    borderLeft: "4px solid #f59e0b",
                  }}
                >
                  <span style={{ fontSize: "12px", color: "#f59e0b", fontWeight: "700", textTransform: "uppercase" }}>
                    ⏳ Stops Remaining & ETA
                  </span>
                  <h3 style={{ margin: "6px 0 0 0", fontSize: "18px", fontWeight: "700", color: "#fff" }}>
                    {remainingStopsCount} {rideType === "METRO" ? "stations" : "stops"} ({etaMinutes} mins)
                  </h3>
                </div>
              </div>

              {/* PROGRESS BAR */}
              <div style={{ marginBottom: "24px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "13px",
                    color: "#8d95ab",
                    marginBottom: "8px",
                  }}
                >
                  <span>Progress along route</span>
                  <span>
                    {Math.round(((currentStopIndex + 1) / Math.max(1, finalDestIdx + 1)) * 100)}%
                  </span>
                </div>
                <div
                  style={{
                    width: "100%",
                    height: "10px",
                    backgroundColor: "#23283b",
                    borderRadius: "5px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      width: `${Math.min(100, Math.round(((currentStopIndex + 1) / Math.max(1, finalDestIdx + 1)) * 100))}%`,
                      background: "linear-gradient(90deg, #10b981 0%, #7c3aed 100%)",
                      transition: "width 0.4s ease",
                    }}
                  />
                </div>
              </div>

              {/* MANUAL STOP OVERRIDE CONTROLS */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "#171a29",
                  padding: "12px 16px",
                  borderRadius: "14px",
                  border: "1px solid #23283b",
                  marginBottom: "24px",
                }}
              >
                <button
                  onClick={handlePrevStop}
                  disabled={currentStopIndex <= 0}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    backgroundColor: currentStopIndex > 0 ? "#23283b" : "#171a29",
                    border: "none",
                    color: currentStopIndex > 0 ? "#fff" : "#4b5563",
                    cursor: currentStopIndex > 0 ? "pointer" : "default",
                    fontWeight: "600",
                  }}
                >
                  ⬅ Previous Stop
                </button>
                <span style={{ fontSize: "14px", color: "#a0a8c0", fontWeight: "600" }}>
                  Stop {currentStopIndex + 1} of {finalDestIdx + 1}
                </span>
                <button
                  onClick={handleNextStop}
                  disabled={currentStopIndex >= finalDestIdx}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "10px",
                    backgroundColor: currentStopIndex < finalDestIdx ? "#7c3aed" : "#171a29",
                    border: "none",
                    color: currentStopIndex < finalDestIdx ? "#fff" : "#4b5563",
                    cursor: currentStopIndex < finalDestIdx ? "pointer" : "default",
                    fontWeight: "600",
                  }}
                >
                  Next Stop ➡️
                </button>
              </div>

              {/* UPCOMING STOPS TIMELINE */}
              <div style={{ marginBottom: "24px" }}>
                <h4 style={{ margin: "0 0 12px 0", fontSize: "15px", fontWeight: "700", color: "#d1d5db" }}>
                  📋 Upcoming Stops Timeline
                </h4>
                <div
                  style={{
                    maxHeight: "220px",
                    overflowY: "auto",
                    backgroundColor: "#171a29",
                    borderRadius: "14px",
                    border: "1px solid #23283b",
                    padding: "12px",
                  }}
                >
                  {stops.slice(0, finalDestIdx + 1).map((st, i) => {
                    const isPassed = i < currentStopIndex;
                    const isCurrent = i === currentStopIndex;
                    const isNext = i === currentStopIndex + 1;
                    const isDestination = i === finalDestIdx;

                    return (
                      <div
                        key={`${st.stop_name}-${i}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "12px",
                          padding: "10px 12px",
                          borderRadius: "10px",
                          backgroundColor: isCurrent ? "#2e2654" : "transparent",
                          opacity: isPassed ? 0.5 : 1,
                        }}
                      >
                        <div
                          style={{
                            width: "12px",
                            height: "12px",
                            borderRadius: "50%",
                            backgroundColor: isCurrent
                              ? "#10b981"
                              : isNext
                              ? "#3b82f6"
                              : isDestination
                              ? "#8b5cf6"
                              : "#4b5563",
                            border: isCurrent ? "2px solid #fff" : "none",
                          }}
                        />
                        <span
                          style={{
                            flex: 1,
                            fontSize: "14px",
                            fontWeight: isCurrent || isNext || isDestination ? "700" : "400",
                            color: isCurrent ? "#10b981" : "#e5e7eb",
                          }}
                        >
                          {i + 1}. {st.stop_name}
                        </span>
                        {isCurrent && (
                          <span
                            style={{
                              fontSize: "11px",
                              backgroundColor: "#10b981",
                              color: "#000",
                              padding: "2px 8px",
                              borderRadius: "12px",
                              fontWeight: "700",
                            }}
                          >
                            Current
                          </span>
                        )}
                        {isNext && (
                          <span
                            style={{
                              fontSize: "11px",
                              backgroundColor: "#3b82f6",
                              color: "#fff",
                              padding: "2px 8px",
                              borderRadius: "12px",
                              fontWeight: "700",
                            }}
                          >
                            Next
                          </span>
                        )}
                        {isDestination && (
                          <span
                            style={{
                              fontSize: "11px",
                              backgroundColor: "#8b5cf6",
                              color: "#fff",
                              padding: "2px 8px",
                              borderRadius: "12px",
                              fontWeight: "700",
                            }}
                          >
                            Destination
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* VOICE / NOTIFICATION QUICK TOGGLE */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "#171a29",
                  padding: "14px 18px",
                  borderRadius: "14px",
                  border: "1px solid #23283b",
                  marginBottom: "20px",
                }}
              >
                <div>
                  <span style={{ fontSize: "14px", fontWeight: "600", color: "#fff" }}>
                    Voice Alerts: {notificationMode === "REMINDER_AND_VOICE" ? "🔊 Enabled" : "🔇 Disabled"}
                  </span>
                  <p style={{ margin: "2px 0 0 0", fontSize: "12px", color: "#8d95ab" }}>
                    {notificationMode === "REMINDER_AND_VOICE"
                      ? "Audio alerts will play dynamically at approach thresholds."
                      : "Visual popups only. No speech synthesis."}
                  </p>
                </div>
                <button
                  onClick={() =>
                    setNotificationMode((prev) =>
                      prev === "REMINDER_AND_VOICE" ? "REMINDER_ONLY" : "REMINDER_AND_VOICE"
                    )
                  }
                  style={{
                    padding: "8px 14px",
                    borderRadius: "10px",
                    backgroundColor: "#23283b",
                    border: "none",
                    color: "#c4b5fd",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "13px",
                  }}
                >
                  Toggle Voice
                </button>
              </div>

              {/* FINISH RIDE CTA */}
              <button
                onClick={() => handleFinishRide(currentStopIndex)}
                style={{
                  width: "100%",
                  padding: "16px",
                  borderRadius: "14px",
                  backgroundColor: "#ef4444",
                  border: "none",
                  color: "#fff",
                  fontSize: "16px",
                  fontWeight: "700",
                  cursor: "pointer",
                  boxShadow: "0 8px 20px rgba(239, 68, 68, 0.3)",
                }}
              >
                🏁 Finish Ride & Show Summary
              </button>
            </div>
          )}

          {/* STEP 3: RIDE SUMMARY SCREEN */}
          {step === "SUMMARY" && rideSummaryData && (
            <div style={{ textAlign: "center", padding: "10px 0" }}>
              <div style={{ fontSize: "64px", marginBottom: "12px" }}>🎉</div>
              <h2 style={{ margin: "0 0 8px 0", fontSize: "24px", color: "#fff" }}>
                Ride Completed!
              </h2>
              <p style={{ color: "#a0a8c0", fontSize: "15px", marginBottom: "24px" }}>
                You have safely arrived at {rideSummaryData.destination}.
              </p>

              <div
                style={{
                  backgroundColor: "#171a29",
                  borderRadius: "20px",
                  padding: "20px",
                  border: "1px solid #23283b",
                  textAlign: "left",
                  marginBottom: "28px",
                }}
              >
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                  <div>
                    <span style={{ fontSize: "12px", color: "#8d95ab" }}>Transport Engine</span>
                    <p style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                      {rideSummaryData.vehicleName}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#8d95ab" }}>Destination</span>
                    <p style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                      {rideSummaryData.destination}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#8d95ab" }}>Stops Travelled</span>
                    <p style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: "700", color: "#fff" }}>
                      {rideSummaryData.stopsTravelled} stops
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#8d95ab" }}>Total Travel Time</span>
                    <p style={{ margin: "4px 0 0 0", fontSize: "16px", fontWeight: "700", color: "#10b981" }}>
                      {rideSummaryData.travelTimeMinutes} mins
                    </p>
                  </div>
                </div>
              </div>

              <button
                onClick={handleStartNewRide}
                style={{
                  width: "100%",
                  padding: "16px",
                  borderRadius: "14px",
                  background: "linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)",
                  border: "none",
                  color: "#fff",
                  fontSize: "17px",
                  fontWeight: "700",
                  cursor: "pointer",
                }}
              >
                🚀 Start New Ride
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
