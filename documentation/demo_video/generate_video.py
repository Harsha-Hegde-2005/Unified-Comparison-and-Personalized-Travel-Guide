import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys

def create_slide_image(width, height, chapter_num, total_chapters, title, subtitle, points, badge_text, theme_color=(124, 58, 237)):
    # Create dark base
    img = Image.new("RGB", (width, height), (18, 15, 30))
    draw = ImageDraw.Draw(img)

    # Ambient gradient glow
    for r in range(300, 0, -10):
        alpha = int(35 * (r / 300))
        glow_box = [width - 350 - r, -50 - r, width + 100 + r, 300 + r]
        draw.ellipse(glow_box, fill=(int(theme_color[0] * 0.25), int(theme_color[1] * 0.15), int(theme_color[2] * 0.35)))

    # Top Brand Bar
    draw.rectangle([0, 0, width, 70], fill=(24, 20, 38))
    draw.line([0, 70, width, 70], fill=(45, 40, 65), width=2)

    # Logo & Project Name
    # Brand Icon
    draw.rounded_rectangle([40, 15, 80, 55], radius=8, fill=(124, 58, 237))
    # Brand Text
    draw.text((95, 20), "BengaluruGo", fill=(255, 255, 255))
    draw.text((215, 24), "· Comprehensive Video Manual & Demo Walkthrough", fill=(160, 155, 180))

    # Badge Top Right
    badge_w = 260
    draw.rounded_rectangle([width - badge_w - 40, 18, width - 40, 52], radius=10, fill=(35, 30, 50), outline=(80, 70, 110))
    draw.text((width - badge_w - 25, 25), f"CHAPTER {chapter_num}/{total_chapters}: {badge_text.upper()}", fill=(220, 180, 255))

    # Title Section
    draw.text((60, 105), f"Module {chapter_num}: {title}", fill=(255, 255, 255))
    draw.text((60, 145), subtitle, fill=(180, 175, 205))
    draw.line([60, 180, width - 60, 180], fill=(50, 45, 75), width=1)

    # Left Column: Features Card
    card_left = 60
    card_top = 205
    card_w = 720
    card_h = 440
    draw.rounded_rectangle([card_left, card_top, card_left + card_w, card_top + card_h], radius=16, fill=(28, 24, 44), outline=(55, 48, 80), width=2)
    draw.rectangle([card_left, card_top, card_left + card_w, card_top + 45], fill=(36, 30, 56))
    draw.text((card_left + 24, card_top + 14), "KEY HIGHLIGHTS & OPERATIONAL MANUAL", fill=(168, 85, 247))

    y_offset = card_top + 65
    for i, pt in enumerate(points):
        # Bullet indicator
        draw.rounded_rectangle([card_left + 24, y_offset + 3, card_left + 36, y_offset + 15], radius=4, fill=(124, 58, 237))
        # Bullet text
        draw.text((card_left + 48, y_offset), f"{pt['label']}:", fill=(240, 240, 255))
        draw.text((card_left + 48, y_offset + 22), pt['desc'], fill=(165, 160, 190))
        y_offset += 68

    # Right Column: Visual Architecture / Interactive Simulation Card
    r_left = 810
    r_top = 205
    r_w = 410
    r_h = 440
    draw.rounded_rectangle([r_left, r_top, r_left + r_w, r_top + r_h], radius=16, fill=(24, 20, 38), outline=(55, 48, 80), width=2)
    draw.rectangle([r_left, r_top, r_left + r_w, r_top + 45], fill=(33, 27, 52))
    draw.text((r_left + 20, r_top + 14), "LIVE SYSTEM ARCHITECTURE", fill=(56, 189, 248))

    # Right card details
    ry = r_top + 65
    draw.text((r_left + 20, ry), "Status: ACTIVE & VERIFIED", fill=(52, 211, 153))
    ry += 30
    draw.text((r_left + 20, ry), "Target: Web (Desktop/Mobile) & App", fill=(200, 200, 220))
    ry += 30
    draw.line([r_left + 20, ry, r_left + r_w - 20, ry], fill=(50, 45, 70), width=1)
    ry += 15

    # Mini simulation wireframe
    draw.rounded_rectangle([r_left + 20, ry, r_left + r_w - 20, ry + 160], radius=10, fill=(16, 13, 26), outline=(70, 60, 100))
    draw.text((r_left + 35, ry + 15), "⚡ Transit Optimization Core", fill=(244, 114, 182))
    draw.text((r_left + 35, ry + 40), "• Real-Time GTFS & BMTC Routes", fill=(170, 165, 195))
    draw.text((r_left + 35, ry + 65), "• BMRCL Purple & Green Metro Matrix", fill=(170, 165, 195))
    draw.text((r_left + 35, ry + 90), "• Live Traffic Delay Sensor", fill=(170, 165, 195))
    draw.text((r_left + 35, ry + 115), "• 2-Way Ride Navigation Engine", fill=(170, 165, 195))

    # Architecture tags
    ry += 180
    tags = ["FastAPI Backend", "React 19 + Vite", "Flutter Mobile", "JWT Security", "Leaflet Maps"]
    tx = r_left + 20
    for tag in tags:
        draw.rounded_rectangle([tx, ry, tx + 170 if len(tag) > 12 else tx + 120, ry + 26], radius=6, fill=(35, 30, 55), outline=(75, 65, 105))
        draw.text((tx + 10, ry + 6), tag, fill=(210, 205, 230))
        tx += 185 if len(tag) > 12 else 135
        if tx > r_left + r_w - 100:
            tx = r_left + 20
            ry += 35

    # Bottom Progress Bar
    progress_w = int(width * (chapter_num / total_chapters))
    draw.rectangle([0, height - 20, width, height], fill=(15, 12, 24))
    draw.rectangle([0, height - 20, progress_w, height], fill=theme_color)
    draw.text((20, height - 17), f"Chapter {chapter_num} of {total_chapters} · BengaluruGo Complete Walkthrough Manual", fill=(255, 255, 255))

    return np.array(img)

