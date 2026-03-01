#!/bin/bash

# Configuration
SSL_DIR="./nginx/ssl"
CRT_FILE="$SSL_DIR/nginx.crt"
KEY_FILE="$SSL_DIR/nginx.key"
DAYS=3650 # 10 years

# Ensure SSL directory exists
mkdir -p "$SSL_DIR"

echo "Generating self-signed certificate..."

# Generate self-signed certificate
# -nodes: no passphrase for the key
# -x509: output a self-signed certificate instead of a certificate request
# -newkey rsa:2048: generate a new RSA key of 2048 bits
openssl req -x509 -nodes -days $DAYS -newkey rsa:2048 \
  -keyout "$KEY_FILE" \
  -out "$CRT_FILE" \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=api.local"

echo "Certificates generated in $SSL_DIR"
ls -l "$SSL_DIR"
