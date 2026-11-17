# AnnaSetu — Architectural & Design Decisions (DECISIONS.md)

This log documents key decisions made during the autonomous build of the **AnnaSetu** platform.

---

### 1. Settings Architecture
- **Decision:** Split Django settings into `base.py`, `dev.py`, and `prod.py` via `python-decouple` and `dj-database-url`.
- **Rationale:** Ensures clean environment parity, allows developer zero-config startup with SQLite and In-Memory channels, while providing zero-downtime production configurations with PostgreSQL, Redis, and Daphne.

### 2. Geo-Distance Calculation without PostGIS Dependency
- **Decision:** Implemented pure-Python **Haversine** distance calculation and bounding-box pre-filtering in `matching/geo.py`.
- **Rationale:** Avoids forcing developers to install native C-libraries (`GDAL`, `GEOS`, `PROJ`, PostGIS extension) during local development or simple Docker containers, while maintaining query efficiency through database bounding-box indexes on `(latitude, longitude)`.

### 3. Concurrency & Claim Race Prevention
- **Decision:** Used database-level `select_for_update()` inside `transaction.atomic()` alongside a `UniqueConstraint` on `Claim` with `condition=Q(status='accepted')`.
- **Rationale:** Strictly guarantees that two NGOs claiming the exact same surplus batch simultaneously will never result in a double-claim. The second transaction either blocks or raises a clear `ValueError`.

### 4. Cryptographic QR Chain-of-Custody
- **Decision:** Used `django.core.signing` with timestamped token dictionaries and configurable TTL (`QR_TOKEN_MAX_AGE`).
- **Rationale:** No sensitive tokens are stored in plain text. Tokens are tamper-proof and verifiable offline or in browser without third-party proprietary dependencies. The mobile UI incorporates `html5-qrcode` camera scanning with a manual alphanumeric fallback.

### 5. Smart Matching Engine Scoring Model
- **Decision:** Modular multi-factor scoring in `matching/services.py`:
  - 30% Distance (square-root exponential decay)
  - 20% Daily kitchen capacity remaining
  - 20% Historical user reliability score (1-5★)
  - 15% Dietary compatibility (veg-only vs non-veg)
  - 10% Claim acceptance response rate
  - 5% Urgency bonus (< 2 hours remaining)
- **Rationale:** Transparent and explainable ("Why this NGO?") breakdown visible to platform moderators and donors.

### 6. Design System & Frontend Stack
- **Decision:** Warm Indian civic tech theme:
  - Deep leaf green (`#14532D` to `#16A34A`), saffron/turmeric accent (`#F59E0B`), warm stone background (`#FAF8F3`), and night surface (`#0B1410`).
  - Google Fonts pairing: **Fraunces** for headings, **Plus Jakarta Sans** for UI, and **Noto Sans Devanagari** for Hindi.
  - HTMX for seamless partial page swaps (e.g. food feed filtering without page reload).
  - Alpine.js for lightweight UI state (modals, tabs, theme toggling).
  - Leaflet.js with OpenStreetMap tiles (no paid Google Maps API keys).

### 7. CSR Impact & Environmental Standards
- **Decision:** Defined explicit standard constants:
  - `0.40 kg` food per serving.
  - `2.50 kg CO₂e` avoided per kg of food diverted from landfills.
- **Rationale:** Transparently cited across the UI and rendered in PDF certificates via ReportLab for corporate sustainability and CSR compliance.
