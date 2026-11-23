#!/bin/bash
# Cloudflare Deployment Script for AUTONOMOUSFORGE
# Run: chmod +x deploy-cloudflare.sh && ./deploy-cloudflare.sh

set -e

echo "🚀 Deploying AUTONOMOUSFORGE to Cloudflare..."

# Configuration - UPDATE THESE VALUES
ACCOUNT_ID="${CF_ACCOUNT_ID:-your-cloudflare-account-id}"
PROJECT_NAME="autonomousforge"
CUSTOM_DOMAIN="${CUSTOM_DOMAIN:-autonomousforge.yourdomain.com}"
API_DOMAIN="${API_DOMAIN:-api.yourdomain.com}"
D1_DATABASE_ID="${D1_DATABASE_ID:-}"
HYPERDRIVE_ID="${HYPERDRIVE_ID:-}"
KV_NAMESPACE_ID="${KV_NAMESPACE_ID:-}"
R2_BUCKET_NAME="${R2_BUCKET_NAME:-autonomousforge-files}"

# Theme configuration
THEME_MODE="${THEME_MODE:-purple}"
PRIMARY_COLOR="${PRIMARY_COLOR:-#7c3aed}"
ACCENT_COLOR="${ACCENT_COLOR:-#a855f7}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() { echo -e "${GREEN}▶${NC} $1"; }
print_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Check prerequisites
check_prereqs() {
    print_step "Checking prerequisites..."

    if ! command -v wrangler &> /dev/null; then
        print_error "Wrangler not installed. Run: npm install -g wrangler"
        exit 1
    fi

    if ! wrangler whoami &> /dev/null; then
        print_error "Not logged into Cloudflare. Run: wrangler login"
        exit 1
    fi

    print_step "Prerequisites OK"
}

# Update index.html with cloud configuration meta tags
update_index_html() {
    print_step "Updating index.html with cloud configuration..."

    local index_file="apps/web/index.html"

    if [[ ! -f "$index_file" ]]; then
        print_error "index.html not found at $index_file"
        return 1
    fi

    # Update meta tags using sed
    sed -i "s|<meta name=\"af-theme-mode\" content=\"[^\"]*\"|<meta name=\"af-theme-mode\" content=\"$THEME_MODE\"|g" "$index_file"
    sed -i "s|<meta name=\"af-primary-color\" content=\"[^\"]*\"|<meta name=\"af-primary-color\" content=\"$PRIMARY_COLOR\"|g" "$index_file"
    sed -i "s|<meta name=\"af-accent-color\" content=\"[^\"]*\"|<meta name=\"af-accent-color\" content=\"$ACCENT_COLOR\"|g" "$index_file"
    sed -i "s|<meta name=\"af-api-domain\" content=\"[^\"]*\"|<meta name=\"af-api-domain\" content=\"$API_DOMAIN\"|g" "$index_file"
    sed -i "s|<meta name=\"af-api-base\" content=\"[^\"]*\"|<meta name=\"af-api-base\" content=\"https://$API_DOMAIN/api\"|g" "$index_file"
    sed -i "s|<meta name=\"af-ws-base\" content=\"[^\"]*\"|<meta name=\"af-ws-base\" content=\"wss://$API_DOMAIN/ws\"|g" "$index_file"
    sed -i "s|<meta name=\"af-cloudflare-deploy\" content=\"[^\"]*\"|<meta name=\"af-cloudflare-deploy\" content=\"true\"|g" "$index_file"
    sed -i "s|<meta name=\"af-cloudflare-pages\" content=\"[^\"]*\"|<meta name=\"af-cloudflare-pages\" content=\"true\"|g" "$index_file"
    sed -i "s|<meta name=\"af-cloudflare-worker\" content=\"[^\"]*\"|<meta name=\"af-cloudflare-worker\" content=\"false\"|g" "$index_file"

    if [[ -n "$D1_DATABASE_ID" ]]; then
        sed -i "s|<meta name=\"af-d1-database-id\" content=\"[^\"]*\"|<meta name=\"af-d1-database-id\" content=\"$D1_DATABASE_ID\"|g" "$index_file"
    fi

    if [[ -n "$HYPERDRIVE_ID" ]]; then
        sed -i "s|<meta name=\"af-hyperdrive-enabled\" content=\"[^\"]*\"|<meta name=\"af-hyperdrive-enabled\" content=\"true\"|g" "$index_file"
    fi

    if [[ -n "$KV_NAMESPACE_ID" ]]; then
        sed -i "s|<meta name=\"af-kv-enabled\" content=\"[^\"]*\"|<meta name=\"af-kv-enabled\" content=\"true\"|g" "$index_file"
    fi

    sed -i "s|<meta name=\"af-r2-enabled\" content=\"[^\"]*\"|<meta name=\"af-r2-enabled\" content=\"true\"|g" "$index_file"

    print_step "index.html updated with cloud configuration"
}

