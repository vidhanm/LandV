#!/bin/bash

# Multi-Device Authentication System Deployment Script
# This script sets up the backend on an Ubuntu VM

set -e

echo "🚀 Starting Multi-Device Authentication Backend Deployment"

# Configuration
PROJECT_NAME="multi-device-auth"
PROJECT_DIR="/home/ubuntu/$PROJECT_NAME"
BACKEND_DIR="$PROJECT_DIR/backend"
SERVICE_NAME="multi-device-auth"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    print_error "Please run this script as the ubuntu user"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git

# Install Node.js (for frontend tooling if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create project directory
print_status "Creating project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone or copy your project files here
print_warning "Please copy your project files to $PROJECT_DIR"
print_warning "Make sure the backend folder contains all Python files"

# Create Python virtual environment
print_status "Creating Python virtual environment..."
cd $BACKEND_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up PostgreSQL database
print_status "Setting up PostgreSQL database..."
sudo -u postgres createdb ${PROJECT_NAME//-/_} || true
sudo -u postgres psql -c "CREATE USER ${PROJECT_NAME//-/_} WITH PASSWORD 'your-secure-password';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${PROJECT_NAME//-/_} TO ${PROJECT_NAME//-/_};" || true

# Create .env file template
print_status "Creating environment file template..."
cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://${PROJECT_NAME//-/_}:your-secure-password@localhost/${PROJECT_NAME//-/_}

# Auth0 Configuration (REPLACE WITH YOUR VALUES)
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_IDENTIFIER=your-api-identifier

# Application Configuration
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
MAX_DEVICES=2
SESSION_TIMEOUT_HOURS=24

# Frontend Configuration (REPLACE WITH YOUR VERCEL URL)
FRONTEND_URL=https://your-vercel-app.vercel.app
CORS_ORIGINS=http://localhost:3000,https://*.vercel.app
EOF

print_warning "Please edit $BACKEND_DIR/.env with your actual Auth0 and database credentials"

# Test database connection and create tables
print_status "Creating database tables..."
python3 database.py

# Install and configure systemd service
print_status "Installing systemd service..."
sudo cp ../deployment/multi-device-auth.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Configure Nginx
print_status "Configuring Nginx..."
sudo cp ../deployment/nginx.conf /etc/nginx/sites-available/$PROJECT_NAME
sudo ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx

# Set up firewall
print_status "Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create startup script
print_status "Creating startup script..."
cat > start.sh << EOF
#!/bin/bash
cd $BACKEND_DIR
source venv/bin/activate
python3 database.py  # Ensure tables exist
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
EOF
chmod +x start.sh

# Create deployment script for updates
cat > deploy.sh << EOF
#!/bin/bash
cd $BACKEND_DIR
source venv/bin/activate
pip install -r requirements.txt
python3 database.py  # Update tables if needed
sudo systemctl restart $SERVICE_NAME
sudo systemctl restart nginx
echo "Deployment completed!"
EOF
chmod +x deploy.sh

print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/$PROJECT_NAME << EOF
/var/log/nginx/$PROJECT_NAME.*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
EOF

# Final instructions
print_status "Deployment setup completed!"
echo
echo "🔧 Next steps:"
echo "1. Edit $BACKEND_DIR/.env with your Auth0 credentials"
echo "2. Update the server_name in /etc/nginx/sites-available/$PROJECT_NAME"
echo "3. Start the services:"
echo "   sudo systemctl start $SERVICE_NAME"
echo "   sudo systemctl start nginx"
echo "4. Check service status:"
echo "   sudo systemctl status $SERVICE_NAME"
echo "   sudo systemctl status nginx"
echo "5. View logs:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   sudo tail -f /var/log/nginx/$PROJECT_NAME.error.log"
echo
echo "🌐 Your API will be available at: http://your-server-ip"
echo "📝 Remember to update your Vercel environment variables with your server URL"

print_warning "Don't forget to configure your domain/SSL certificates for production!"