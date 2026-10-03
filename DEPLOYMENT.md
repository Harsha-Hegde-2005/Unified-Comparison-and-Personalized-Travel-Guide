# Deployment & Environment Configuration Guide

## Architecture Overview

```
                      GitHub
                        |
          +-------------+-------------+
          |                           |
      Production                  Production
     Web Hosting               Backend Hosting
   (e.g., Vercel)          (Render / Railway / Fly.io)
          |                           |
          v                           v
   +--------------+            +--------------------+
   | Web Frontend |            |   Common Backend   |
   | (React/Vite) | ---------- |  (FastAPI/Uvicorn) |
   +--------------+            +--------------------+
                                      ^
                                      |
                               +--------------+
                               |  Mobile App  |
                               |  (Flutter)   |
                               +--------------+
```

---

## 1. Local Development Setup

### Running Backend (FastAPI):
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

### Running Web Frontend (React + Vite):
```bash
cd frontend
npm run dev
```

### Running Mobile App (Flutter):
```bash
cd mobile_app
flutter run
```

---

## 2. Future Production Deployment Steps

### Step 1: Deploy Backend (e.g., Render / Railway)
1. Deploy the `backend/` directory to a persistent Python host (Render, Railway, Fly.io, or AWS App Runner).
2. Set Environment Variables in your backend host dashboard:
   - `GOOGLE_MAPS_API_KEY`: Server-side restricted key.
   - `GEMINI_API_KEY`: Gemini API key.
   - `GROQ_API_KEY`: Groq API key.
   - `DATABASE_URL`: Managed PostgreSQL string (e.g., `postgresql://user:pass@host/db`).
   - `ALLOWED_ORIGINS`: Your production frontend domain (e.g., `https://your-app.vercel.app`).
3. Note your backend URL (e.g., `https://your-common-backend.onrender.com`).

### Step 2: Deploy Web Frontend to Vercel
1. Log into Vercel and import your GitHub repository.
2. Select Root Directory: `frontend`.
3. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-common-backend.onrender.com`
4. Deploy project.

### Step 3: Compile Mobile App (Flutter)
Compile your Flutter app targeting the common production backend URL:
```bash
cd mobile_app
flutter build apk --release --dart-define=API_BASE_URL=https://your-common-backend.onrender.com
```
