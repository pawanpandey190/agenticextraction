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
   *Note: t3.micro may be too small for the background worker tasks.*
6. **Key pair**: Create a new key pair or select an existing one. You will need this to SSH into the server.
7. **Network Settings**:
   - Allow SSH traffic from (Anywhere or your IP).
   - Allow HTTPS/HTTP traffic if you plan to use a domain.
   - **Important**: Add a custom Rule for Port **8000** (Backend API) if you plan to access it directly.

## Step 2: Configure Security Groups
Make sure the Following ports are open in your Security Group:
- **22** (SSH)
- **80** (HTTP - for Frontend)
- **8000** (Backend API)
- **443** (HTTPS - if using SSL)

## Step 3: Connect and Setup
SSH into your instance:
```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```

Update and install essential tools:
```bash
sudo apt update && sudo apt upgrade -y
```

## Step 4: Install Docker & Docker Compose
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect
```

## Step 5: Deploy the App
1. **Clone the Repo**:
   ```bash
   git clone <your-repo-url>
   cd french_admission_workflow-main
   ```
2. **Setup Environment**:
   ```bash
   nano .env
   # Add your OpenAI/Claude Keys and other secrets
   ```
3. **Run with Docker Compose**:
   ```bash
   docker compose up -d --build
   ```

## Step 6: Stickiness (Elastic IP)
EC2 public IPs can change if the instance is stopped/started. 
1. Go to **"Elastic IPs"** in the EC2 Console.
2. Click **"Allocate Elastic IP address"**.
3. Once allocated, select it and click **"Associate Elastic IP address"**.
4. Select your instance and click **"Associate"**.

---

### Cost Management Tips:
- **Savings Plans/Reserved Instances**: If you plan to run this 24/7 for a year, you can save ~40% by committing to a 1-year term.
- **Data Transfer**: AWS charges for data leaving the server. Keep an eye on high-resolution image uploads/downloads.
