#!/bin/bash
# =============================================================================
# setup-https.sh - Sets up trusted HTTPS using Let's Encrypt + Certbot
# =============================================================================
# USAGE: Run this script ONCE after deploying the app on EC2.
# PREREQUISITE: 
#   1) The app must be running (docker compose up -d)
#   2) Port 80 MUST be open in your AWS Security Group
#   3) Replace YOUR_DOMAIN below with your AWS public DNS hostname
#      e.g. ec2-13-234-56-78.ap-south-1.compute.amazonaws.com
# =============================================================================

set -e

# ---- EDIT THIS ----
YOUR_DOMAIN="ec2-CHANGE-ME.ap-south-1.compute.amazonaws.com"
YOUR_EMAIL="your-email@example.com"
# -------------------

echo "=========================================="
echo "  Setting up Let's Encrypt HTTPS"
echo "  Domain: $YOUR_DOMAIN"
echo "=========================================="

# Step 1: Install Certbot on the host
sudo apt-get update -y
sudo apt-get install -y certbot

# Step 2: Temporarily stop Nginx (Certbot needs port 80 for verification)
echo "Stopping Nginx temporarily for verification..."
docker compose stop frontend

# Step 3: Run Certbot in standalone mode to get the certificate
sudo certbot certonly --standalone \
  --non-interactive \
  --agree-tos \
  --email "$YOUR_EMAIL" \
  -d "$YOUR_DOMAIN"

# Step 4: Copy the certificates to our nginx/ssl directory
echo "Copying certificates to nginx/ssl..."
sudo cp /etc/letsencrypt/live/$YOUR_DOMAIN/fullchain.pem nginx/ssl/nginx.crt
sudo cp /etc/letsencrypt/live/$YOUR_DOMAIN/privkey.pem nginx/ssl/nginx.key
sudo chmod 644 nginx/ssl/nginx.crt
sudo chmod 640 nginx/ssl/nginx.key

# Step 5: Restart Nginx with the new certs
echo "Restarting frontend with new certificates..."
docker compose start frontend

echo ""
echo "=========================================="
echo "  DONE! Visit: https://$YOUR_DOMAIN"
echo "=========================================="
echo ""
echo "Auto-renewal: Run 'crontab -e' and add this line:"
echo "  0 3 * * * $(pwd)/scripts/renew-certs.sh"
