'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { Loader2, Shield } from 'lucide-react';
import { useEffect } from 'react';

export default function Home() {
  const { user, error, isLoading } = useUser();

  useEffect(() => {
    if (user) {
      // Redirect to dashboard if user is logged in
      window.location.href = '/dashboard';
    }
  }, [user]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
      <div className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 text-white rounded-full mb-6">
            <Shield className="h-8 w-8" />
          </div>
          
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Multi-Device Authentication
          </h1>
          <p className="text-gray-600 mb-8">
            Secure authentication system with intelligent device management
          </p>
          <a 
            href="/api/auth/login"
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            Sign In with Auth0
          </a>
          
          {error && (
            <div className="mt-4 text-sm text-red-600">
              <p>Authentication error: {error.message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
