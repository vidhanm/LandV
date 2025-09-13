'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, LogOut } from 'lucide-react';

interface LogoutNotificationProps {
  isOpen: boolean;
  onClose: () => void;
  reason?: 'force_logout' | 'session_expired' | 'device_limit' | 'security_logout';
  message?: string;
  autoClose?: boolean;
  autoCloseDelay?: number;
}

const getReasonConfig = (reason: string) => {
  const configs = {
    force_logout: {
      icon: LogOut,
      title: 'Account Accessed from New Device',
      defaultMessage: 'You have been logged out because this account was accessed from a new device. This is a security measure to protect your account.',
      color: 'blue'
    },
    session_expired: {
      icon: AlertCircle,
      title: 'Session Expired',
      defaultMessage: 'Your session has expired for security reasons. Please sign in again to continue.',
      color: 'yellow'
    },
    device_limit: {
      icon: AlertCircle,
      title: 'Device Limit Reached',
      defaultMessage: 'You have been logged out because the maximum number of devices for your account has been exceeded.',
      color: 'orange'
    },
    security_logout: {
      icon: AlertCircle,
      title: 'Security Logout',
      defaultMessage: 'You have been logged out for security reasons. Please sign in again.',
      color: 'red'
    }
  };

  return configs[reason as keyof typeof configs] || configs.force_logout;
};

export default function LogoutNotification({
  isOpen,
  onClose,
  reason = 'force_logout',
  message,
  autoClose = true,
  autoCloseDelay = 10000
}: LogoutNotificationProps) {
  const config = getReasonConfig(reason);
  const IconComponent = config.icon;

  useEffect(() => {
    if (isOpen && autoClose) {
      const timer = setTimeout(() => {
        onClose();
      }, autoCloseDelay);

      return () => clearTimeout(timer);
    }
  }, [isOpen, autoClose, autoCloseDelay, onClose]);

  const handleSignInAgain = () => {
    window.location.href = '/api/auth/login';
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="modal-backdrop">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", duration: 0.3 }}
            className="modal-content max-w-lg"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-full bg-${config.color}-100`}>
                  <IconComponent className={`w-6 h-6 text-${config.color}-600`} />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {config.title}
                  </h3>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Message */}
            <div className="mb-8">
              <p className="text-gray-600 leading-relaxed">
                {message || config.defaultMessage}
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 sm:justify-end">
              <button
                onClick={onClose}
                className="btn-secondary w-full sm:w-auto order-2 sm:order-1"
              >
                Close
              </button>
              <button
                onClick={handleSignInAgain}
                className="btn-primary w-full sm:w-auto order-1 sm:order-2"
              >
                Sign In Again
              </button>
            </div>

            {/* Auto-close indicator */}
            {autoClose && (
              <motion.div
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: autoCloseDelay / 1000, ease: 'linear' }}
                className={`mt-4 h-1 bg-${config.color}-200 rounded-full overflow-hidden`}
              >
                <div className={`h-full bg-${config.color}-500 transition-all duration-100`}></div>
              </motion.div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}