def generate_video(output_path="BengaluruGo_Comprehensive_Walkthrough.mp4"):
    width, height = 1280, 720
    fps = 24
    seconds_per_slide = 5
    frames_per_slide = fps * seconds_per_slide
    fade_frames = 12

    chapters = [
        {
            "num": 1,
            "title": "Welcome to BengaluruGo - Project Overview",
            "subtitle": "Bengaluru's Unified Multi-Modal Transit Guide & Intelligent Commuter Ecosystem",
            "badge": "Overview",
            "theme": (124, 58, 237),
            "points": [
                {"label": "Project Mission", "desc": "Seamlessly integrates Bus (BMTC), Metro (BMRCL), Cabs, Auto, Personal & Walk modes into one unified platform."},
                {"label": "Universal Reach", "desc": "Cross-platform accessibility with React 19 web app and Flutter native mobile application."},
                {"label": "Core Objectives", "desc": "Provide real-time schedules, fare transparency, congestion avoidance, and multi-criteria journey optimization."},
                {"label": "User-Centric Architecture", "desc": "Modern glassmorphism interface, dark mode aesthetic, and 100% responsive viewport scaling."}
            ]
        },
        {
            "num": 2,
            "title": "Authentication & Secure Profile Vault",
            "subtitle": "Dual-mode Landing Portal, JWT Token Security & Local Storage Persistence",
            "badge": "Security",
            "theme": (79, 70, 229),
            "points": [
                {"label": "High-Impact Landing Page", "desc": "Clean CTA triggers ('Get Started', 'Sign In') introducing commuters to multimodal benefits."},
                {"label": "Dual-Mode Auth Modal", "desc": "Instant switching between Login and Registration with real-time field validation."},
                {"label": "Stateful Session Handling", "desc": "Secure JWT bearer token generation, localStorage sync, and automatic session restoration."},
                {"label": "Guest & Member Access", "desc": "Seamless journey preview with personalized user vaults for registered commuters."}
            ]
        },
        {
            "num": 3,
            "title": "1-Page Non-Scrollable Home Dashboard",
            "subtitle": "Compact Desktop & Mobile Layout, Dynamic Greeting & Landmark Skyline",
            "badge": "Home Hub",
            "theme": (147, 51, 234),
            "points": [
                {"label": "Time-Aware Dynamic Greeting", "desc": "Greets travelers with 'Good Morning', 'Good Afternoon', or 'Good Evening' based on real-time clock."},
                {"label": "Plan Journey Direct Button", "desc": "Positioned beside the greeting and above the cityscape illustration for instant 1-tap route planning."},
                {"label": "Non-Scrollable Viewport", "desc": "Zero vertical scroll overflow on desktop—all tools and feature tiles fit comfortably in single view."},
                {"label": "Feature Grid Navigation", "desc": "Modular full-page drawers for Saved Places, Recent Searches, Garage, Glovebox, and Quick Actions."}
            ]
        },
        {
            "num": 4,
            "title": "Saved Places & Recent Searches Hub",
            "subtitle": "Instant 1-Click Commute Triggering with Cached Origin-Destination Pairs",
            "badge": "Fast Travel",
            "theme": (236, 72, 153),
            "points": [
                {"label": "Saved Places Bookmarks", "desc": "Save frequent spots like 'Home', 'Office', 'College' with customizable tags and transit preferences."},
                {"label": "1-Tap Route Planner Query", "desc": "Clicking any saved place instantly fires the route comparison engine without re-typing stop names."},
                {"label": "Recent Searches History", "desc": "Chronological journey audit trail preserving origin, destination, time, and preferred mode."},
                {"label": "Offline & Cloud Sync", "desc": "Local caching ensures instant recall even during spotty underground metro connectivity."}
            ]
        },
        {
            "num": 5,
            "title": "My Garage & Real-Time Commute Costing",
            "subtitle": "Personal Vehicle Registry (Car, Bike, EV) with Accurate Fuel & Carbon Tracking",
            "badge": "Garage",
            "theme": (16, 185, 129),
            "points": [
                {"label": "Vehicle Portfolio", "desc": "Add multiple vehicles with make, model, fuel type (Petrol, Diesel, CNG, Electric), and year."},
                {"label": "Dynamic Mileage Calibration", "desc": "Computes exact running cost per km based on live Bengaluru fuel rates and vehicle fuel efficiency."},
                {"label": "EV Charging & Range Analysis", "desc": "Tracks battery state-of-charge, energy consumption (kWh/km), and eco emission savings vs ICE vehicles."},
                {"label": "Active Vehicle Switching", "desc": "Toggle primary vehicle to immediately update private vehicle estimates in comparison results."}
            ]
        },
        {
            "num": 6,
            "title": "Digital Glovebox & Document Vault",
            "subtitle": "Secure Storage & In-App Viewer for Vehicle RC, Insurance, PUC & Driving License",
            "badge": "Docs Vault",
            "theme": (14, 165, 233),
            "points": [
                {"label": "Multi-Document Management", "desc": "Stores Registration Certificate (RC), Insurance Policy, Pollution Certificate (PUC), and Driving License."},
                {"label": "Built-In Document Viewer", "desc": "Open uploaded PDF documents and high-res image files directly within the app without external apps."},
                {"label": "Expiry Notifications", "desc": "Automatic color-coded badges highlighting impending insurance or PUC renewal deadlines."},
                {"label": "Cross-Platform Access", "desc": "Universal file availability across both Web dashboard and Flutter native mobile screens."}
            ]
        },
        {
            "num": 7,
            "title": "Multi-Modal Route Planner & Comparison Matrix",
            "subtitle": "Pareto Multi-Criteria Optimization Across BMTC, Metro, Cabs, Auto & Eco Modes",
            "badge": "Trip Planner",
            "theme": (245, 158, 11),
            "points": [
                {"label": "Intelligent Stop Auto-Complete", "desc": "Predictive dropdown querying 500+ Bengaluru transit stops, metro stations, and key landmarks."},
                {"label": "Multi-Criteria Sorting (Pareto)", "desc": "Filter journeys by Cheapest (Cost-first), Fastest (Time-first), or Comfortable (Transfer-minimized)."},
                {"label": "Side-by-Side Comparison Matrix", "desc": "Transparently shows cost, travel time, transfer counts, carbon footprint, and convenience score."},
                {"label": "Multimodal Hybrid Trips", "desc": "Discovers combined Bus + Metro + Walking routes for optimal city crossing."}
            ]
        },
        {
            "num": 8,
            "title": "Dedicated Mode View & 'See All Buses' Detail",
            "subtitle": "Independent Deep-Dive Pages for BMTC Bus, Namma Metro & Cabs",
            "badge": "Mode Detail",
            "theme": (239, 68, 68),
            "points": [
                {"label": "Dedicated BMTC Bus Page", "desc": "Dedicated view featuring direct bus options, connecting transfers, and fare breakdown."},
                {"label": "'See All Buses' Modal", "desc": "Lists every scheduled BMTC bus number (e.g. 500D, 335E, KIA-9) servicing the selected corridor."},
                {"label": "Metro Lines Navigator", "desc": "Displays Purple and Green line transfers, interchange at Majestic, and platform numbers."},
                {"label": "Streamlined Cab Results", "desc": "Clean fare estimates for Auto, Mini, Prime, and Bike Taxi with surcharge transparency."}
            ]
        },
        {
            "num": 9,
            "title": "Interactive Leaflet GPS Map & Linear Schematic",
            "subtitle": "Dual-View Route Visualizer with Real-Time Traffic Layer & Transit Nodes",
            "badge": "Mapping",
            "theme": (99, 102, 241),
            "points": [
                {"label": "Interactive Leaflet GPS Map", "desc": "High-resolution map with route polylines, start/stop pins, transfer interchanges, and station markers."},
                {"label": "Multi-Style Basemaps", "desc": "Switch seamlessly between OpenStreetMap, Dark Carto, Satellite, and Navigation views."},
                {"label": "Linear Route Schematic", "desc": "Step-by-step subway-style linear diagram illustrating exact sequence of upcoming stops."},
                {"label": "Congestion Heat Overlay", "desc": "Live traffic congestion highlights along major bottlenecks (Silk Board, Outer Ring Road, Tin Factory)."}
            ]
        },
        {
            "num": 10,
            "title": "Active Ride Mode & Turn-by-Turn Navigation",
            "subtitle": "Bidirectional 2-Way Travel, Flexible Intermediate Boarding & Live Stop Tracker",
            "badge": "Navigation",
            "theme": (168, 85, 247),
            "points": [
                {"label": "Bidirectional 2-Way Mode", "desc": "Instant toggle between Forward (A → B) and Return (B → A) directions on any route."},
                {"label": "Intermediate Stop Boarding", "desc": "Select any middle station if boarding midway; route automatically recalibrates remaining stops."},
                {"label": "Simulated GPS & Stop Alerts", "desc": "Live next-stop announcement cards, progress percentage bar, and arrival distance countdown."},
                {"label": "Unified Single Navigation Bar", "desc": "Streamlined action bar housing Ride Mode, Start Navigation, and Save Route actions."}
            ]
        },
        {
            "num": 11,
            "title": "Transit Intelligence Tools & Weather Advisory",
            "subtitle": "Timetables, Route Lookup, Nearby Stops, Stage Fare Matrix & Rain Fallbacks",
            "badge": "Transit Intel",
            "theme": (20, 184, 166),
            "points": [
                {"label": "Route Lookup & Timetables", "desc": "Search any BMTC or Metro route code to inspect complete stop sequences and departure hours."},
                {"label": "Nearest Stops Geo-Finder", "desc": "Locate bus stops and metro entrances within 500m to 1km radius of current GPS coordinates."},
                {"label": "Stage Fare Calculator", "desc": "Official BMTC stage distance matrix and BMRCL distance-based fare tier lookup."},
                {"label": "Smart Weather Fallback", "desc": "Detects heavy Bengaluru rain and proactively recommends weather-resilient transport modes."}
            ]
        },
        {
            "num": 12,
            "title": "AI Transit Assistant Chatbot & Summary",
            "subtitle": "Natural Language Commute Co-Pilot & Production Deployment Wrap-Up",
            "badge": "AI & Summary",
            "theme": (139, 92, 246),
            "points": [
                {"label": "AI Floating Transit Bot", "desc": "Conversational assistant: 'How do I reach Whitefield from Banashankari?' auto-fills routes."},
                {"label": "Production Deployed", "desc": "Live frontend on Vercel, FastAPI backend, synced GitHub repository with continuous integration."},
                {"label": "Scalable & Extensible", "desc": "Modular architecture ready for smart ticketing, live GPS bus telematics, and metro QR passes."},
                {"label": "BengaluruGo - Commute Smarter", "desc": "Empowering Bengaluru commuters with time savings, cost transparency, and seamless mobility."}
            ]
        }
    ]

    total_chapters = len(chapters)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, float(fps), (width, height))

    print(f"Generating comprehensive walkthrough video ({total_chapters} chapters)...")

    # Generate each slide
    slide_images = []
    for chap in chapters:
        slide_img = create_slide_image(
            width, height,
            chap["num"], total_chapters,
            chap["title"], chap["subtitle"],
            chap["points"], chap["badge"],
            chap["theme"]
        )
        slide_images.append(slide_img)

    # Render frames with smooth cross-fade transitions
    for idx, current_slide in enumerate(slide_images):
        print(f"Encoding Chapter {idx + 1}/{total_chapters}: {chapters[idx]['title']}...")
        
        # Display static slide frames
        for _ in range(frames_per_slide - fade_frames):
            # OpenCV expects BGR
            bgr_frame = cv2.cvtColor(current_slide, cv2.COLOR_RGB2BGR)
            out.write(bgr_frame)

        # Cross-fade to next slide (or fade to black if last)
        next_slide = slide_images[idx + 1] if idx + 1 < len(slide_images) else np.zeros_like(current_slide)
        for f in range(fade_frames):
            alpha = (f + 1) / float(fade_frames)
            blended = cv2.addWeighted(current_slide, 1.0 - alpha, next_slide, alpha, 0)
            bgr_frame = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
            out.write(bgr_frame)

    out.release()
    print(f"Video created successfully at: {output_path}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "BengaluruGo_Comprehensive_Walkthrough.mp4"
    generate_video(out_file)
