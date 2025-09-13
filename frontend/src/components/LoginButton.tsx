'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { LogIn, Loader2 } from 'lucide-react';

interface LoginButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function LoginButton({ 
  variant = 'primary', 
  size = 'md',
  className = '' 
}: LoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    try {
      // Redirect to Auth0 login
      window.location.href = '/api/auth/login';
    } catch (error) {
      console.error('Login error:', error);
      setIsLoading(false);
    }
  };

  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:ring-4 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white focus:ring-primary-200 shadow-lg hover:shadow-xl',
    secondary: 'bg-white hover:bg-gray-50 text-primary-600 border-2 border-primary-600 focus:ring-primary-200 shadow-lg hover:shadow-xl'
  };

  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg'
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={handleLogin}
      disabled={isLoading}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Signing In...
        </>
      ) : (
        <>
          <LogIn className="w-5 h-5 mr-2" />
          Sign In with Auth0
        </>
      )}
    </motion.button>
  );
}