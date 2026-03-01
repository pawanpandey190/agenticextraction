#!/bin/bash
# =============================================================================
# renew-certs.sh - Renews Let's Encrypt certificate and restarts Nginx
# Add to crontab: 0 3 * * * /path/to/scripts/renew-certs.sh
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
YOUR_DOMAIN=$(openssl x509 -noout -subject -in "$SCRIPT_DIR/nginx/ssl/nginx.crt" | sed 's/.*CN = //')

echo "[$(date)] Renewing certificate for $YOUR_DOMAIN..."

# Stop Nginx, renew, copy, restart
docker compose -f "$SCRIPT_DIR/docker-compose.yml" stop frontend
sudo certbot renew --standalone --non-interactive
sudo cp /etc/letsencrypt/live/$YOUR_DOMAIN/fullchain.pem "$SCRIPT_DIR/nginx/ssl/nginx.crt"
sudo cp /etc/letsencrypt/live/$YOUR_DOMAIN/privkey.pem "$SCRIPT_DIR/nginx/ssl/nginx.key"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" start frontend

echo "[$(date)] Certificate renewed successfully."