# Deploy frontend to Cloudflare Pages
deploy_frontend() {
    print_step "Deploying frontend to Cloudflare Pages..."

    cd apps/web

    # Update index.html with cloud configuration
    update_index_html

    # Create _headers for security and caching
    cat > _headers << 'EOF'
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()

/sw.js
  Service-Worker-Allowed: /
  Cache-Control: public, max-age=0, must-revalidate

/assets/*
  Cache-Control: public, max-age=31536000, immutable

/manifest.json
  Cache-Control: public, max-age=86400
EOF

    # Create _redirects for SPA routing
    cat > _redirects << 'EOF'
/api/*  https://api.yourdomain.com/api/:splat  200
/ws*    https://api.yourdomain.com/ws/:splat   200
/*      /index.html   200
EOF

    print_step "Deploying to Pages..."
    wrangler pages deploy . \
        --project-name="$PROJECT_NAME" \
        --branch=main \
        --commit-dirty=true

    cd ../..

    print_step "Frontend deployed!"
    print_warn "Configure custom domain in Cloudflare Dashboard: $CUSTOM_DOMAIN"
}

# Create Worker for API Gateway (if not using Docker)
create_api_worker() {
    print_step "Creating API Gateway Worker..."

    mkdir -p workers/api-gateway

    cat > workers/api-gateway/src/index.ts << 'EOF'
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'

type Bindings = {
  SESSION_KV: KVNamespace
  FILE_STORAGE: R2Bucket
  DB?: D1Database
  HYPERDRIVE?: Hyperdrive
  AI?: Ai
  // Add service bindings here
}

const app = new Hono<{ Bindings: Bindings }>()

app.use('*', logger())
app.use('*', cors({
  origin: ['https://autonomousforge.yourdomain.com', 'http://localhost:3000'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-Master-Key'],
  allowMethods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  credentials: true,
}))

// Cloud configuration endpoint for frontend
app.get('/cloud-config', (c) => {
  return c.json({
    isCloudflare: true,
    isCloudflareWorker: true,
    themeMode: c.env.THEME_MODE || 'purple',
    primaryColor: c.env.PRIMARY_COLOR || '#7c3aed',
    accentColor: c.env.ACCENT_COLOR || '#a855f7',
    databaseType: c.env.DB ? 'd1' : (c.env.HYPERDRIVE ? 'hyperdrive' : 'postgresql'),
    d1DatabaseId: c.env.D1_DATABASE_ID || '',
    apiBaseUrl: `https://${c.env.API_DOMAIN || 'api.yourdomain.com'}/api`,
    wsBaseUrl: `wss://${c.env.API_DOMAIN || 'api.yourdomain.com'}/ws`,
    enableD1: !!c.env.DB,
    enableR2: !!c.env.FILE_STORAGE,
    enableKV: !!c.env.SESSION_KV,
    enableHyperdrive: !!c.env.HYPERDRIVE,
    enableWorkersAI: !!c.env.AI,
  })
})

// Health check
app.get('/health', (c) => c.json({ status: 'healthy', timestamp: new Date().toISOString() }))

// Auth routes - proxy to auth service
app.post('/auth/*', async (c) => {
  // Forward to auth service (via service binding or HTTP)
  return c.json({ message: 'Proxy to auth-service' })
})

// Agent routes
app.get('/agents', async (c) => {
  return c.json({ agents: [] })
})

app.get('/agents/hierarchy', async (c) => {
  return c.json({
    master: { active: 1, total: 1 },
    principals: { active: 8, total: 10 },
    heads: { active: 45, total: 100 },
    team_leaders: { active: 320, total: 1000 },
    workers: { active: 1200, total: 15000 },
  })
})

// Project routes
app.get('/projects', async (c) => c.json({ projects: [] }))
app.post('/projects', async (c) => c.json({ id: crypto.randomUUID() }))

// Master API Key validation middleware
app.use('/master/*', async (c, next) => {
  const masterKey = c.req.header('X-Master-Key')
  if (!masterKey || !masterKey.startsWith('af_master_')) {
    return c.json({ error: 'Invalid master key' }, 401)
  }
  // Validate against KV or database
  await next()
})

// Master endpoints - full system control
app.get('/master/status', async (c) => {
  return c.json({ system: 'operational', agents: 16111 })
})

app.post('/master/command', async (c) => {
  const body = await c.req.json()
  return c.json({ executed: true, command: body })
})

export default app
EOF

    cat > workers/api-gateway/wrangler.toml << EOF
name = "autonomousforge-api"
main = "src/index.ts"
compatibility_date = "2024-11-22"
compatibility_flags = ["nodejs_compat"]

[vars]
ENVIRONMENT = "production"
THEME_MODE = "$THEME_MODE"
PRIMARY_COLOR = "$PRIMARY_COLOR"
ACCENT_COLOR = "$ACCENT_COLOR"
API_DOMAIN = "$API_DOMAIN"
D1_DATABASE_ID = "$D1_DATABASE_ID"

[[kv_namespaces]]
binding = "SESSION_KV"
id = "$KV_NAMESPACE_ID"

[[r2_buckets]]
binding = "FILE_STORAGE"
bucket_name = "$R2_BUCKET_NAME"

# D1 Database (if using Cloudflare D1)
EOF

    if [[ -n "$D1_DATABASE_ID" ]]; then
        cat >> workers/api-gateway/wrangler.toml << EOF
[[d1_databases]]
binding = "DB"
database_name = "autonomousforge"
database_id = "$D1_DATABASE_ID"
EOF
    fi

    if [[ -n "$HYPERDRIVE_ID" ]]; then
        cat >> workers/api-gateway/wrangler.toml << EOF
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "$HYPERDRIVE_ID"
EOF
    fi

    # Workers AI
    cat >> workers/api-gateway/wrangler.toml << EOF
# Workers AI (optional)
# [[ai]]
# binding = "AI"

[build]
command = "npm run build"
EOF

    cat > workers/api-gateway/package.json << 'EOF'
{
  "name": "autonomousforge-api",
  "private": true,
  "scripts": {
    "build": "wrangler deploy",
    "dev": "wrangler dev",
    "test": "vitest"
  },
  "dependencies": {
    "hono": "^4.5.0"
  },
  "devDependencies": {
    "@cloudflare/workers-types": "^4.2024000.0",
    "wrangler": "^3.70.0",
    "vitest": "^2.0.0"
  }
}
EOF

    print_step "API Worker created at workers/api-gateway/"
    print_warn "Run: cd workers/api-gateway && npm install && npm run build"
}

# Setup Cloudflare resources
setup_resources() {
    print_step "Setting up Cloudflare resources..."

    # Create KV namespace for sessions
    print_step "Creating KV namespace for sessions..."
    local kv_output=$(wrangler kv:namespace create "SESSION_KV" --preview false 2>&1)
    echo "$kv_output"
    KV_NAMESPACE_ID=$(echo "$kv_output" | grep -o 'id = "[^"]*"' | cut -d'"' -f2 | head -1)
    if [[ -n "$KV_NAMESPACE_ID" ]]; then
        print_step "KV Namespace ID: $KV_NAMESPACE_ID"
    fi

    # Create R2 bucket for files
    print_step "Creating R2 bucket for file storage..."
    wrangler r2 bucket create "$R2_BUCKET_NAME"
    wrangler r2 bucket create "$R2_BUCKET_NAME-preview"

    # Create D1 database (optional - if not using PostgreSQL)
    if [[ -z "$D1_DATABASE_ID" ]]; then
        print_step "Creating D1 database..."
        local d1_output=$(wrangler d1 create autonomousforge 2>&1)
        echo "$d1_output"
        D1_DATABASE_ID=$(echo "$d1_output" | grep -o 'database_id = "[^"]*"' | cut -d'"' -f2 | head -1)
        if [[ -n "$D1_DATABASE_ID" ]]; then
            print_step "D1 Database ID: $D1_DATABASE_ID"
        fi
    fi

    # Create Hyperdrive (optional - for PostgreSQL connection pooling)
    if [[ -z "$HYPERDRIVE_ID" ]] && [[ -n "$DATABASE_URL" ]]; then
        print_step "Creating Hyperdrive for PostgreSQL connection pooling..."
        local hd_output=$(wrangler hyperdrive create autonomousforge-hyperdrive --connection-string="$DATABASE_URL" 2>&1)
        echo "$hd_output"
        HYPERDRIVE_ID=$(echo "$hd_output" | grep -o 'id = "[^"]*"' | cut -d'"' -f2 | head -1)
        if [[ -n "$HYPERDRIVE_ID" ]]; then
            print_step "Hyperdrive ID: $HYPERDRIVE_ID"
        fi
    fi

    print_step "Resources created! Update configuration with the IDs."
}

# Main
main() {
    echo "=========================================="
    echo "  AUTONOMOUSFORGE Cloudflare Deployment"
    echo "=========================================="
    echo ""
    echo "Configuration:"
    echo "  Account ID: $ACCOUNT_ID"
    echo "  Project: $PROJECT_NAME"
    echo "  Frontend Domain: $CUSTOM_DOMAIN"
    echo "  API Domain: $API_DOMAIN"
    echo "  Theme: $THEME_MODE ($PRIMARY_COLOR / $ACCENT_COLOR)"
    echo "  D1 Database: ${D1_DATABASE_ID:-'will create'}"
    echo "  Hyperdrive: ${HYPERDRIVE_ID:-'will create if DATABASE_URL provided'}"
    echo "  KV Namespace: ${KV_NAMESPACE_ID:-'will create'}"
    echo "  R2 Bucket: $R2_BUCKET_NAME"
    echo ""

    check_prereqs
    setup_resources
    deploy_frontend
    create_api_worker

    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ Deployment preparation complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Generated IDs (save these):"
    echo "  KV_NAMESPACE_ID=$KV_NAMESPACE_ID"
    echo "  D1_DATABASE_ID=$D1_DATABASE_ID"
    echo "  HYPERDRIVE_ID=$HYPERDRIVE_ID"
    echo ""
    echo "Next steps:"
    echo "1. Configure custom domains in Cloudflare Dashboard:"
    echo "   - Frontend: $CUSTOM_DOMAIN → Pages project '$PROJECT_NAME'"
    echo "   - API: $API_DOMAIN → Workers route"
    echo "2. Set environment variables in Cloudflare Dashboard (Pages & Workers):"
    echo "   - JWT_SECRET, NVIDIA_API_KEY, MASTER_API_KEY, etc."
    echo "   - THEME_MODE=$THEME_MODE"
    echo "   - PRIMARY_COLOR=$PRIMARY_COLOR"
    echo "   - ACCENT_COLOR=$ACCENT_COLOR"
    echo "   - API_DOMAIN=$API_DOMAIN"
    echo "   - D1_DATABASE_ID=$D1_DATABASE_ID"
    echo "   - KV_NAMESPACE_ID=$KV_NAMESPACE_ID"
    echo "   - R2_BUCKET_NAME=$R2_BUCKET_NAME"
    echo "3. Deploy API Worker: cd workers/api-gateway && npm install && npm run build"
    echo "4. For backend services: Use Cloudflare Tunnels or keep Docker on VPS"
    echo ""
    echo "Hybrid architecture recommendation:"
    echo "  - Frontend: Cloudflare Pages (static, global CDN)"
    echo "  - API Gateway: Cloudflare Worker (edge routing, auth, cloud-config endpoint)"
    echo "  - Backend Services: Docker on VPS (via Cloudflare Tunnel)"
    echo "  - Database: PostgreSQL on VPS (via Hyperdrive) or Cloudflare D1"
    echo ""
    echo "Auto-rewrite features enabled:"
    echo "  - Database URL auto-rewrites to D1 or Hyperdrive"
    echo "  - Visual theme auto-applies (purple default, cloudflare orange on CF)"
    echo "  - API endpoints auto-detect deployment environment"
    echo "  - Service bindings for KV, R2, D1, Hyperdrive, Workers AI"
}

main "$@"