'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Smartphone, AlertTriangle, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

interface DeviceSession {
  id: number;
  device_id: string;
  user_agent: string;
  ip_address: string;
  login_time: string;
  last_active: string;
}

interface DeviceConflictModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCancelLogin: () => void;
  onForceLogout: (deviceId: string) => Promise<void>;
  currentSessions: DeviceSession[];
  maxDevices: number;
  newDeviceInfo?: {
    user_agent: string;
    ip_address: string;
  };
}

const getDeviceInfo = (userAgent: string) => {
  const ua = userAgent.toLowerCase();
  
  // Device type detection
  let deviceType = 'Desktop';
  let deviceIcon = '🖥️';
  
  if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
    deviceType = 'Mobile';
    deviceIcon = '📱';
  } else if (ua.includes('tablet') || ua.includes('ipad')) {
    deviceType = 'Tablet';
    deviceIcon = '📟';
  }
  
  // Browser detection
  let browser = 'Unknown';
  if (ua.includes('chrome')) browser = 'Chrome';
  else if (ua.includes('firefox')) browser = 'Firefox';
  else if (ua.includes('safari')) browser = 'Safari';
  else if (ua.includes('edge')) browser = 'Edge';
  
  // OS detection
  let os = 'Unknown';
  if (ua.includes('windows')) os = 'Windows';
  else if (ua.includes('mac')) os = 'macOS';
  else if (ua.includes('linux')) os = 'Linux';
  else if (ua.includes('android')) os = 'Android';
  else if (ua.includes('ios')) os = 'iOS';
  
  return { deviceType, deviceIcon, browser, os };
};

export default function DeviceConflictModal({
  isOpen,
  onClose,
  onCancelLogin,
  onForceLogout,
  currentSessions,
  maxDevices,
  newDeviceInfo
}: DeviceConflictModalProps) {
  const [loadingDeviceId, setLoadingDeviceId] = useState<string | null>(null);

  const handleForceLogout = async (deviceId: string) => {
    setLoadingDeviceId(deviceId);
    try {
      await onForceLogout(deviceId);
    } catch (error) {
      console.error('Force logout error:', error);
    } finally {
      setLoadingDeviceId(null);
    }
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
            className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-full bg-orange-100">
                  <AlertTriangle className="w-6 h-6 text-orange-600" />
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    Device Limit Reached
                  </h3>
                  <p className="text-sm text-gray-500">
                    Maximum {maxDevices} devices allowed
                  </p>
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
            <div className="mb-6 p-4 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-orange-800">
                You've reached the maximum number of devices ({maxDevices}) for your account. 
                To continue with this new device, you'll need to log out one of your existing devices.
              </p>
            </div>

            {/* New Device Info */}
            {newDeviceInfo && (
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 mb-3">New Device Trying to Login</h4>
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center space-x-3">
                    <Smartphone className="w-5 h-5 text-blue-600" />
                    <div className="flex-1">
                      <p className="font-medium text-blue-900">
                        {getDeviceInfo(newDeviceInfo.user_agent).deviceType} - {getDeviceInfo(newDeviceInfo.user_agent).browser}
                      </p>
                      <p className="text-sm text-blue-700">
                        {getDeviceInfo(newDeviceInfo.user_agent).os} • IP: {newDeviceInfo.ip_address}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Current Sessions */}
            <div className="mb-8">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Current Active Devices</h4>
              <div className="space-y-3">
                {currentSessions.map((session) => {
                  const deviceInfo = getDeviceInfo(session.user_agent);
                  return (
                    <motion.div
                      key={session.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors duration-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center space-x-3 flex-1">
                          <div className="text-2xl">{deviceInfo.deviceIcon}</div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <p className="font-medium text-gray-900 truncate">
                                {deviceInfo.deviceType} - {deviceInfo.browser}
                              </p>
                              <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                Active
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 truncate">
                              {deviceInfo.os} • IP: {session.ip_address}
                            </p>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                              <span>
                                Logged in: {format(new Date(session.login_time), 'MMM d, yyyy h:mm a')}
                              </span>
                              <span>
                                Last active: {format(new Date(session.last_active), 'MMM d, yyyy h:mm a')}
                              </span>
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleForceLogout(session.device_id)}
                          disabled={loadingDeviceId === session.device_id}
                          className="ml-4 px-3 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors duration-200 flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {loadingDeviceId === session.device_id ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span>Logging out...</span>
                            </>
                          ) : (
                            <>
                              <span>Log Out</span>
                            </>
                          )}
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 pt-6 border-t border-gray-200">
              <button
                onClick={onCancelLogin}
                className="btn-secondary flex-1 order-2 sm:order-1"
              >
                Cancel Login
              </button>
              <div className="flex-1 order-1 sm:order-2">
                <p className="text-xs text-gray-500 mb-2 text-center sm:text-right">
                  Or log out a device above to continue with this new device
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}