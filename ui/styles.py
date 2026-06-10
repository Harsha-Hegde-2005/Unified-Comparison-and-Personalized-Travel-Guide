"""Shared Streamlit styles for unified transport planner - matching React design."""

import streamlit as st


def inject_styles():
    """Inject custom CSS styles for the app - modern React-inspired design."""
    st.markdown(
        """
    <style>
        /* Reset and base styles */
        * {
            box-sizing: border-box;
        }

        body {
            background-color: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
        }

        /* Main container */
        .main {
            padding: 2rem 1rem;
        }

        /* Header styling */
        .header-container {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }

        .header-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1a1a2e;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header-subtitle {
            font-size: 1rem;
            color: #6b7280;
            font-weight: 500;
            margin-top: 0.5rem;
            max-width: 700px;
        }

        /* Mode selector buttons */
        .mode-selector {
            display: flex;
            gap: 1.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .mode-btn {
            flex: 1;
            min-width: 180px;
            padding: 1.5rem;
            border: 2px solid #e5e7eb;
            border-radius: 14px;
            background: white;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }

        .mode-btn:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
        }

        .mode-btn-active {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }

        .mode-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }

        .mode-label {
            font-weight: 700;
            font-size: 1.1rem;
            color: inherit;
        }

        /* Transport cards - matching React design */
        .transport-card {
            background: white;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            border: 1px solid #e5e7eb;
            transition: all 0.3s ease;
        }

        .transport-card:hover {
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            transform: translateY(-4px);
        }

        .transport-card-recommended {
            border: 2px solid #3b82f6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
        }

        .card-icon-section {
            display: flex;
            gap: 1rem;
            align-items: flex-start;
        }

        .card-icon {
            width: 48px;
            height: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            background: #dbeafe;
            color: #3b82f6;
        }

        .card-icon-recommended {
            background: #3b82f6;
            color: white;
        }

        .card-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #1a1a2e;
            margin: 0 0 0.25rem 0;
        }

        .card-mode {
            font-size: 0.85rem;
            color: #6b7280;
            margin: 0;
        }

        .card-tag {
            background: #3b82f6;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .card-details {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .detail-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px solid #f3f4f6;
        }

        .detail-row:last-child {
            border-bottom: none;
        }

        .detail-label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #6b7280;
            font-size: 0.95rem;
        }

        .detail-value {
            font-weight: 700;
            color: #1a1a2e;
            font-size: 1rem;
        }

        /* Buttons */
        .primary-btn {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1rem;
            width: 100%;
        }

        .primary-btn:hover {
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }

        .secondary-btn {
            background: white;
            color: #3b82f6;
            border: 2px solid #3b82f6;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .secondary-btn:hover {
            background: #f0f9ff;
        }

        /* Input fields */
        .input-field {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }

        .input-field:focus {
            border-color: #3b82f6;
            outline: none;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        /* Metro line colors */
        .line-green {
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
        }

        .line-purple {
            background: #8b5cf6;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
        }

        .line-yellow {
            background: #f59e0b;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
            display: inline-block;
        }

        /* Info boxes */
        .info-box {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #1e40af;
        }

        .warning-box {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #92400e;
        }

        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            color: #065f46;
        }

        /* Section divider */
        .section-divider {
            font-size: 0.95rem;
            font-weight: 700;
            color: #1a1a2e;
            margin: 2rem 0 1.5rem 0;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #f3f4f6;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .mode-selector {
                flex-direction: column;
            }

            .mode-btn {
                min-width: 100%;
            }

            .card-header {
                flex-direction: column;
            }

            .card-details {
                gap: 1rem;
            }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str = ""):
    """Render app header with title and subtitle."""
    st.markdown(
        f"""
    <div class="header-container">
        <div class="header-title">🚌 {title}</div>
        <div class="header-subtitle">{subtitle}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_section_divider(title: str):
    """Render section divider."""
    st.markdown(f'<div class="section-divider">{title}</div>', unsafe_allow_html=True)
