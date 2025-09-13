# Multi-Device Authentication System

A comprehensive multi-device authentication system built with FastAPI backend and Next.js frontend, featuring Auth0 integration, real-time notifications, and intelligent device session management.

## 🚀 Features

- **Multi-Device Support**: Manage user sessions across unlimited devices with configurable limits
- **Real-time Notifications**: WebSocket-based logout notifications and device conflict alerts
- **Device Fingerprinting**: Secure device identification using browser and system characteristics
- **Force Logout**: Allow new devices to securely logout existing devices when limits are reached
- **Professional UI**: Modern, responsive design with Tailwind CSS and Framer Motion animations
- **Auth0 Integration**: Enterprise-grade authentication with JWT token validation
- **Session Management**: Automatic session cleanup and heartbeat monitoring
- **Production Ready**: Complete deployment configurations for VM and Vercel

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (Vercel)      │    │    (Your VM)    │    │ (PostgreSQL)    │
│                 │    │                 │    │                 │
│ Next.js 14      │◄──►│ FastAPI         │◄──►│ Session Storage │
│ Auth0 Client    │    │ Auth0 JWT       │    │ Device Tracking │
│ WebSocket       │    │ WebSocket       │    │ User Profiles   │
│ Tailwind CSS    │    │ Device Manager  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

### Backend (VM)
- Ubuntu 20.04+ server
- Python 3.8+
- PostgreSQL 12+
- Nginx
- Domain name or static IP

### Frontend (Vercel)
- Node.js 18+
- Vercel account
- Auth0 account

### Auth0 Setup
- Auth0 application configured
- API identifier created
- JWT tokens enabled

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd multi-device-auth
```

### 2. Backend Setup (VM)

#### Quick Setup with Deploy Script

```bash
# Make the deploy script executable
chmod +x deployment/deploy.sh

# Run the automated setup
./deployment/deploy.sh
```

#### Manual Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# Create project directory
sudo mkdir -p /home/ubuntu/multi-device-auth
sudo chown ubuntu:ubuntu /home/ubuntu/multi-device-auth
cd /home/ubuntu/multi-device-auth

# Copy backend files
cp -r /path/to/your/backend ./

# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Configure PostgreSQL

```bash
# Create database and user
sudo -u postgres createdb multi_device_auth
sudo -u postgres psql -c "CREATE USER multi_device_auth WITH PASSWORD 'your-secure-password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE multi_device_auth TO multi_device_auth;"
```

#### Configure Environment Variables

Create `/home/ubuntu/multi-device-auth/backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql://multi_device_auth:your-secure-password@localhost/multi_device_auth

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_API_IDENTIFIER=your-api-identifier

# Application Configuration
SECRET_KEY=your-super-secret-key-here
MAX_DEVICES=2
SESSION_TIMEOUT_HOURS=24

# Frontend Configuration
FRONTEND_URL=https://your-vercel-app.vercel.app
CORS_ORIGINS=http://localhost:3000,https://*.vercel.app
```

#### Setup System Service

```bash
# Copy service file
sudo cp deployment/multi-device-auth.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable multi-device-auth
sudo systemctl start multi-device-auth

# Check status
sudo systemctl status multi-device-auth
```

#### Configure Nginx

```bash
# Copy nginx configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/multi-device-auth

# Enable site
sudo ln -s /etc/nginx/sites-available/multi-device-auth /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test and restart nginx
sudo nginx -t
sudo systemctl restart nginx
```

### 3. Frontend Setup (Vercel)

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Configure Environment Variables

Create `frontend/.env.local`:

```bash
# Auth0 Configuration
AUTH0_SECRET=your-super-secret-key-for-sessions
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# API Configuration
NEXT_PUBLIC_API_URL=http://your-vm-ip-or-domain

