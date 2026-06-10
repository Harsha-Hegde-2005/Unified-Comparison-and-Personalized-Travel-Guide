"""Metro-only journey planning page - Modern design."""

import streamlit as st
from adapters.metro_adapter import MetroAdapter
from ui.styles import render_section_divider


def render():
    """Render the Metro-only planning interface."""

    st.markdown("## 🚇 Bangalore Metro")
    st.markdown(
        "Find the fastest route across all metro lines. "
        "Compare token and smart card pricing.",
        unsafe_allow_html=True,
    )

    # Initialize adapter
    if "metro_adapter" not in st.session_state:
        st.session_state.metro_adapter = MetroAdapter()

    adapter = st.session_state.metro_adapter
    all_stations = sorted(adapter.get_all_stops())

    # Input section
    render_section_divider("Plan Your Journey")

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        source = st.selectbox(
            "From Station",
            all_stations,
            key="metro_src",
            placeholder="Select starting station...",
        )

    with col2:
        destination = st.selectbox(
            "To Station",
            all_stations,
            key="metro_dst",
            placeholder="Select destination station...",
            index=min(1, len(all_stations) - 1),
        )

    # Search button
    col_search, col_clear = st.columns([3, 1], gap="small")

    with col_search:
        search_clicked = st.button(
            "🔍 Find Metro Route", use_container_width=True, key="metro_search_btn"
        )

    with col_clear:
        if st.button("Clear", use_container_width=True, key="metro_clear_btn"):
            st.session_state.pop("metro_result", None)
            st.rerun()

    # Results section
    if search_clicked and source and destination:
        if source == destination:
            st.markdown(
                '<div class="warning-box">⚠️ Source and destination cannot be the same</div>',
                unsafe_allow_html=True
            )
        else:
            with st.spinner("Finding metro route..."):
                try:
                    result = st.session_state.metro_adapter.plan(source, destination)
                    st.session_state.metro_result = result

                except Exception as e:
                    st.markdown(
                        f'<div class="warning-box">❌ {str(e)}</div>',
                        unsafe_allow_html=True
                    )

    # Display results
    if "metro_result" in st.session_state:
        result = st.session_state.metro_result

        render_section_divider("Journey Details")

        # Create transport card
        fare_info = result.total_fare
        if isinstance(fare_info, dict):
            fare_token = fare_info.get("token", 0)
            fare_card = fare_info.get("smart_card", 0)
            fare_display = f"₹{fare_token} (Token) / ₹{fare_card} (Smart Card)"
        else:
            fare_display = f"₹{fare_info}"

        st.markdown(f"""
        <div class="transport-card transport-card-recommended">
            <div class="card-header">
                <div class="card-icon-section">
                    <div class="card-icon card-icon-recommended">🚇</div>
                    <div>
                        <div class="card-title">{result.source} → {result.destination}</div>
                        <div class="card-mode">Metro Journey</div>
                    </div>
                </div>
                <span class="card-tag">RECOMMENDED</span>
            </div>

            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">⏱️ Estimated Time</span>
                    <span class="detail-value">~{result.total_time} mins</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">💰 Fare</span>
                    <span class="detail-value">{fare_display}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">🔄 Transfers</span>
                    <span class="detail-value">{result.transfers}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Route breakdown
        render_section_divider("Route Breakdown")

        if result.legs:
            for i, leg in enumerate(result.legs, 1):
                line = leg.get("route", "")
                from_station = leg.get("from", "")
                to_station = leg.get("to", "")
                stations_crossed = leg.get("stations_crossed", 0)

                # Color code by line
                if line == "Green":
                    line_html = '<span class="line-green">GREEN LINE</span>'
                elif line == "Purple":
                    line_html = '<span class="line-purple">PURPLE LINE</span>'
                elif line == "Yellow":
                    line_html = '<span class="line-yellow">YELLOW LINE</span>'
                else:
                    line_html = f'<span>{line}</span>'

                st.markdown(f"""
                <div class="transport-card">
                    <div class="card-header">
                        <div>
                            <div class="card-title">Leg {i}: {line_html}</div>
                            <div class="card-mode">{from_station} → {to_station}</div>
                        </div>
                    </div>
                    <div class="card-details">
                        <div class="detail-row">
                            <span class="detail-label">Stations to cross</span>
                            <span class="detail-value">{stations_crossed}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Instructions
        if result.raw_output.get("instructions"):
            render_section_divider("Step-by-Step Instructions")
            instructions = result.raw_output["instructions"]
            for i, instruction in enumerate(instructions, 1):
                st.markdown(f"**{i}.** {instruction}")

        # Back button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Mode Selection", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
