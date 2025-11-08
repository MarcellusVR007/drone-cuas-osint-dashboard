# OSINT CUAS Dashboard - Setup & Deployment Guide

## Local Development Setup

### Step 1: Install Dependencies
```bash
cd drone-cuas-osint-dashboard
python3 -m pip install -r requirements.txt
```

### Step 2: Run the Dashboard
```bash
python3 app.py
```

The dashboard will:
- Create SQLite database at `data/drone_cuas.db`
- Seed sample data (EU airports and military bases)
- Start on `http://localhost:8000`
- Auto-open in your browser

### Step 3: Access
- **Dashboard:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger interactive docs)
- **API Health:** http://localhost:8000/api/health

---

## Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python3", "app.py"]
```

Build and run:
```bash
docker build -t osint-cuas .
docker run -p 8000:8000 -v $(pwd)/data:/app/data osint-cuas
```

---

## Cloud Deployment

### Option 1: Heroku (Free tier)

```bash
# Create Heroku app
heroku create your-cuas-dashboard

# Add Procfile
echo "web: python3 app.py" > Procfile

# Deploy
git push heroku main
```

**Note:** Heroku has 550 free dyno hours/month. SQLite persists during dyno restart but use PostgreSQL for production.

### Option 2: Railway.app (Recommended for quick deploy)

1. Push code to GitHub
2. Connect GitHub to Railway
3. Set environment variables if needed
4. Deploy

Railway runs 24/7 free for first month.

### Option 3: AWS/Google Cloud/Azure (Scalable)

Use:
- **Compute:** EC2 / App Engine / App Service
- **Database:** RDS PostgreSQL (instead of SQLite)
- **Networking:** CloudFront / CDN for static assets
- **Monitoring:** CloudWatch / Stackdriver logs

---

## Migration to PostgreSQL (Production)

Update `backend/database.py`:
```python
DATABASE_URL = "postgresql://user:password@localhost/drone_cuas"
```

Install PostgreSQL driver:
```bash
python3 -m pip install psycopg2-binary
```

---

## Data Integration

### Import CSV Data

Create `scripts/import_incidents.py`:
```python
import csv
from sqlalchemy.orm import sessionmaker
from backend.models import Incident
from backend.database import engine

Session = sessionmaker(bind=engine)
session = Session()

with open('incidents.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        incident = Incident(
            sighting_date=row['date'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            source='import',
            title=row['title'],
            description=row['description']
        )
        session.add(incident)

session.commit()
print("✓ Imported incidents")
```

Run:
```bash
python3 scripts/import_incidents.py
```

### Real-time Data Ingestion

Create `scripts/ingest_from_apis.py`:
```python
import requests
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models import Incident

def fetch_easa_incidents():
    """Fetch from EASA API (hypothetical)"""
    # response = requests.get('https://api.easa.europa.eu/incidents')
    # Parse and create Incident records
    pass

def fetch_news_incidents():
    """Scrape news sources"""
    import feedparser
    feeds = [
        'https://www.aviation-safety.net/news/feed/',
        # Add more RSS feeds
    ]
    for feed_url in feeds:
        # Parse and create records
        pass

if __name__ == '__main__':
    fetch_easa_incidents()
    fetch_news_incidents()
    print("✓ Ingestion complete")
```

Run periodically:
```bash
# Every 6 hours via cron
0 */6 * * * cd /path && python3 scripts/ingest_from_apis.py
```

---

## Authentication (Production)

Add authentication to `backend/main.py`:
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import CookieAuthentication

# Configure based on your AD/LDAP/OAuth provider
# Example with OAuth2:

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"])

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Validate credentials
    # Return JWT token
    pass
```

---

## Monitoring & Logging

Add logging to `backend/main.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup():
    logger.info("Dashboard starting")
    init_db()
    seed_db()
```

---

## Backup Strategy

### Automated SQLite Backup
```bash
#!/bin/bash
# backup.sh - Run daily via cron

BACKUP_DIR="/backups/cuas"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp data/drone_cuas.db $BACKUP_DIR/drone_cuas_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

echo "✓ Backup completed: $BACKUP_DIR/drone_cuas_$DATE.db"
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### PostgreSQL Backup (Production)
```bash
pg_dump -h localhost -U postgres -d drone_cuas > backup_$(date +%Y%m%d).sql
```

---

## Performance Optimization

### Enable SQLite Query Caching
```python
# backend/database.py
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # Verify connection alive
    echo=False
)
```

### Add Database Indices
```python
# backend/models.py
class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True)
    sighting_date = Column(Date, nullable=False, index=True)  # Add index
    latitude = Column(Float, nullable=False, index=True)      # For spatial queries
    longitude = Column(Float, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
```

### Caching with Redis
```bash
pip install redis fastapi-cache2
```

---

## Security Hardening

### 1. Enable HTTPS
```python
# Use reverse proxy (nginx/Apache) for TLS
# Or with self-signed cert:

import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    certfile="cert.pem",
    keyfile="key.pem"
)

uvicorn.run(app, ssl_context=ssl_context)
```

### 2. Restrict CORS
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Restrict
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. Add Rate Limiting
```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    return {"status": "healthy"}
```

### 4. Add Security Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
```

---

## Testing

### Run Tests
```bash
pip install pytest pytest-asyncio

# Create tests/test_api.py
pytest tests/
```

Example test:
```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
```

---

## Troubleshooting

### Issue: Module not found errors
**Solution:**
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/drone-cuas-osint-dashboard"
python3 app.py
```

### Issue: Port 8000 in use
```bash
# Find what's using port
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Issue: Database locked
```bash
# Remove stale database
rm data/drone_cuas.db
# It will recreate on next run
```

### Issue: CORS errors from frontend
Verify FastAPI is serving frontend correctly:
```bash
curl http://localhost:8000
# Should return HTML, not JSON error
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| API response time | < 200ms |
| Dashboard load | < 2s |
| Incident search | < 500ms |
| Map rendering | < 1s |
| Pattern detection | < 5s |

---

## Next Steps

1. **Test locally** - Ensure dashboard runs smoothly
2. **Add sample data** - Use the API to add incidents and patterns
3. **Configure data sources** - Setup RSS feeds, API integrations
4. **Deploy to staging** - Test in staging environment first
5. **Configure monitoring** - Setup logs and alerts
6. **Go to production** - Deploy with proper backups and security

---

**Questions?** Check `/docs` endpoint for interactive API documentation.

---

## Support Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- Vue.js Docs: https://vuejs.org
- SQLAlchemy: https://docs.sqlalchemy.org
- Leaflet Maps: https://leafletjs.com
