---
description: Deploying the application to an AWS EC2 instance using Docker Compose.
---

# AWS EC2 Deployment Guide

Deploying on AWS EC2 gives you the flexibility of the AWS ecosystem. For this application, a **t3.medium** (2 vCPUs, 4 GiB RAM) is the recommended minimum to handle the API, Worker, and Redis.

---

## Step 1: Launch an EC2 Instance
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/ec2/).
2. Click **"Launch instance"**.
3. **Name**: Give your instance a name (e.g., `french-admission-app`).
4. **AMI**: Select **Ubuntu 24.04 LTS (64-bit x86)**.
5. **Instance Type**: Select **t3.medium** (2 vCPU, 4 GiB Memory).
6. **Key pair**: Create a new key pair. You will need this `.pem` file to SSH in.
7. **Network Settings** — Open these ports:

| Port | Protocol | Purpose | Access |
| :--- | :--- | :--- | :--- |
| 22 | TCP | SSH (Management) | Your IP |
| 80 | TCP | HTTP (Needed for HTTPS verification) | Anywhere (0.0.0.0/0) |
| 443 | TCP | HTTPS (Website) | Anywhere (0.0.0.0/0) |

> [!IMPORTANT]
> Port 80 must be open even if you want HTTPS only. Let's Encrypt uses it to verify you own the domain.

## Step 2: Find Your Free AWS Domain
AWS gives every EC2 instance a free public DNS hostname. Find yours in the EC2 Console → select your instance → look for **"Public IPv4 DNS"**. It looks like:
```
ec2-13-234-56-78.ap-south-1.compute.amazonaws.com
```
You will use this as your domain. **No purchase required.**

## Step 3: Connect and Setup
SSH into your instance:
```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```
Update system:
```bash
sudo apt update && sudo apt upgrade -y
```

## Step 4: Install Docker & Docker Compose
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker  # Apply group changes without logging out
```

## Step 5: Deploy the App
1. **Clone the Repo**:
   ```bash
   git clone <your-repo-url>
   cd french_admission_workflow-main
   ```
2. **Setup Environment Variables**:
   ```bash
   nano .env
   # Paste your OpenAI/Claude API keys and other secrets
   ```
3. **Run with Docker Compose**:
   ```bash
   docker compose up -d --build
   ```

## Step 6: Set Up Trusted HTTPS (Free, No Browser Warnings)

This is a one-time setup that gives you a fully trusted SSL certificate using **Let's Encrypt**.

### 6a. Edit the setup script
Open the script and fill in your AWS domain and email:
```bash
nano scripts/setup-https.sh
```
Change these two lines:
```bash
YOUR_DOMAIN="ec2-CHANGE-ME.ap-south-1.compute.amazonaws.com"  # Your AWS public DNS
YOUR_EMAIL="your-email@example.com"                              # Any valid email
```

### 6b. Run the setup script
```bash
chmod +x scripts/setup-https.sh
bash scripts/setup-https.sh
```

This script will:
1. Install Certbot on the server.
2. Temporarily pause Nginx.
3. Verify your domain with Let's Encrypt.
4. Issue a **fully trusted SSL certificate**.
5. Restart Nginx with the new certificate.

### 6c. Set Up Auto-Renewal (Important!)
Let's Encrypt certificates expire every **90 days**. Set up a cron job to auto-renew:
```bash
chmod +x scripts/renew-certs.sh
crontab -e
```
Add this line at the bottom:
```
0 3 * * * /home/ubuntu/french_admission_workflow-main/scripts/renew-certs.sh >> /home/ubuntu/renew-certs.log 2>&1
```

### 6d. Access Your App
```
https://ec2-13-234-56-78.ap-south-1.compute.amazonaws.com
```
✅ Green padlock. No warnings. Fully trusted HTTPS.

---

## Step 7: Stickiness (Elastic IP) — Optional but Recommended
EC2 public IPs **and DNS names** can change if the instance is stopped.
1. Go to **"Elastic IPs"** in the EC2 Console.
2. Click **"Allocate Elastic IP address"**.
3. Select it → **"Associate Elastic IP address"** → select your instance.

> [!NOTE]
> If you use an Elastic IP, your public DNS hostname will also change to match the new IP. You will need to re-run `setup-https.sh` with the new domain name.

---

### Cost Management Tips:
- **Savings Plans/Reserved Instances**: If you plan to run this 24/7 for a year, you can save ~40% by committing to a 1-year term.
- **Data Transfer**: AWS charges for data leaving the server. Keep an eye on high-resolution image uploads/downloads.
- **Elastic IP**: An Elastic IP is free as long as it's associated with a running instance. You're charged if the instance is stopped.
