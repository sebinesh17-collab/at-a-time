# AUTONOMOUSFORGE - Cloudflare Deployment Guide

## Overview

This guide covers deploying AUTONOMOUSFORGE to Cloudflare with automatic database URL rewriting, visual theme adaptation, and hybrid architecture support.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cloudflare Edge                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐    │
│  │  Cloudflare     │    │  Cloudflare Workers             │    │
│  │  Pages          │    │  (API Gateway)                  │    │
│  │  (Frontend)     │◄───┤  - Auth, Routing, Rate Limit    │    │
│  │                 │    │  - Cloud Config Endpoint        │    │
│  │  - Static files │    │  - Service Bindings             │    │
│  │  - SPA routing  │    │  - KV, R2, D1, Hyperdrive       │    │
│  └─────────────────┘    └─────────────────────────────────┘    │
│           │                        │                            │
│           │                        ▼                            │
│           │    ┌─────────────────────────────────┐              │
│           │    │  Cloudflare Resources           │              │
│           │    │  - KV (sessions, cache)         │              │
│           │    │  - R2 (file storage)            │              │
│           │    │  - D1 (SQLite database)         │              │
│           │    │  - Hyperdrive (PG pooling)      │              │
│           │    │  - Workers AI (LLM inference)   │              │
│           │    └─────────────────────────────────┘              │
└───────────│─────────────────────────────────────────────────────┘
            │
            ▼ (Cloudflare Tunnel)
┌─────────────────────────────────────────────────────────────────┐
│                      VPS / Private Network                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Docker Compose Services                                │    │
│  │  - PostgreSQL (primary DB)                              │    │
│  │  - Redis (caching, queues)                              │    │
│  │  - Auth Service                                         │    │
│  │  - Master Orchestrator                                  │    │
│  │  - Agent Registry                                       │    │
│  │  - Task Scheduler                                       │    │
│  │  - Model Gateway (NVIDIA NIM)                          │    │
│  │  - Provider Service                                     │    │
│  │  - File Service                                         │    │
│  │  - Memory Service                                       │    │
│  │  - Knowledge Service                                    │    │
│  │  - Execution Service                                    │    │
│  │  - Build Service                                        │    │
│  │  - Testing Service                                      │    │
│  │  - Monitoring Service                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Prerequisites

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Verify account
wrangler whoami
```

### 2. Set Environment Variables

```bash
export CF_ACCOUNT_ID="your-account-id"
export CUSTOM_DOMAIN="autonomousforge.yourdomain.com"
export API_DOMAIN="api.yourdomain.com"
export DATABASE_URL="postgresql://user:pass@host:5432/db"  # For Hyperdrive
export JWT_SECRET="your-jwt-secret-32-chars-min"
export NVIDIA_API_KEY="your-nvidia-api-key"
export MASTER_API_KEY="af_master_your-master-key"
export ENCRYPTION_KEY="your-32-char-encryption-key"
```

### 3. Deploy

```bash
# Make script executable
chmod +x deploy-cloudflare.sh

