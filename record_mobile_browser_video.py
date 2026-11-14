import http.server
import socketserver
import threading
import os
import sys
import time
import json
import subprocess
import asyncio
import websockets
import base64
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Set working directory to project root
PROJECT_ROOT = r"c:\Users\Harsh\Downloads\BMTC_fixed"
DIST_DIR = os.path.join(PROJECT_ROOT, "frontend", "dist")
OUTPUT_VIDEO = os.path.join(PROJECT_ROOT, "documentation", "demo_video", "BengaluruGo_Mobile_Demo_Walkthrough.mp4")

class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

def start_local_server(port=8099):
    httpd = socketserver.TCPServer(("127.0.0.1", port), QuietHTTPHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

class CDPController:
    def __init__(self, cdp_port=9238):
        self.cdp_port = cdp_port
        self.proc = None
        self.ws = None
        self.cmd_id = 1

    def launch_chrome(self, app_url):
        chrome_cmd = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            f"--remote-debugging-port={self.cdp_port}",
            "--window-size=390,844",
            app_url
        ]
        self.proc = subprocess.Popen(chrome_cmd)
        for _ in range(20):
            time.sleep(0.4)
            try:
                import urllib.request
                with urllib.request.urlopen(f"http://127.0.0.1:{self.cdp_port}/json/list") as resp:
                    data = json.loads(resp.read().decode())
                    if data:
                        self.ws_url = data[0]["webSocketDebuggerUrl"]
                        return
            except Exception:
                pass
        raise RuntimeError("Chrome CDP initialization timed out")

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=100*1024*1024)
        # Mobile Device Metrics override (iPhone 14 standard: 390x844, 2x scale)
        await self.send("Emulation.setDeviceMetricsOverride", {
            "width": 390,
            "height": 844,
            "deviceScaleFactor": 2,
            "mobile": True,
            "hasTouch": True
        })

    async def send(self, method, params=None):
        cid = self.cmd_id
        self.cmd_id += 1
        msg = {"id": cid, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        while True:
            raw = await self.ws.recv()
            d = json.loads(raw)
            if d.get("id") == cid:
                return d.get("result", {})

    async def eval(self, js):
        res = await self.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return res.get("result", {}).get("value")

    async def capture_frame_pil(self):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        png_bytes = base64.b64decode(res["data"])
        import io
        img = Image.open(io.BytesIO(png_bytes))
        return img.convert("RGB")

    def close(self):
        if self.proc:
            self.proc.terminate()

def overlay_mobile_frame_and_caption(mobile_img, title, subtitle, manual_tip, step_num, total_steps):
    """
    Composes a 1280x720 16:9 presentation frame:
    Left: An elegant, photorealistic iPhone mobile device mockup showing the EXACT mobile website.
    Right: Detailed project manual annotation panel explaining the feature, user action, and algorithm.
    """
    canvas_w, canvas_h = 1280, 720
    canvas = Image.new("RGB", (canvas_w, canvas_h), (16, 13, 26))
    draw = ImageDraw.Draw(canvas)

    # Ambient backdrop gradient glow
    for r in range(250, 0, -10):
        alpha = int(25 * (r / 250))
        draw.ellipse([800 - r, 360 - r, 800 + r, 360 + r], fill=(30, 20, 50))

    # --- LEFT: Mobile Phone Frame Mockup ---
    # Mobile screen target size: height 640px, width approx 296px (maintaining 390:844 ratio)
    screen_h = 630
    screen_w = int(screen_h * (390 / 844))  # ~291px
    phone_w = screen_w + 24
    phone_h = screen_h + 24
    phone_x = 70
    phone_y = (canvas_h - phone_h) // 2

    # Phone outer shadow and titanium border
    draw.rounded_rectangle([phone_x - 4, phone_y - 4, phone_x + phone_w + 4, phone_y + phone_h + 4], radius=34, fill=(10, 8, 16))
    draw.rounded_rectangle([phone_x, phone_y, phone_x + phone_w, phone_y + phone_h], radius=30, fill=(35, 30, 48), outline=(90, 80, 115), width=2)

    # Inner bezel
    screen_x = phone_x + 12
    screen_y = phone_y + 12
    draw.rounded_rectangle([screen_x - 2, screen_y - 2, screen_x + screen_w + 2, screen_y + screen_h + 2], radius=22, fill=(0, 0, 0))

    # Paste the scaled real mobile website screenshot
    resized_mobile = mobile_img.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    canvas.paste(resized_mobile, (screen_x, screen_y))

    # iPhone Dynamic Island Pill on top of screen
    pill_w = 70
    pill_h = 14
    pill_x = screen_x + (screen_w - pill_w) // 2
    pill_y = screen_y + 8
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=7, fill=(0, 0, 0))

    # Phone Home Indicator Bar at bottom
    bar_w = 90
    bar_h = 4
    bar_x = screen_x + (screen_w - bar_w) // 2
    bar_y = screen_y + screen_h - 8
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=2, fill=(255, 255, 255, 120))

    # --- RIGHT: Feature Manual & Walkthrough Explanation Panel ---
    panel_x = 420
    panel_y = 50
    panel_w = 800
    panel_h = 620

    # Brand Header Top
    draw.rounded_rectangle([panel_x, panel_y, panel_x + 36, panel_y + 36], radius=10, fill=(124, 58, 237))
    draw.text((panel_x + 10, panel_y + 8), "🚌", fill=(255, 255, 255))
    draw.text((panel_x + 48, panel_y + 4), "BengaluruGo · Mobile Demo & Manual", fill=(255, 255, 255))
    draw.text((panel_x + 48, panel_y + 24), "LIVE MOBILE WEB EXPERIENCE WALKTHROUGH", fill=(160, 150, 185))

    # Step Progress Badge
    badge_text = f"STEP {step_num} OF {total_steps}"
    draw.rounded_rectangle([panel_x + panel_w - 140, panel_y + 6, panel_x + panel_w, panel_y + 32], radius=8, fill=(35, 28, 55), outline=(124, 58, 237))
    draw.text((panel_x + panel_w - 128, panel_y + 11), badge_text, fill=(216, 180, 254))

    # Title Banner
    draw.text((panel_x, panel_y + 70), title, fill=(255, 255, 255))
    draw.text((panel_x, panel_y + 106), subtitle, fill=(180, 175, 205))
    draw.line([panel_x, panel_y + 135, panel_x + panel_w, panel_y + 135], fill=(50, 45, 75), width=1)

    # Key Manual Feature Card
    card_y = panel_y + 155
    draw.rounded_rectangle([panel_x, card_y, panel_x + panel_w, card_y + 260], radius=14, fill=(24, 20, 38), outline=(60, 50, 85), width=1)
    draw.rectangle([panel_x, card_y, panel_x + panel_w, card_y + 38], fill=(32, 26, 50))
    draw.text((panel_x + 18, card_y + 10), "MOBILE OPERATIONAL GUIDE & ALGORITHM", fill=(168, 85, 247))

    # Points list inside card
    py = card_y + 55
    for tip in manual_tip:
        draw.rounded_rectangle([panel_x + 18, py + 3, panel_x + 28, py + 13], radius=3, fill=(124, 58, 237))
        draw.text((panel_x + 38, py), tip["head"] + ":", fill=(240, 240, 255))
        draw.text((panel_x + 38, py + 22), tip["detail"], fill=(160, 155, 180))
        py += 64

    # Technical Footprint Tags
    tag_y = card_y + 280
    tags = ["React 19 Responsive Viewport", "Touch Gesture Enabled", "Pareto Route Scoring", "Zero Desktop Overflow"]
    tx = panel_x
    for tag in tags:
        tw = len(tag) * 7 + 20
        draw.rounded_rectangle([tx, tag_y, tx + tw, tag_y + 28], radius=6, fill=(28, 24, 44), outline=(70, 60, 100))
        draw.text((tx + 10, tag_y + 6), tag, fill=(200, 195, 220))
        tx += tw + 12

    # Bottom Progress Bar
    prog_w = int(canvas_w * (step_num / total_steps))
    draw.rectangle([0, canvas_h - 10, canvas_w, canvas_h], fill=(20, 16, 32))
    draw.rectangle([0, canvas_h - 10, prog_w, canvas_h], fill=(124, 58, 237))

    return np.array(canvas)

