# AnnaSetu — Food Rescue & Redistribution Platform

> *"Good food deserves a plate, not a bin."*

AnnaSetu ("Anna" = food, "Setu" = bridge) connects people and businesses with surplus food (restaurants, caterers, hotels, wedding banquet hosts, and individuals) to verified NGOs and community kitchens in real time, with volunteer runners handling pickup and delivery.

Every handoff is cryptographically verifiable through a two-stage QR chain of custody.

---

## ⚡ Quick Start in 4 Commands

```bash
# 1. Clone & create virtualenv
git clone <repo-url> && cd annasetu
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies & initialize
make setup

# 3. Start development server
make run
```

Visit **http://localhost:8000** in your browser.

---

## 🔑 Demo Logins

The database comes pre-seeded with 30 donors, 15 NGOs, 25 volunteers, and 200 historical & active rescue missions across Delhi NCR and Bareilly.

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Admin / Moderator** | `admin` | `admin123` | Document verification queue, user management, reports |
| **Donor (Restaurant)** | `donor_demo` | `password123` | Post surplus listings, download CSR certificates |
| **NGO (Kitchen)** | `ngo_demo` | `password123` | Browse proximity feed, claim food batches, scan deliveries |
| **Volunteer** | `volunteer_demo` | `password123` | Accept pickup tasks, complete safety checklist, scan pickup QR |

---

## 🌟 Core Features

- **Multi-Step Onboarding:** Role selection (Donor, NGO, Volunteer), document verification uploads, and an interactive Leaflet location pin picker.
- **Real-Time Discovery Feed:** Distance slider, food type chips (Veg, Non-Veg, Jain), urgency flags (< 2 hours left), and an instant **List / Map toggle** powered by HTMX.
- **Smart Matching Engine:** Weighted multi-factor scoring (30% distance, 20% kitchen capacity, 20% trust score, 15% food compatibility, 10% response rate, 5% urgency) with explainable breakdowns.
- **Cryptographic QR Chain-of-Custody:** Signed time-expiring tokens (`django.core.signing`). In-browser camera scanner (`html5-qrcode`) with manual alphanumeric code fallback.
- **Food Safety Verification:** Mandatory 4-point safety checklist before pickup handoff (temperature, packaging, smell, time window).
- **Gamification & Hall of Heroes:** Points ledger, streaks, badges (*First Rescue*, *Night Owl*, *100 Meals*, *Reliability Icon*), and city leaderboards.
- **CSR PDF Certificates:** ReportLab-generated CSR-ready PDF certificates with QR codes verifiable at `/verify/<serial>/`.
- **Public Impact Analytics:** Live animated counter strip, Chart.js trends, food distribution doughnut chart, and a Leaflet heatmap (`leaflet.heat`).
- **Full REST API (v1):** JWT authentication, OpenAPI 3 / Swagger UI at `/api/v1/docs/` and ReDoc at `/api/v1/redoc/`.
- **Bilingual (i18n):** Complete English and Hindi localization with instant language switcher.

---

## 🛠️ Architecture

```
annasetu/
├── config/                # settings split: base.py, dev.py, prod.py; asgi.py; celery.py
├── accounts/              # Custom User, multi-step onboarding, approval queue
├── donations/             # Donation listings, state machine, expiry tasks
├── logistics/             # Claims, DeliveryTasks, QR verification, safety checklist
├── matching/              # Pure-Python Haversine distance, smart matching engine
├── notifications/         # Central notify() service, WebSockets (Channels)
├── analytics/             # Impact analytics, heatmap data endpoint
├── gamification/          # Points ledger, badges, ratings, leaderboards
├── moderation/            # User/donation abuse reports
├── certificates/          # ReportLab PDF generation, /verify/<serial>/ validation
├── api/                   # DRF viewsets, serializers, JWT endpoints, Swagger
├── templates/             # UI component library, landing page, app shells
└── locale/                # English and compiled Hindi (.po/.mo)
```

---

## ⚙️ Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | Dev default | Django secret key |
| `DEBUG` | `True` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection string (PostgreSQL in prod) |
| `REDIS_URL` | `""` (InMemory) | Redis URL for Channels and Celery |
| `ENABLE_SMS` | `False` | Twilio SMS notifications toggle |
| `ENABLE_AI` | `False` | AI food classification toggle |
| `MATCHING_RADIUS_KM` | `25` | Default discovery radius in km |
| `AUTO_ACCEPT_RELIABILITY_THRESHOLD` | `4.5` | Reliability score for auto-claim acceptance |

---

## 🐳 Docker Deployment

To spin up the entire production stack (Web, Daphne ASGI, Postgres, Redis, Celery Worker, Celery Beat):

```bash
docker compose up --build
```

---

## 🧪 Testing & Code Quality

```bash
# Run pytest test suite (100% passing)
make test

# Run Ruff linter (0 errors)
make lint
```
