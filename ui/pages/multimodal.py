"""Multimodal journey planning page - Modern card design."""

import streamlit as st
from multimodal.router import MultimodalRouter
from ui.styles import render_section_divider


def render():
    """Render the multimodal journey planning interface."""

    st.markdown("## 🔄 Multimodal Journey Planner")
    st.markdown(
        "Combine BMTC buses and Metro trains for the smartest journeys. "
        "Get multiple options optimized for fare and time.",
        unsafe_allow_html=True,
    )

    # Initialize router
    if "multimodal_router" not in st.session_state:
        st.session_state.multimodal_router = MultimodalRouter()

    router = st.session_state.multimodal_router

    # Get combined stops list (BMTC + Metro)
    bmtc_stops = router.bmtc.get_all_stops()
    metro_stops = router.metro.get_all_stops()
    all_stops = sorted(set(bmtc_stops + metro_stops))

    # Input section
    render_section_divider("Plan Your Journey")

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        source = st.selectbox(
            "From",
            all_stops,
            key="multimodal_src",
            placeholder="Select starting point...",
        )

    with col2:
        destination = st.selectbox(
            "To",
            all_stops,
            key="multimodal_dst",
            placeholder="Select destination...",
            index=min(1, len(all_stops) - 1),
        )

    # Search button
    col_search, col_clear = st.columns([3, 1], gap="small")

    with col_search:
        search_clicked = st.button(
            "🔍 Find Best Route", use_container_width=True, key="multimodal_search_btn"
        )

    with col_clear:
        if st.button("Clear", use_container_width=True, key="multimodal_clear_btn"):
            st.session_state.pop("multimodal_results", None)
            st.rerun()

    # Results section
    if search_clicked and source and destination:
        if source == destination:
            st.markdown(
                '<div class="warning-box">⚠️ Source and destination cannot be the same</div>',
                unsafe_allow_html=True
            )
        else:
            with st.spinner("Finding multimodal routes..."):
                try:
                    results = router.plan_multimodal(source, destination)

                    if not results:
                        st.markdown(
                            '<div class="warning-box">❌ No multimodal routes found for this journey. '
                            'Try selecting different locations or use single-mode search.</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.session_state.multimodal_results = results

                except Exception as e:
                    st.markdown(
                        f'<div class="warning-box">⚠️ {str(e)}</div>',
                        unsafe_allow_html=True
                    )

    # Display results
    if "multimodal_results" in st.session_state:
        results = st.session_state.multimodal_results

        render_section_divider(f"Journey Options ({len(results)} found)")

        # Display cards for each option
        for i, result in enumerate(results, 1):
            col_left, col_right = st.columns([1, 0.2], gap="small")

            with col_left:
                # Determine icon based on mode
                is_recommended = (i == 1)

                card_class = "transport-card transport-card-recommended" if is_recommended else "transport-card"
                tag_html = '<span class="card-tag">BEST OPTION</span>' if is_recommended else ""

                st.markdown(f"""
                <div class="{card_class}">
                    <div class="card-header">
                        <div class="card-icon-section">
                            <div class="card-icon {'card-icon-recommended' if is_recommended else ''}">
                                🔄
                            </div>
                            <div>
                                <div class="card-title">Option {i}</div>
                                <div class="card-mode">Multimodal Journey</div>
                            </div>
                        </div>
                        {tag_html}
                    </div>

                    <div class="card-details">
                        <div class="detail-row">
                            <span class="detail-label">💰 Total Fare</span>
                            <span class="detail-value">₹{result.total_fare}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">⏱️ Total Time</span>
                            <span class="detail-value">~{result.total_time} mins</span>
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

            with col_right:
                if st.button("📍", key=f"expand_{i}", help="View details"):
                    st.session_state[f"expand_{i}"] = not st.session_state.get(f"expand_{i}", False)

            # Show details if expanded
            if st.session_state.get(f"expand_{i}", False):
                st.markdown("<div style='margin-left: 1rem; margin-top: 1rem'>", unsafe_allow_html=True)

                st.markdown("**Route Breakdown:**")

                for j, leg in enumerate(result.legs, 1):
                    mode = leg.get("mode", "Unknown")
                    from_loc = leg.get("from", "")
                    to_loc = leg.get("to", "")
                    route = leg.get("route", "")
                    fare = leg.get("fare", 0)
                    time = leg.get("time", 0)

                    # Determine styling based on mode
                    if mode == "BMTC":
                        icon = "🚌"
                        color = "#1f7a6d"
                        route_text = f"Route {route}"
                    elif mode == "Metro":
                        icon = "🚇"
                        color = "#3b82f6"
                        if route == "Green":
                            route_text = '<span class="line-green">GREEN</span>'
                        elif route == "Purple":
                            route_text = '<span class="line-purple">PURPLE</span>'
                        elif route == "Yellow":
                            route_text = '<span class="line-yellow">YELLOW</span>'
                        else:
                            route_text = route
                    else:
                        icon = "🚶"
                        color = "#999"
                        route_text = "Walking"

                    st.markdown(f"""
                    <div class="transport-card" style="border-left: 4px solid {color};">
                        <div class="card-header">
                            <div>
                                <div class="card-title">{icon} Leg {j}: {mode}</div>
                                <div class="card-mode">{from_loc} → {to_loc}</div>
                                <div style="color: #6b7280; font-size: 0.85rem; margin-top: 0.5rem;">{route_text}</div>
                            </div>
                        </div>
                        <div class="card-details">
                            <div class="detail-row">
                                <span class="detail-label">💰 Fare</span>
                                <span class="detail-value">₹{fare}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">⏱️ Time</span>
                                <span class="detail-value">~{time} min</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

        # Transfer info
        st.markdown(
            '<div class="info-box">💡 <strong>Pro Tip:</strong> Allow extra time at interchange points for smooth transitions</div>',
            unsafe_allow_html=True
        )

        # Back button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Mode Selection", use_container_width=True):
            st.session_state.mode = None
            st.rerun()
