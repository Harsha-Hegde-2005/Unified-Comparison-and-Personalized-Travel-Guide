"""BMTC-only journey planning page - Modern design."""

import streamlit as st
from adapters.bmtc_adapter import BMTCAdapter
from ui.styles import render_section_divider


def render():
    """Render the BMTC-only planning interface."""

    st.markdown("## 🚌 BMTC Bus Journey Planner")
    st.markdown(
        "Plan the best BMTC journey with real-time fares and traffic-aware timing.",
        unsafe_allow_html=True,
    )

    # Initialize adapter
    if "bmtc_adapter" not in st.session_state:
        st.session_state.bmtc_adapter = BMTCAdapter()

    adapter = st.session_state.bmtc_adapter
    all_stops = adapter.get_all_stops()

    # Input section
    render_section_divider("Plan Your Journey")

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        source = st.selectbox(
            "From Stop",
            all_stops,
            key="bmtc_src",
            placeholder="Type to search source stop...",
        )

    with col2:
        destination = st.selectbox(
            "To Stop",
            all_stops,
            key="bmtc_dst",
            placeholder="Type to search destination stop...",
            index=min(1, len(all_stops) - 1),
        )

    # Travel preferences
    render_section_divider("Travel Preferences")

    use_time_preference = st.checkbox(
        "Set preferred arrival time", value=False, key="bmtc_use_time"
    )
    preferred_time = None

    if use_time_preference:
        time_input = st.text_input(
            "Enter preferred arrival time (HH:MM)",
            value="18:00",
            placeholder="e.g. 08:30 or 17:45",
            key="bmtc_pref_time",
        )
        try:
            from datetime import datetime

            parsed = datetime.strptime(time_input.strip(), "%H:%M")
            preferred_time = datetime.now().replace(
                hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0
            )
            st.markdown(
                f'<div class="success-box">✓ Targeting arrival by <strong>{parsed.hour:02d}:{parsed.minute:02d}</strong></div>',
                unsafe_allow_html=True
            )
        except ValueError:
            st.markdown(
                '<div class="warning-box">⚠️ Please enter time in HH:MM format (e.g. 08:30)</div>',
                unsafe_allow_html=True
            )

    # Search button
    col_search, col_clear = st.columns([3, 1], gap="small")

    with col_search:
        search_clicked = st.button(
            "🔍 Find Best Route", use_container_width=True, key="bmtc_search_btn"
        )

    with col_clear:
        if st.button("Clear", use_container_width=True, key="bmtc_clear_btn"):
            st.session_state.pop("bmtc_result", None)
            st.rerun()

    # Results section
    if search_clicked and source and destination:
        if source == destination:
            st.markdown(
                '<div class="warning-box">⚠️ Source and destination cannot be the same</div>',
                unsafe_allow_html=True
            )
        else:
            with st.spinner("Calculating optimal route..."):
                try:
                    result = adapter.plan(source, destination)
                    st.session_state.bmtc_result = result

                except Exception as e:
                    st.markdown(
                        f'<div class="warning-box">❌ {str(e)}</div>',
                        unsafe_allow_html=True
                    )

    # Display results
    if "bmtc_result" in st.session_state:
        result = st.session_state.bmtc_result

        render_section_divider("Journey Details")

        # Create transport card
        st.markdown(f"""
        <div class="transport-card transport-card-recommended">
            <div class="card-header">
                <div class="card-icon-section">
                    <div class="card-icon card-icon-recommended">🚌</div>
                    <div>
                        <div class="card-title">{result.source} → {result.destination}</div>
                        <div class="card-mode">BMTC Journey</div>
                    </div>
                </div>
                <span class="card-tag">BEST OPTION</span>
            </div>

            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">⏱️ Estimated Time</span>
                    <span class="detail-value">~{result.total_time} mins</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">💰 Total Fare</span>
                    <span class="detail-value">₹{result.total_fare}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">🔄 Transfers</span>
                    <span class="detail-value">{result.transfers}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
        )

        # Route breakdown
        render_section_divider("Route Breakdown")

        if result.legs:
            for i, leg in enumerate(result.legs, 1):
                route_no = leg.get("route", "")
                from_stop = leg.get("from", "")
                to_stop = leg.get("to", "")
                leg_fare = leg.get("fare", 0)
                leg_time = leg.get("time", 0)
                instructions = leg.get("instructions", "")

                st.markdown(f"""
                <div class="transport-card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">🚌 Leg {i}: Route {route_no}</div>
                            <div class="card-mode">{from_stop} → {to_stop}</div>
                            <div style="color: #6b7280; font-size: 0.85rem; margin-top: 0.5rem;">{instructions}</div>
                        </div>
                    </div>
                    <div class="card-details">
                        <div class="detail-row">
                            <span class="detail-label">💰 Fare</span>
                            <span class="detail-value">₹{leg_fare}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">⏱️ Time</span>
                            <span class="detail-value">~{leg_time} min</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
                )
        else:
            st.info("No direct route found.")

        # Back button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Mode Selection", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
