# Vercel Deployment Configuration for NextJS Frontend

# Build settings in vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "AUTH0_SECRET": "@auth0-secret",
    "AUTH0_BASE_URL": "@auth0-base-url",
    "AUTH0_ISSUER_BASE_URL": "@auth0-issuer-base-url",
    "AUTH0_CLIENT_ID": "@auth0-client-id",
    "AUTH0_CLIENT_SECRET": "@auth0-client-secret",
    "NEXT_PUBLIC_API_URL": "@next-public-api-url"
  }
}

# Environment Variables to set in Vercel Dashboard:
# 
# AUTH0_SECRET=your-long-random-string-for-session-encryption
# AUTH0_BASE_URL=https://your-vercel-app.vercel.app
# AUTH0_ISSUER_BASE_URL=https://your-auth0-domain.auth0.com
# AUTH0_CLIENT_ID=your-auth0-client-id
# AUTH0_CLIENT_SECRET=your-auth0-client-secret
# NEXT_PUBLIC_API_URL=http://your-vm-ip-or-domain
# NODE_ENV=production

# Deployment Steps:
# 1. Push your frontend code to GitHub
# 2. Connect repository to Vercel
# 3. Set environment variables in Vercel dashboard
# 4. Deploy automatically on push to main branch

# Auth0 Configuration Required:
# - Allowed Callback URLs: https://your-vercel-app.vercel.app/api/auth/callback
# - Allowed Logout URLs: https://your-vercel-app.vercel.app
# - Allowed Web Origins: https://your-vercel-app.vercel.app
# - Allowed Origins (CORS): https://your-vercel-app.vercel.app