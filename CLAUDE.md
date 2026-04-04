# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Stolari** is a Django 4.2 web application for managing furniture/woodworking offers with a sophisticated dimension calculation engine. Users create offers containing furniture elements, configure coefficient multipliers, and the system automatically calculates final dimensions using formula-based rules.

## Commands

### Development Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Docker
```bash
docker-compose up --build
# App: http://localhost:5005, Nginx: http://localhost:5085
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

### Tests
```bash
python manage.py test
python manage.py test apps.offers
```

### Static Files
```bash
python manage.py collectstatic --no-input
```

### Frontend Assets (Gulp/Vite)
```bash
npm install
# See gulpfile.js and vite.config.mjs for build tasks
```

## Architecture

### App Structure
- **`core/`** — Django settings, root URLs, WSGI/ASGI
- **`home/`** — Dashboard views and general pages
- **`apps/offers/`** — Core business logic: offers, elements, coefficients, dimension calculations
- **`apps/users/`** — Extended user profiles with coefficient preferences
- **`apps/api/`** — DRF REST API with OpenAPI/Swagger via drf-spectacular
- **`apps/tasks/`** — Celery async tasks (Redis broker, optional)
- **`apps/tables/`**, **`apps/charts/`**, **`apps/common/`**, **`apps/file_manager/`** — Supporting features

### Core Data Model (Offers App)

```
Offer (created_by User)
 ├─ Element (1-N): user-input Dx, Dy, Dz dimensions + element_type + sub_type
 ├─ OfferCoefficientSelection (1-N): selected Coefficient per CoefficientGroup
 └─ CalculatedElementSubTypeElement (1-N): calculated Dx, Dy results

CoefficientGroup → Coefficient (is_default flag)
UserCoefficientPreference → per-user default coefficients per group
ElementSubType → ElementSubTypeElements (formula templates with formula_code)
```

### Calculation Engine (`apps/offers/calculations.py` — 720 lines)

The most complex part of the codebase. `DimensionCalculator` computes final Dx/Dy for each `ElementSubTypeElements` record using:
1. User-input Element dimensions (Dx, Dy, Dz)
2. Selected offer coefficients from `OfferCoefficientSelection`
3. Per-element formula code from `ElementSubTypeElements.formula_code`

Recalculation is triggered via Django signals when coefficients or element dimensions change, and manually via AJAX at `/offers/ajax/recalculate-dimensions/<id>/`.

See `apps/offers/CALCULATIONS_README.md` for formula documentation and `apps/offers/TESTING_CALCULATIONS.md` for testing guidance.

### Element Types
- `donji_elementi` (lower elements), `gornji_elementi` (upper elements), `visoki_elementi` (tall elements), `ladice` (drawers)
- **Ladice** have special handling: extra fields schema on `ElementSubType.extra_fields_schema` (JSON) and explicit fields `dubina_ladice`, `visina_fronte_1–4` on `Element`

### Authentication
- django-allauth with email-based login + optional OAuth (Google, GitHub)
- `UserCoefficientPreference` stores per-user default coefficients; new offers auto-populate from these

### Tech Stack
- **Backend:** Django 4.2.9, Django REST Framework, drf-spectacular
- **Frontend:** Soft UI Dashboard PRO (Bootstrap 5), Quill rich text editor
- **Async:** Celery + Redis (commented out in docker-compose by default)
- **Database:** SQLite (dev), PostgreSQL (prod via env vars)
- **Deployment:** Docker + Gunicorn + Nginx, or Render (render.yaml)

## Environment Variables

The `.env` file at project root is required. Key variables:
```
DEBUG=True
SECRET_KEY=<key>
# Production additionally needs: DB_*, EMAIL_HOST/PASS, GOOGLE_*/GITHUB_* OAuth credentials
```

## Key Files

- [apps/offers/calculations.py](apps/offers/calculations.py) — Dimension calculation engine
- [apps/offers/CALCULATIONS_README.md](apps/offers/CALCULATIONS_README.md) — Formula system documentation
- [apps/offers/models.py](apps/offers/models.py) — All offer-related models
- [apps/offers/views.py](apps/offers/views.py) — Offer CRUD and AJAX endpoints
- [core/settings.py](core/settings.py) — Django configuration
- [scripts/](scripts/) — Utility scripts for populating element configurations
