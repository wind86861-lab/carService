#!/bin/bash
# AutoService Deployment Script
# Run this on the server as root

set -e

echo "=== AutoService Deployment ==="

# 1. System update and Docker installation
echo "Installing Docker..."
apt-get update && apt-get upgrade -y
apt-get install -y docker.io docker-compose-plugin git nginx certbot
systemctl enable docker
systemctl start docker

# 2. Create application directory
mkdir -p /opt/autoservice
cd /opt/autoservice

# 3. Clone repository (or pull if exists)
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/wind86861-lab/carService.git .
fi

# 4. Create environment file
cat > autoservice/.env << 'EOF'
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://autoservice:changeme@postgres/autoservice
ADMIN_IDS=your_admin_telegram_ids
BOT_USERNAME=your_bot_username
SECRET_KEY=generate_a_random_secret_key_32chars
ACCESS_TOKEN_EXPIRE_HOURS=24
MAX_PHOTO_SIZE_MB=10
UPLOAD_DIR=/app/uploads
WEB_URL=https://yourdomain.com
POSTGRES_PASSWORD=changeme
DB_USER=autoservice
DB_PASSWORD=changeme
MONITORING_CHAT_ID=your_monitoring_chat_id
EOF

echo "Please edit autoservice/.env with your actual values before continuing!"
read -p "Press Enter after editing .env file..."

# 5. Create uploads directory
mkdir -p uploads

# 6. Build and start services
echo "Building Docker images..."
docker compose build --no-cache

echo "Starting services..."
docker compose up -d

# 7. Cleanup
docker image prune -f

# 8. Health check
echo "Waiting for services to start..."
sleep 10

echo "=== Deployment Status ==="
docker compose ps

echo ""
echo "=== Logs (last 30 lines) ==="
docker compose logs --tail=30

echo ""
echo "=== Next Steps ==="
echo "1. Obtain SSL certificate:"
echo "   certbot certonly --standalone -d yourdomain.com"
echo "   cp /etc/letsencrypt/live/yourdomain.com/*.pem autoservice/nginx/certs/"
echo ""
echo "2. Restart nginx:"
echo "   docker compose restart nginx"
echo ""
echo "3. Set up monitoring cron:"
echo "   crontab -e"
echo "   Add: */5 * * * * cd /opt/autoservice && python3 autoservice/monitoring/healthcheck.py"
echo ""
echo "4. Set up SSL auto-renewal:"
echo "   crontab -e"
echo "   Add: 0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/*.pem /opt/autoservice/autoservice/nginx/certs/ && docker compose restart nginx"
