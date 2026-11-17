# AnnaSetu — System Architecture (ARCHITECTURE.md)

AnnaSetu connects surplus food donors with verified NGOs and volunteer runners across India with an audit-logged cryptographic chain of custody.

---

## 1. System Context Diagram

```mermaid
flowchart TD
    Donor["Food Donor (Caterer/Restaurant)"] -->|1. Posts Surplus Food| WebApp["AnnaSetu Web (Django / Daphne)"]
    WebApp -->|2. Smart Match Score| MatchingEngine["Matching Service (Haversine)"]
    MatchingEngine -->|3. Proximity Alert| NGO["Verified NGO / Kitchen"]
    NGO -->|4. Claims Food| WebApp
    WebApp -->|5. Creates Task & Alerts| Volunteer["Volunteer Runner"]
    Volunteer -->|6. Scans Pickup QR + Checklist| Donor
    Volunteer -->|7. Delivers Food & Scans Delivery QR| NGO
    WebApp -->|8. Issues CSR Certificate| CertificateEngine["ReportLab PDF Engine"]
    CertificateEngine --> Donor
```

---

## 2. Real-Time & Event Architecture

```mermaid
sequenceDiagram
    autonumber
    actor Donor
    actor Volunteer
    actor NGO
    participant Server as AnnaSetu Server
    participant Redis as Redis / Channels
    participant DB as Database (SQLite/Postgres)

    Donor->>Server: Post food listing
    Server->>DB: Save Donation (status=POSTED)
    Server->>Redis: Broadcast new donation to channel 'donation_feed'
    Server->>NGO: Push WebSocket alert (Smart Match score)

    NGO->>Server: Claim donation (atomic select_for_update)
    Server->>DB: Save Claim (ACCEPTED) & create DeliveryTask
    Server->>Volunteer: Alert nearby volunteers

    Volunteer->>Server: Accept DeliveryTask
    Server->>DB: Set DeliveryTask (status=ASSIGNED)

    Volunteer->>Server: Submit 4-point safety checklist
    Volunteer->>Server: Scan Pickup QR token
    Server->>DB: Verify signature & record StatusEvent (PICKED_UP)

    NGO->>Server: Scan Delivery QR token
    Server->>DB: Verify signature & record StatusEvent (DELIVERED)
    Server->>Volunteer: Award gamification points & badges
    Server->>Donor: Generate verifiable CSR Certificate
```

---

## 3. Technology Stack Breakdown

| Layer | Technologies |
|---|---|
| **Web Server / ASGI** | Django 5.x, Daphne, Gunicorn, WhiteNoise |
| **Real-time WebSockets** | Django Channels, `channels-redis` (with InMemory dev fallback) |
| **API & Documentation** | Django REST Framework, SimpleJWT, `drf-spectacular` (OpenAPI 3 / Swagger) |
| **Database** | SQLite (Dev) / PostgreSQL (Prod via `dj-database-url`) |
| **Geo Engine** | Pure-Python Haversine with DB Bounding Box Indexing |
| **Async Jobs** | Celery + Celery Beat + Redis |
| **Frontend** | Tailwind CSS, Alpine.js, HTMX, Leaflet.js (OpenStreetMap), Chart.js, Lucide Icons |
| **Document Generation** | ReportLab (CSR PDF certificates), QRCode (PIL) |