# Run deployment
./deploy-cloudflare.sh
```

The script will:
1. Create KV namespace for sessions
2. Create R2 bucket for file storage
3. Create D1 database (optional)
4. Create Hyperdrive for PostgreSQL pooling (optional)
5. Update `index.html` with cloud configuration meta tags
6. Deploy frontend to Cloudflare Pages
7. Create API Gateway Worker with bindings

### 4. Configure Custom Domains

In Cloudflare Dashboard:
- **Pages Project**: Add custom domain `autonomousforge.yourdomain.com`
- **Workers**: Add route `api.yourdomain.com/*` → Worker

### 5. Set Environment Variables in Dashboard

**Pages Project Settings → Environment Variables:**
```
THEME_MODE=purple
PRIMARY_COLOR=#7c3aed
ACCENT_COLOR=#a855f7
API_DOMAIN=api.yourdomain.com
```

**Worker Settings → Environment Variables:**
```
JWT_SECRET=your-jwt-secret
NVIDIA_API_KEY=your-nvidia-key
MASTER_API_KEY=af_master_your-key
ENCRYPTION_KEY=your-32-char-key
THEME_MODE=purple
PRIMARY_COLOR=#7c3aed
ACCENT_COLOR=#a855f7
API_DOMAIN=api.yourdomain.com
D1_DATABASE_ID=your-d1-id
KV_NAMESPACE_ID=your-kv-id
R2_BUCKET_NAME=autonomousforge-files
```

### 6. Deploy Backend Services (VPS)

```bash
# On your VPS
git clone <repo>
cd autonomousforge

# Update .env with production values
cp .env.example .env
# Edit .env with your values

# Start services
docker-compose up -d

# Verify
docker-compose ps
```

### 7. Create Cloudflare Tunnel

```bash
# Install cloudflared
# On VPS
cloudflared tunnel login
cloudflared tunnel create autonomousforge
cloudflared tunnel route dns autonomousforge api.yourdomain.com

# Configure config.yml
cat > ~/.cloudflared/config.yml << EOF
tunnel: autonomousforge
credentials-file: /home/user/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run autonomousforge
```

## Auto-Configuration Features

### Database URL Rewriting

The system automatically detects the deployment environment and rewrites database connections:

| Environment | Database | Connection |
|-------------|----------|------------|
| Local       | PostgreSQL | `postgresql://...` |
| Cloudflare + D1 | D1 (SQLite) | `d1://database-id` |
| Cloudflare + Hyperdrive | PostgreSQL (pooled) | Hyperdrive connection string |
| Cloudflare + Tunnel | PostgreSQL | `postgresql://...` (via tunnel) |

### Visual Theme Adaptation

| Environment | Theme | Primary Color |
|-------------|-------|---------------|
| Local       | Purple (default) | `#7c3aed` |
| Cloudflare  | Cloudflare Orange | `#f38020` |
| Custom      | Via `THEME_MODE` env var | Configurable |

### API Endpoint Auto-Detection

Frontend automatically detects deployment and configures:
- **Local**: `/api`, `/ws`
- **Cloudflare Pages**: `https://api.yourdomain.com/api`, `wss://api.yourdomain.com/ws`

### Service Binding Auto-Configuration

In Cloudflare Workers, services communicate via:
- **Service bindings** (preferred): Zero-latency, no network overhead
- **HTTP fallback**: For external services or VPS via tunnel

## Configuration Files

### `wrangler.toml` (Root)

Main configuration for Pages and Workers:
```toml
name = "autonomousforge"
compatibility_date = "2024-11-22"
compatibility_flags = ["nodejs_compat"]

[vars]
THEME_MODE = "purple"
PRIMARY_COLOR = "#7c3aed"
ACCENT_COLOR = "#a855f7"
API_DOMAIN = "api.yourdomain.com"
D1_DATABASE_ID = ""

[[kv_namespaces]]
binding = "SESSION_KV"
id = "your-kv-id"

[[r2_buckets]]
binding = "FILE_STORAGE"
bucket_name = "autonomousforge-files"

# Optional D1
# [[d1_databases]]
# binding = "DB"
# database_id = "your-d1-id"

# Optional Hyperdrive
# [[hyperdrive]]
# binding = "HYPERDRIVE"
# id = "your-hyperdrive-id"
```

### `deploy-cloudflare.sh`

Automated deployment script that:
- Creates all Cloudflare resources
- Updates `index.html` with meta tags
- Deploys frontend to Pages
- Creates Worker with bindings

### `packages/shared-types/cloudflare_config.py`

Python backend auto-configuration:
- Detects Cloudflare environment
- Rewrites database URLs
- Configures service URLs
- Provides visual theme config

### `apps/web/js/cloud-config.js`

Frontend auto-configuration:
- Detects deployment via hostname
- Reads meta tags from `index.html`
- Applies visual theme via CSS variables
- Configures API/WebSocket endpoints

## Service-Specific Cloudflare Configuration

### Auth Service
- Uses KV for session storage (instead of Redis)
- Master API key validation
- JWT token management

### API Gateway
- Cloudflare Worker at edge
- Rate limiting via KV
- Service bindings to backend
- Cloud config endpoint: `/cloud-config`

### Master Orchestrator
- Coordinates 16,111 agent hierarchy
- Task decomposition (7 levels)
- Service bindings for agent communication

### Model Gateway
- NVIDIA NIM integration
- Workers AI fallback (optional)
- Request/response caching via KV

### File Service
- R2 for object storage
- Signed URLs for uploads
- CDN caching

### Memory/Knowledge Services
- D1 for structured data
- Vector embeddings in D1
- R2 for document storage

## Environment Variables Reference

### Required for All Deployments
| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | JWT signing secret (32+ chars) | `super-secret-key-32-chars-min` |
| `NVIDIA_API_KEY` | NVIDIA NIM API key | `nvapi-xxx` |
| `MASTER_API_KEY` | Master API key (af_master_*) | `af_master_xxx` |
| `ENCRYPTION_KEY` | Encryption key (32 chars) | `32-char-encryption-key-here` |

### Cloudflare-Specific
| Variable | Description | Example |
|----------|-------------|---------|
| `CF_ACCOUNT_ID` | Cloudflare account ID | `abc123` |
| `D1_DATABASE_ID` | D1 database ID | `uuid` |
| `KV_NAMESPACE_ID` | KV namespace ID | `uuid` |
| `R2_BUCKET_NAME` | R2 bucket name | `autonomousforge-files` |
| `HYPERDRIVE_ID` | Hyperdrive ID | `uuid` |
| `API_DOMAIN` | API custom domain | `api.yourdomain.com` |
| `THEME_MODE` | Visual theme | `purple`, `cloudflare`, `dark`, `light` |
| `PRIMARY_COLOR` | Primary color hex | `#7c3aed` |
| `ACCENT_COLOR` | Accent color hex | `#a855f7` |

### Database (VPS/PostgreSQL)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |

## Troubleshooting

### Frontend Not Loading
1. Check Pages deployment status
2. Verify custom domain DNS
3. Check `_redirects` file exists
4. Verify `index.html` meta tags

### API Errors
1. Check Worker logs: `wrangler tail`
2. Verify service bindings
3. Check tunnel connection
4. Verify environment variables

### Database Connection Issues
1. **D1**: Verify `D1_DATABASE_ID` and bindings
2. **Hyperdrive**: Verify connection string
3. **PostgreSQL**: Verify tunnel and credentials

### Theme Not Applying
1. Check `index.html` meta tags
2. Verify `cloud-config.js` loads first
3. Check browser console for errors
4. Verify CSS custom properties

## Monitoring & Debugging

### Worker Logs
```bash
# Real-time logs
wrangler tail autonomousforge-api

# Filter by level
wrangler tail autonomousforge-api --format json | jq 'select(.level=="error")'
```

### Pages Analytics
- Cloudflare Dashboard → Pages → Analytics
- Web Vitals, bandwidth, requests

### Database Monitoring
- D1: Dashboard → D1 → Query analytics
- Hyperdrive: Dashboard → Hyperdrive → Metrics
- PostgreSQL: Use pg_stat_statements

## Cost Optimization

### Free Tier Limits
| Resource | Free Tier |
|----------|-----------|
| Workers | 100k requests/day |
| Pages | 500 builds/month, unlimited requests |
| KV | 1GB storage, 100k reads/day |
| R2 | 10GB storage, 1M operations/month |
| D1 | 5GB storage, 5M rows read/day |
| Hyperdrive | 100GB data transfer/month |

### Optimization Tips
1. Enable caching in `_headers`
2. Use KV for session/rate limiting
3. Batch D1 queries
4. Use Hyperdrive for connection pooling
5. Compress responses (gzip/brotli)

## Security Checklist

- [ ] Strong `JWT_SECRET` (32+ random chars)
- [ ] Strong `MASTER_API_KEY` (af_master_* format)
- [ ] Strong `ENCRYPTION_KEY` (32 chars)
- [ ] Custom domains with HTTPS
- [ ] CORS configured for your domains only
- [ ] Rate limiting enabled
- [ ] Security headers in `_headers`
- [ ] Environment variables in Dashboard (not code)
- [ ] Regular rotation of API keys
- [ ] WAF rules for API protection

## Rollback Procedure

```bash
# Rollback Pages deployment
wrangler pages deployment list --project-name=autonomousforge
wrangler pages deployment rollback --project-name=autonomousforge <deployment-id>

# Rollback Worker
wrangler deployments list autonomousforge-api
wrangler rollback autonomousforge-api <deployment-id>
```

## Support

- Check logs first: `wrangler tail`
- Review this guide for configuration
- Check Cloudflare status page
- GitHub Issues for bugs