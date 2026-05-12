# EduPath AI - Career Recommendation System

EduPath AI is a premium, AI-powered career recommendation platform. It leverages an interactive onboarding experience and an adaptive Q&A session driven by the Groq API (Qwen 32B) to rank and recommend the top 10 best-fit careers.

## Features
- **Adaptive AI Assessment**: Interactive questionnaire that evolves based on your profile and previous answers.
- **Premium Design**: Modern, glassmorphic UI with vibrant gradients and micro-animations.
- **Expert Ranking**: Detailed career blueprints with match scores, skill gap analysis, and market insights (salary/growth).
- **Session History**: Revisit and track your past career discovery journeys.
- **Privacy First**: Local SQLite storage and secure JWT-based authentication.

## Tech Stack
- **Backend**: Python + Flask, SQLite, Groq SDK.
- **Frontend**: Vanilla JS, Tailwind CSS, Google Fonts (Outfit).
- **AI**: Qwen 32B via Groq API.

## Setup & Running

1. **Prerequisites**: Python 3.8+ installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API Key**:
   Create a `.env` file from `.env.example` and add your `GROQ_API_KEY`.
4. **Run the App**:
   ```bash
   python app.py
   ```
5. **Access**:
   Open `http://localhost:5000` in your browser.

## Project Structure
- `app.py`: Main backend logic, API routes, and AI orchestration.
- `templates/`: Premium HTML5 templates with glassmorphic styling.
- `static/`: Generated assets and hero illustrations.
- `database.sqlite`: Persistent storage for users, sessions, and results.

---
**Build with passion for career clarity.**
