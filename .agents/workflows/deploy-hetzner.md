---
description: Deploying the application to a Hetzner CX21 VPS using Docker Compose.
---

# Hetzner CX21 Deployment Guide

The Hetzner CX21 is a powerful yet affordable Cloud VPS with **2 vCPUs and 4 GB RAM**. This is perfect for this application because it can easily handle the FastAPI backend, the Celery worker, and the Redis instance all on one machine.

### Why CX21 is different:
- **Dedicated Resources**: Unlike "Serverless" options (like Vercel/Railway) which share resources and can have "cold starts," a VPS is always running and yours alone.
- **Fixed Cost**: You pay ~$5/month regardless of how many documents you process (excluding LLM API costs).
- **Control**: You have full root access to the machine.

---

## Step 1: Create the Server
1. Log in to [Hetzner Cloud Console](https://console.hetzner.cloud/).
2. Create a new project (e.g., "French-Admission").
3. Click "Add Server".
4. **Location**: Pick the one closest to your users (e.g., Falkenstein or Nuremberg).
5. **Image**: Select **Ubuntu 24.04**.
6. **Type**: Select **CX21**.
7. **SSH Key**: Add your public SSH key (recommended) or choose password.
8. Click "Create & Buy".

## Step 2: Initial Server Setup
SSH into your new server:
```bash
ssh root@your_server_ip
```
Update the system:
```bash
apt update && apt upgrade -y
```

## Step 3: Install Docker
Install Docker and Docker Compose using the official script:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

## Step 4: Deploy the Application
1. **Clone your repository**:
   ```bash
   git clone <your-repo-url>
   cd french_admission_workflow-main
   ```
2. **Setup Environment Variables**:
   Create a `.env` file from your existing template:
   ```bash
   nano .env
   ```
   *Paste your API keys and production settings here (Claude/OpenAI keys, etc.).*

3. **Build and Start**:
   ```bash
   docker compose up -d --build
   ```

## Step 5: Domain and Security (Optional but Recommended)
For a professional production setup, you should:
- **Point a domain** to your server IP.
- **Setup an SSL Certificate** (Let's Encrypt) using Nginx or Caddy.

### Accessing the App:
- **Frontend**: http://your_server_ip
- **Backend API**: http://your_server_ip:8000