async def record_full_walkthrough():
    print("Starting in-process local HTTP server on port 8099...")
    server = start_local_server(8099)
    app_url = "http://127.0.0.1:8099/"

    print("Launching headless Chrome with iPhone 14 mobile emulation...")
    cdp = CDPController(9238)
    cdp.launch_chrome(app_url)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 20
    out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, float(fps), (1280, 720))

    try:
        await cdp.connect()
        await asyncio.sleep(2)

        walkthrough_steps = [
            {
                "title": "1. Mobile Landing Page & Responsive Viewport",
                "subtitle": "Bengaluru's Unified Multi-Modal Transit Guide on Mobile Screens",
                "action": "load_landing",
                "duration_sec": 4,
                "tips": [
                    {"head": "Responsive Mobile Layout", "detail": "Tailored touch-friendly navigation adapting seamlessly to iOS and Android viewports."},
                    {"head": "Hero Value Proposition", "detail": "Immediate summary of multi-modal benefits across bus, metro, cabs, and personal drive."},
                    {"head": "Instant Entry", "detail": "One-tap switching between guest explore mode and personalized commuter profiles."}
                ]
            },
            {
                "title": "2. Mobile Authentication & Login Flow",
                "subtitle": "Secure JWT Bearer Session Sync with Mobile-Optimized Inputs",
                "action": "open_login",
                "duration_sec": 4,
                "tips": [
                    {"head": "Mobile Auth Sheet", "detail": "Clean modal drawer with non-obstructive keyboard-friendly form controls."},
                    {"head": "JWT Security", "detail": "Encrypted credentials exchanged for secure tokens stored in client-side localStorage."},
                    {"head": "Instant Access", "detail": "Logging in unlocks personalized features: Saved Places, Garage, and Glovebox."}
                ]
            },
            {
                "title": "3. 1-Page Non-Scrollable Mobile Dashboard",
                "subtitle": "Dynamic Time Greeting & Prominent 'Plan Journey' Beside Header",
                "action": "login_and_dashboard",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Dynamic Greeting", "detail": "Automatically greets commuters with 'Good Morning', 'Good Afternoon', or 'Good Evening'."},
                    {"head": "Plan Journey Button", "detail": "Prominently positioned beside greeting and above the city skyline for instant 1-tap planning."},
                    {"head": "Non-Scrollable Single Page", "detail": "Zero vertical overflow on mobile dashboard—all tools organized in intuitive touch tiles."}
                ]
            },
            {
                "title": "4. Entering Origin & Destination in Plan Tab",
                "subtitle": "Autocomplete Stop Suggestion Engine Across 500+ Bengaluru Stations",
                "action": "open_plan_input",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Predictive Stop Search", "detail": "Instant auto-complete indexing BMTC bus stops, Namma Metro stations, and landmarks."},
                    {"head": "Preference Filters", "detail": "Commuters can toggle between Cheapest (💰), Fastest (⚡), and Comfortable (🎯)."},
                    {"head": "Real-Time Departure", "detail": "Defaults to live current time with automatic real-time delay adjustments."}
                ]
            },
            {
                "title": "5. Querying 'Silk Board' to 'Majestic' Corridor",
                "subtitle": "Selecting Source & Destination with Autocomplete Dropdowns",
                "action": "type_source_and_dest",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Origin Set: Silk Board", "detail": "Selected major junction and transit interchange connecting South and East corridors."},
                    {"head": "Destination: Majestic", "detail": "Kempegowda Bus Station / Metro interchange at the heart of Bengaluru's transit grid."},
                    {"head": "One-Click Trigger", "detail": "Tapping 'Compare All Modes' fires the Pareto multi-criteria comparison engine."}
                ]
            },
            {
                "title": "6. Mobile Comparison Results Overview",
                "subtitle": "Multi-Modal Comparison Matrix with Live Weather & Congestion Status",
                "action": "view_results_overview",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Multi-Criteria Matrix", "detail": "Side-by-side evaluation of cost, duration, transfers, comfort score, and carbon emissions."},
                    {"head": "Real-Time Traffic Sensor", "detail": "Live congestion heat alerts highlighting bottlenecks along the selected corridor."},
                    {"head": "Weather Integration", "detail": "Monitors current precipitation to recommend weather-resilient transport modes."}
                ]
            },
            {
                "title": "7. Scrolling through Mode 1: BMTC Bus",
                "subtitle": "Vajra AC, Ordinary Bus Options, Stage Fares & 'See All Buses' Action",
                "action": "scroll_bmtc",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Direct & Connecting Buses", "detail": "Displays active bus numbers (500-D, 335-E), frequency (every 5-8 mins), and ₹25 stage fare."},
                    {"head": "See All Buses Feature", "detail": "Dedicated button listing every alternative bus scheduled along the exact same route."},
                    {"head": "Start Navigation", "detail": "1-tap transition from bus results into active turn-by-turn Ride Mode."}
                ]
            },
            {
                "title": "8. Scrolling through Mode 2: Namma Metro",
                "subtitle": "Purple & Green Line Routes, Majestic Interchange & Platform Guidance",
                "action": "scroll_metro",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Interchange Optimization", "detail": "Calculates exact platform transfers at Kempegowda/Majestic station."},
                    {"head": "Predictable Timing", "detail": "High-frequency rapid transit (28 mins) immune to road surface congestion."},
                    {"head": "Token & QR Fare", "detail": "Displays official BMRCL distance-based fare tier (₹35) and train frequency."}
                ]
            },
            {
                "title": "9. Scrolling through Mode 3: Cabs & Auto-Rickshaw",
                "subtitle": "Transparent Fare Estimates for Auto, Uber/Ola Mini, Prime & Bike Taxi",
                "action": "scroll_cabs",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Dynamic Surge Transparency", "detail": "Real-time pricing for Auto-rickshaw (₹145), Cab Mini (₹260), and Prime Sedan."},
                    {"head": "Streamlined Result Card", "detail": "Clean, clutter-free fare card without obtrusive advisory banners."},
                    {"head": "Bike Taxi Option", "detail": "Quick solo commuter alternative navigating dense city traffic efficiently."}
                ]
            },
            {
                "title": "10. Scrolling through Mode 4 & 5: Garage & Eco Modes",
                "subtitle": "Personal Driving Cost vs Cycling (0 Emissions, Calorie Burn)",
                "action": "scroll_garage_eco",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "My Garage Integration", "detail": "Calculates personal fuel costs using commuter's registered vehicle mileage."},
                    {"head": "Bicycle & Walk Trajectory", "detail": "Zero-carbon active mobility tracking estimated calorie burn and walking paths."},
                    {"head": "Multimodal Hybrid", "detail": "Intelligent combinations: First-mile walk + Metro + Bus final connection."}
                ]
            },
            {
                "title": "11. Dedicated BMTC Bus Page & 'See All Buses'",
                "subtitle": "Full Corridor Inspection with Sequential Stops Table & Guidelines",
                "action": "open_bmtc_detail",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Exclusive Mode View", "detail": "Tapping BMTC opens a dedicated bus view with route guidelines and complete schedule."},
                    {"head": "All Corridor Buses", "detail": "Shows all alternative bus numbers (e.g. 500-D, 500-CA, KIA-9) on one screen."},
                    {"head": "Direct Navigation", "detail": "Launches Ride Mode directly calibrated for the selected bus service."}
                ]
            },
            {
                "title": "12. Active Ride Mode with 2-Way & Intermediate Boarding",
                "subtitle": "Bidirectional Travel (A↔B) and Flexible Intermediate Stop Boarding",
                "action": "open_ride_mode",
                "duration_sec": 5,
                "tips": [
                    {"head": "2-Way Direction Toggle", "detail": "Instant switch between Forward (A → B) and Return (B → A) with '⇄ Switch Direction'."},
                    {"head": "Intermediate Boarding", "detail": "Select any middle bus stop if boarding midway; route automatically recalibrates remaining stops."},
                    {"head": "Single Unified Action Bar", "detail": "Houses Ride Mode, Start Navigation, and Save Route in one cohesive bar."}
                ]
            },
            {
                "title": "13. Digital Glovebox & In-App Document Viewer",
                "subtitle": "Accessing Vehicle RC, Insurance & PUC with Built-in PDF Viewer",
                "action": "open_glovebox",
                "duration_sec": 4.5,
                "tips": [
                    {"head": "Integrated Document Vault", "detail": "Secure repository for vehicle Registration, Insurance, PUC, and Driving License."},
                    {"head": "Built-in PDF & Image Viewer", "detail": "Opens uploaded documents directly inside the mobile app without external viewers."},
                    {"head": "Expiry Alerts", "detail": "Badges warn commuters when insurance or emission certificates near expiry."}
                ]
            },
            {
                "title": "14. AI Transit Assistant Chatbot on Mobile",
                "subtitle": "Natural Language Commute Co-Pilot & Production Deployment Wrap-Up",
                "action": "open_chatbot",
                "duration_sec": 5,
                "tips": [
                    {"head": "Conversational AI Bot", "detail": "Understands plain English transit questions ('Fastest way to Majestic now')."},
                    {"head": "Automatic Form Population", "detail": "Populates origin, destination, and mode preferences straight from conversation."},
                    {"head": "Production Deployed", "detail": "Live on Vercel, responsive on all devices, fully verified with zero runtime crashes."}
                ]
            }
        ]

        total_steps = len(walkthrough_steps)
        print(f"Beginning live recording of {total_steps} mobile walkthrough steps...")

        for idx, step in enumerate(walkthrough_steps):
            step_num = idx + 1
            print(f"Recording Step {step_num}/{total_steps}: {step['title']}...")

            # Perform the UI action in Chrome
            if step["action"] == "load_landing":
                await cdp.eval("window.scrollTo({ top: 0, behavior: 'instant' });")
                await asyncio.sleep(1)

            elif step["action"] == "open_login":
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const loginBtn = btns.find(b => b.textContent.includes('Login') || b.textContent.includes('Sign In'));
                    if (loginBtn) loginBtn.click();
                """)
                await asyncio.sleep(1)

            elif step["action"] == "login_and_dashboard":
                await cdp.eval("""
                    localStorage.setItem('token', 'mock_jwt_verified_2026');
                    localStorage.setItem('username', 'Harsha');
                    location.reload();
                """)
                await asyncio.sleep(2.5)

            elif step["action"] == "open_plan_input":
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const planBtn = btns.find(b => b.textContent.includes('Plan Journey'));
                    if (planBtn) planBtn.click();
                """)
                await asyncio.sleep(1.5)

            elif step["action"] == "type_source_and_dest":
                await cdp.eval("""
                    const inputs = document.querySelectorAll('input');
                    if (inputs[0]) {
                        inputs[0].value = 'Silk Board';
                        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    if (inputs[1]) {
                        inputs[1].value = 'Kempegowda Bus Station (Majestic)';
                        inputs[1].dispatchEvent(new Event('input', { bubbles: true }));
                    }
                """)
                await asyncio.sleep(1)

            elif step["action"] == "view_results_overview":
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const searchBtn = btns.find(b => b.textContent.includes('Compare') || b.textContent.includes('Search') || b.textContent.includes('Plan'));
                    if (searchBtn) searchBtn.click();
                """)
                await asyncio.sleep(2)
                await cdp.eval("window.scrollTo({ top: 0, behavior: 'smooth' });")
                await asyncio.sleep(1)

            elif step["action"] == "scroll_bmtc":
                await cdp.eval("window.scrollBy({ top: 160, behavior: 'smooth' });")
                await asyncio.sleep(1)

            elif step["action"] == "scroll_metro":
                await cdp.eval("window.scrollBy({ top: 320, behavior: 'smooth' });")
                await asyncio.sleep(1)

            elif step["action"] == "scroll_cabs":
                await cdp.eval("window.scrollBy({ top: 340, behavior: 'smooth' });")
                await asyncio.sleep(1)

            elif step["action"] == "scroll_garage_eco":
                await cdp.eval("window.scrollBy({ top: 380, behavior: 'smooth' });")
                await asyncio.sleep(1)

            elif step["action"] == "open_bmtc_detail":
                await cdp.eval("""
                    const cards = Array.from(document.querySelectorAll('div, button'));
                    const bmtc = cards.find(el => el.textContent.includes('BMTC Bus') || el.textContent.includes('500C') || el.textContent.includes('500D'));
                    if (bmtc) bmtc.click();
                """)
                await asyncio.sleep(1.5)

            elif step["action"] == "open_ride_mode":
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const ride = btns.find(b => b.textContent.includes('Ride Mode') || b.textContent.includes('Start Navigation'));
                    if (ride) ride.click();
                """)
                await asyncio.sleep(1.5)

            elif step["action"] == "open_glovebox":
                await cdp.eval("""
                    const closeBtns = Array.from(document.querySelectorAll('button'));
                    const close = closeBtns.find(b => b.textContent.includes('✕') || b.getAttribute('aria-label') === 'Close');
                    if (close) close.click();
                    const homeBtns = Array.from(document.querySelectorAll('button'));
                    const home = homeBtns.find(b => b.textContent.includes('Home') || b.textContent.includes('BengaluruGo'));
                    if (home) home.click();
                """)
                await asyncio.sleep(1)
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const glove = btns.find(b => b.textContent.includes('Digital Glovebox') || b.textContent.includes('Glovebox'));
                    if (glove) glove.click();
                """)
                await asyncio.sleep(1.5)

            elif step["action"] == "open_chatbot":
                await cdp.eval("""
                    const btns = Array.from(document.querySelectorAll('button'));
                    const bot = btns.find(b => b.textContent.includes('🤖') || b.getAttribute('title') === 'Chatbot');
                    if (bot) bot.click();
                """)
                await asyncio.sleep(1.5)

            # Capture the live mobile frame
            mobile_pil = await cdp.capture_frame_pil()

            # Compose high-resolution video presentation frame
            frame_img = overlay_mobile_frame_and_caption(
                mobile_pil,
                step["title"],
                step["subtitle"],
                step["tips"],
                step_num,
                total_steps
            )

            # Write frames for the step's duration
            num_frames = int(fps * step["duration_sec"])
            bgr_frame = cv2.cvtColor(frame_img, cv2.COLOR_RGB2BGR)
            for _ in range(num_frames):
                out.write(bgr_frame)

        print("Recording finished! Releasing video writer...")
        out.release()
        print(f"Video saved successfully at: {OUTPUT_VIDEO}")

    finally:
        cdp.close()
        server.shutdown()

if __name__ == "__main__":
    asyncio.run(record_full_walkthrough())