# Environment
NODE_ENV=development
```

#### Deploy to Vercel

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set environment variables in Vercel dashboard

3. **Vercel Environment Variables**:
   ```
   AUTH0_SECRET=your-long-random-string
   AUTH0_BASE_URL=https://your-vercel-app.vercel.app
   AUTH0_ISSUER_BASE_URL=https://your-auth0-domain.auth0.com
   AUTH0_CLIENT_ID=your-auth0-client-id
   AUTH0_CLIENT_SECRET=your-auth0-client-secret
   NEXT_PUBLIC_API_URL=http://your-vm-ip-or-domain
   NODE_ENV=production
   ```

### 4. Auth0 Configuration

#### Application Settings

In your Auth0 dashboard:

1. **Allowed Callback URLs**:
   ```
   http://localhost:3000/api/auth/callback,
   https://your-vercel-app.vercel.app/api/auth/callback
   ```

2. **Allowed Logout URLs**:
   ```
   http://localhost:3000,
   https://your-vercel-app.vercel.app
   ```

3. **Allowed Web Origins**:
   ```
   http://localhost:3000,
   https://your-vercel-app.vercel.app
   ```

4. **Allowed Origins (CORS)**:
   ```
   http://localhost:3000,
   https://your-vercel-app.vercel.app
   ```

#### API Configuration

1. Create an API in Auth0 dashboard
2. Set the API identifier (use this as `AUTH0_API_IDENTIFIER`)
3. Enable RS256 signing algorithm

## 🧪 Testing Scenarios

### Scenario 1: Normal Multi-Device Login

1. **Device 1**: Login successfully
2. **Device 2**: Login successfully
3. **Verify**: Both devices show in dashboard sessions

### Scenario 2: Device Limit Enforcement

1. **Setup**: Set `MAX_DEVICES=2` in backend `.env`
2. **Device 1**: Login successfully
3. **Device 2**: Login successfully
4. **Device 3**: Attempt login → Device conflict modal appears
5. **Action**: Choose "Force Logout Previous Device"
6. **Result**: Device 1 receives logout notification and is logged out

### Scenario 3: Real-time Logout Notification

1. **Device 1**: Login and stay on dashboard
2. **Device 2**: Login and force logout Device 1
3. **Device 1**: Should receive real-time logout notification
4. **Device 1**: Should be automatically redirected to login

### Scenario 4: Session Management

1. **Login**: Multiple devices
2. **Dashboard**: View all active sessions
3. **Heartbeat**: WebSocket connections maintain sessions
4. **Cleanup**: Old sessions automatically expire

## 🔒 Security Features

### Device Fingerprinting

The system generates unique device IDs using:
- User Agent string
- Screen resolution
- Timezone
- Platform information
- Canvas fingerprinting

### Session Security

- JWT token validation with Auth0
- Secure session storage
- Automatic session cleanup
- Real-time session monitoring
- CORS protection

### Network Security

- Rate limiting on API endpoints
- WebSocket security
- HTTPS enforcement (production)
- Security headers

## 📊 API Documentation

### Authentication Endpoints

```bash
POST /auth/validate-token
Authorization: Bearer <jwt-token>
```

### User Endpoints

```bash
GET /user/profile
Authorization: Bearer <jwt-token>
```

### Device Management Endpoints

```bash
# Register new device
POST /device/register
Authorization: Bearer <jwt-token>

# Get user sessions
GET /device/sessions
Authorization: Bearer <jwt-token>

# Force logout device
POST /device/force-logout
Authorization: Bearer <jwt-token>
Body: {"device_id": "device-hash"}

# Logout current device
DELETE /device/logout
Authorization: Bearer <jwt-token>
```

### WebSocket Endpoint

```bash
WS /ws/{user_id}
```

Message types:
- `heartbeat` - Keep connection alive
- `device_registration` - Register device ID
- `logout_notification` - Receive logout alerts
- `device_conflict` - Receive conflict notifications

## 🚀 Production Deployment

### SSL/HTTPS Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Monitoring

```bash
# View service logs
sudo journalctl -u multi-device-auth -f

# View nginx logs
sudo tail -f /var/log/nginx/multi-device-auth.access.log
sudo tail -f /var/log/nginx/multi-device-auth.error.log

# Monitor system resources
htop
df -h
```

### Scaling Considerations

- **Database**: Consider PostgreSQL connection pooling
- **Backend**: Use multiple uvicorn workers
- **WebSocket**: Implement Redis for multi-instance support
- **CDN**: Use Vercel's edge network for frontend

## 🛠️ Development

### Local Development

#### Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run dev
```

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 🐛 Troubleshooting

### Common Issues

1. **Auth0 Token Issues**:
   - Check Auth0 domain and API identifier
   - Verify callback URLs
   - Ensure JWT algorithm is RS256

2. **WebSocket Connection Failed**:
   - Check CORS settings
   - Verify nginx WebSocket proxy configuration
   - Check firewall settings

3. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure database exists

4. **Device Registration Failed**:
   - Check device fingerprinting
   - Verify session management
   - Check device limit settings

### Logs and Debugging

```bash
# Backend logs
sudo journalctl -u multi-device-auth --since "1 hour ago"

# Nginx logs
sudo tail -100 /var/log/nginx/multi-device-auth.error.log

# Frontend logs (Vercel)
# Check Vercel dashboard → Functions → View Function Logs
```

## 📈 Performance Optimization

### Backend Optimizations

- Use connection pooling for PostgreSQL
- Implement caching for user sessions
- Optimize WebSocket connection management
- Use async/await patterns consistently

### Frontend Optimizations

- Implement proper image optimization
- Use dynamic imports for components
- Optimize bundle size
- Implement service worker for caching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Built with ❤️ using FastAPI, Next.js, and Auth0**