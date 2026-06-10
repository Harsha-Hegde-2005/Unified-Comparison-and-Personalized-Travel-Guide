"""Main unified entry point for Bangalore Journey Planner - UTRS Style."""

import os
import sys

# ------------------------------------------------------------------
# Fix imports when running with:
# streamlit run ui/multimodal_app.py
# ------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from ui.styles import inject_styles, render_header, render_section_divider

# Page config
st.set_page_config(
    page_title="UTRS - Unified Travel Recommendation System",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()

# Initialize mode in session state
if "mode" not in st.session_state:
    st.session_state.mode = None

# Render header
render_header(
    "Unified Travel Recommendation System",
    "Plan your journey using BMTC buses, Metro trains, or a combination of both. "
    "Compare fares, travel times, and find the best route for your needs."
)

# Mode selector with modern design
st.markdown('<div class="mode-selector">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    if st.button(
        "🚌\n\n**BMTC Only**\n\nBuses",
        use_container_width=True,
        key="btn_bmtc",
        help="Plan journeys using BMTC buses"
    ):
        st.session_state.mode = "bmtc"
        st.rerun()

with col2:
    if st.button(
        "🚇\n\n**Metro Only**\n\nTrains",
        use_container_width=True,
        key="btn_metro",
        help="Plan journeys using Metro trains"
    ):
        st.session_state.mode = "metro"
        st.rerun()

with col3:
    if st.button(
        "🔄\n\n**Multimodal**\n\nBuses + Trains",
        use_container_width=True,
        key="btn_multimodal",
        help="Combine BMTC and Metro for optimal routes"
    ):
        st.session_state.mode = "multimodal"
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Route to appropriate mode
if st.session_state.mode == "bmtc":
    from ui.pages.bmtc_only import render as render_bmtc
    render_bmtc()

elif st.session_state.mode == "metro":
    from ui.pages.metro_only import render as render_metro
    render_metro()

elif st.session_state.mode == "multimodal":
    from ui.pages.multimodal import render as render_multimodal
    render_multimodal()

else:
    # Show welcome screen with helpful info
    st.markdown('<br>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-box">
            <strong>👈 Get Started:</strong> Select a transport mode above to begin planning your journey!
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(2, gap="medium")

    with col_left:
        st.markdown("""
        <div class="transport-card">
            <h3 class="card-title">🚌 BMTC Only</h3>
            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">✓ Direct bus routes</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Real-time fares</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Traffic-aware timing</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Multiple transfers</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
        )

    with col_right:
        st.markdown("""
        <div class="transport-card">
            <h3 class="card-title">🚇 Metro Only</h3>
            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">✓ All 3 metro lines</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Fixed schedules</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Token & smart card</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">✓ Line interchange info</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
        )

    st.markdown("""
    <div class="transport-card">
        <h3 class="card-title">🔄 Multimodal (NEW)</h3>
        <div class="card-details">
            <div class="detail-row">
                <span class="detail-label">✓ Smart bus + train combos</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">✓ Automatic interchange matching</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">✓ Best fare & time options</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">✓ Optimized recommendations</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
    )
