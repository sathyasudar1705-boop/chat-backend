# OmniBot - Multi-Provider Secure AI Chatbot Platform

OmniBot is a complete, production-ready, full-stack AI chatbot platform built using React, FastAPI, and PostgreSQL. It features strict user-based data isolation, image generation capabilities, usage auditing, and a multi-provider fallback router.

---

## Key Features

1.  **Strict Data Isolation**: Every SQL query filters records by the authenticated user's ID extracted from a signed JWT token. Request bodies containing user IDs are discarded to prevent ID-spoofing attacks.
2.  **Multi-Provider AI Router**: Automatically queries Gemini, Groq, OpenRouter, Cerebras, and Mistral in sequence. Fails over seamlessly on 429 rate limits, timeouts, or 5xx server errors, but fails immediately on auth errors or safety blocks.
3.  **Image Studio**: Keyless image generation using Pollinations AI, downloading and serving images locally to ensure high availability and prevent external hotlink expiration.
4.  **Usage Analytics**: Custom visualizations built with Recharts detailing query frequencies, successful/failed attempts, average latencies, and fallback counts.
5.  **Data Deletion Sandbox**: Allows users to purge their own chat history or image vaults. Physical files and database rows are cleaned strictly for the active user context.

---

## Directory Structure

```text
├── backend/
│   ├── static/images/      # Downloaded image files
│   ├── auth.py             # Password hashing & JWT dependency
│   ├── database.py         # SQLAlchemy engine & session generators
│   ├── main.py             # FastAPI routes (Auth, Chat, Images, etc.)
│   ├── models.py           # Database models
│   ├── router_ai.py        # ask_ai router and provider clients
│   └── schemas.py          # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── components/     # ProtectedRoute, Navbar
│   │   ├── pages/          # LandingPage, Login, Register, Chatbot, etc.
│   │   ├── App.jsx         # App router and theme manager
│   │   ├── index.css       # Tailwind directives & global animations
│   │   └── main.jsx        # Client entry point
│   ├── vite.config.js      # Proxies mapping /api to local port 8000
│   └── tailwind.config.js  # Dark mode theme specifications
├── .env                    # Secret API keys & Database URL (Backend only)
├── .env.example            # Environment configurations template
├── requirements.txt        # Backend python packages
└── package.json            # Node workspace scripts
```

---

## Installation & Setup

### Prerequisites

*   Python 3.9+
*   Node.js 16+
*   PostgreSQL Database URL (or use the configured Neon DB URL)

### 1. Configuration (.env)

A `.env` file containing correct API keys is already created in the project root. If you need to update keys, edit the values inside `.env`:

```env
DATABASE_URL=postgresql://neondb_owner:npg_oFTP62EDtbOJ@ep-curly-dust-at2yvj6c.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
JWT_SECRET_KEY=your-custom-secret-key-here
GEMINI_API_KEY=your-gemini-key-here
GROQ_API_KEY=your-groq-key-here
OPENROUTER_API_KEY=your-openrouter-key-here
CEREBRAS_API_KEY=your-cerebras-key-here
MISTRAL_API_KEY=your-mistral-key-here
```

### 2. Run Backend Server

From the project root directory, install the Python requirements and boot the development server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend API documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Run Frontend Server

From the project root directory, install npm packages and boot Vite:

```bash
# Install packages
npm run install:frontend

# Run dev server
npm run dev:frontend
```

Open `http://localhost:5173` in your browser. The frontend will proxy all API requests to the running backend.

---

## Security Verification

Before pushing to production, verify:
*   [x] Database queries filter strictly by `current_user.id`.
*   [x] JWT parsing extracts claims securely on the backend; the frontend does not send `user_id` inside request payloads.
*   [x] API keys are stored only in the backend `.env` file and never bundled or exposed in frontend JS assets.
