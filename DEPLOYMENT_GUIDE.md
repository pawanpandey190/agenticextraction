# AWS Deployment Guide for Document Analysis System

This guide provides a comprehensive path to deploy the application on an AWS EC2 Linux instance.

## 1. AWS EC2 Setup
- **AMI**: Ubuntu 22.04 LTS or Amazon Linux 2023.
- **Instance Type**: `t3.medium` (4GB RAM) is recommended due to memory-intensive OCR tasks.
- **Security Group Rules**:
    - **Port 22**: SSH (Restricted to your IP).
    - **Port 80**: HTTP (Open to all for UI).
    - **Port 8000**: API (Optional - Nginx proxies this, but useful for direct testing).

## 2. Install Docker
On **Ubuntu**:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
# Logout and login back
```

On **Amazon Linux 2023**:
```bash
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
sudo dnf install -y docker-compose-plugin
# Logout and login back
```

## 3. Transfer Code & Setup
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd french_admission_workflow-main
   ```

2. Create your secret `.env` file from the example:
   ```bash
   nano .env
   ```
   Add your keys:
   ```env
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```

3. Update `.env.docker` for Production:
   ```bash
   nano .env.docker
   ```
   Update `DAU_CORS_ORIGINS`:
   ```env
   DAU_CORS_ORIGINS=["http://your-ec2-public-ip", "http://localhost"]
   ```

4. Prepare Logs Directory:
   ```bash
   mkdir -p logs
   chmod 777 logs
   ```

## 4. Launch Application
```bash
docker-compose up -d --build
```

## 5. Maintenance & Monitoring
- **Check Status**: `docker-compose ps`
- **View All Logs**: `tail -f logs/*.log`
- **Nginx Error Logs**: `tail -f logs/error.log`
- **Stop System**: `docker-compose down`

## 6. Troubleshooting
- **Out of Memory**: If the worker crashes, increase instance size or swap.
- **Port Conflict**: Ensure no other service is using port 80.
- **API Errors**: Double check the `.env` file inside the root folder.
