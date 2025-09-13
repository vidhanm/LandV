'use client';

import { useUser, withPageAuthRequired } from '@auth0/nextjs-auth0/client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Phone, 
  Mail, 
  Smartphone, 
  Shield, 
  LogOut, 
  RefreshCw,
  Clock,
  MapPin
} from 'lucide-react';
import { toast } from 'sonner';
import DeviceConflictModal from '@/components/DeviceConflictModal';
import LogoutNotification from '@/components/LogoutNotification';
import { ApiService, WebSocketClient, handleApiError, isDeviceConflictError } from '@/lib/api';

interface DeviceSession {
  id: number;
  device_id: string;
  user_agent: string;
  ip_address: string;
  login_time: string;
  last_active: string;
}

function DashboardPage() {
  const { user, isLoading } = useUser();
  const [sessions, setSessions] = useState<DeviceSession[]>([]);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [apiService, setApiService] = useState<ApiService | null>(null);
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  
  // Modal states
  const [showDeviceConflict, setShowDeviceConflict] = useState(false);
  const [showLogoutNotification, setShowLogoutNotification] = useState(false);
  const [conflictData, setConflictData] = useState<any>(null);
  const [logoutReason, setLogoutReason] = useState<string>('force_logout');

  useEffect(() => {
    if (user) {
      // Initialize API service (we'll need to get the access token)
      const api = new ApiService();
      setApiService(api);
      
      // Initialize WebSocket client
      const ws = new WebSocketClient(user.sub!);
      setWsClient(ws);
      
      // Set up WebSocket event handlers
      ws.onLogout((data) => {
        setLogoutReason(data.reason || 'force_logout');
        setShowLogoutNotification(true);
        
        // Redirect to login after showing notification
        setTimeout(() => {
          window.location.href = '/api/auth/logout?returnTo=' + 
            encodeURIComponent(window.location.origin + '/?logout=forced');
        }, 3000);
      });
      
      ws.onDeviceConflict((data) => {
        toast.info('New device conflict detected on another device');
      });
      
      ws.connect();
      
      // Cleanup on unmount
      return () => {
        ws.disconnect();
      };
    }
  }, [user]);

  useEffect(() => {
    if (apiService && user) {
      loadUserData();
      registerDevice();
    }
  }, [apiService, user]);

  const loadUserData = async () => {
    if (!apiService) return;
    
    try {
      // Load user profile
      const profile = await apiService.getUserProfile();
      setUserProfile(profile);
      
      // Load sessions
      await loadSessions();
    } catch (error) {
      console.error('Failed to load user data:', error);
      toast.error('Failed to load user data');
    }
  };

  const loadSessions = async () => {
    if (!apiService) return;
    
    try {
      setLoadingSessions(true);
      const response = await apiService.getUserSessions();
      setSessions(response.active_sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      toast.error('Failed to load device sessions');
    } finally {
      setLoadingSessions(false);
    }
  };

  const registerDevice = async () => {
    if (!apiService) return;
    
    try {
      const result = await apiService.registerDevice();
      
      if (result.conflict) {
        setConflictData(result);
        setShowDeviceConflict(true);
      } else {
        toast.success('Device registered successfully');
        loadSessions(); // Refresh sessions
      }
    } catch (error) {
      if (isDeviceConflictError(error)) {
        setConflictData(error.response.data);
        setShowDeviceConflict(true);
      } else {
        console.error('Device registration failed:', error);
        toast.error(handleApiError(error));
      }
    }
  };

  const handleForceLogout = async (deviceId: string) => {
    if (!apiService) return;
    
    try {
      await apiService.forceLogoutDevice(deviceId);
      toast.success('Device logged out and current device registered');
      setShowDeviceConflict(false);
      loadSessions(); // Refresh sessions
    } catch (error) {
      console.error('Force logout failed:', error);
      toast.error(handleApiError(error));
    }
  };

  const handleLogout = async () => {
    try {
      if (apiService) {
        await apiService.logoutCurrentDevice();
      }
      window.location.href = '/api/auth/logout';
    } catch (error) {
      console.error('Logout failed:', error);
      // Continue with logout even if API call fails
      window.location.href = '/api/auth/logout';
    }
  };

  const getDeviceInfo = (userAgent: string) => {
    const ua = userAgent.toLowerCase();
    
    let deviceType = 'Desktop';
    let deviceIcon = '🖥️';
    
    if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
      deviceType = 'Mobile';
      deviceIcon = '📱';
    } else if (ua.includes('tablet') || ua.includes('ipad')) {
      deviceType = 'Tablet';
      deviceIcon = '📟';
    }
    
    let browser = 'Unknown';
    if (ua.includes('chrome')) browser = 'Chrome';
    else if (ua.includes('firefox')) browser = 'Firefox';
    else if (ua.includes('safari')) browser = 'Safari';
    else if (ua.includes('edge')) browser = 'Edge';
    
    return { deviceType, deviceIcon, browser };
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Shield className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            </div>
            <button
              onClick={handleLogout}
              className="btn-secondary flex items-center space-x-2"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* User Profile */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="card"
            >
              <div className="card-header">
                <h2 className="text-xl font-semibold text-gray-900">Profile</h2>
              </div>
              
              <div className="space-y-6">
                {/* Profile Picture */}
                <div className="text-center">
                  <div className="relative inline-block">
                    <img
                      src={user?.picture || '/default-avatar.png'}
                      alt="Profile"
                      className="w-24 h-24 rounded-full border-4 border-primary-100"
                    />
                    <div className="absolute bottom-0 right-0 w-6 h-6 bg-green-500 rounded-full border-2 border-white"></div>
                  </div>
                </div>

                {/* User Info */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <User className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Full Name</p>
                      <p className="font-medium text-gray-900">
                        {userProfile?.name || user?.name || 'Not provided'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Mail className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium text-gray-900">
                        {userProfile?.email || user?.email}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Phone className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-500">Phone Number</p>
                      <p className="font-medium text-gray-900">
                        {userProfile?.phone || 'Not provided'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Active Sessions */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="card"
            >
              <div className="card-header flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Active Devices</h2>
                <button
                  onClick={loadSessions}
                  disabled={loadingSessions}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingSessions ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </button>
              </div>

              {loadingSessions ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {sessions.length === 0 ? (
                    <div className="text-center py-12">
                      <Smartphone className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">No active sessions found</p>
                    </div>
                  ) : (
                    sessions.map((session, index) => {
                      const deviceInfo = getDeviceInfo(session.user_agent);
                      return (
                        <motion.div
                          key={session.id}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.1 }}
                          className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors duration-200"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className="text-3xl">{deviceInfo.deviceIcon}</div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <p className="font-medium text-gray-900">
                                    {deviceInfo.deviceType} - {deviceInfo.browser}
                                  </p>
                                  <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                    Active
                                  </span>
                                </div>
                                <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                                  <div className="flex items-center space-x-1">
                                    <MapPin className="w-4 h-4" />
                                    <span>IP: {session.ip_address}</span>
                                  </div>
                                  <div className="flex items-center space-x-1">
                                    <Clock className="w-4 h-4" />
                                    <span>
                                      Active: {new Date(session.last_active).toLocaleString()}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })
                  )}
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </main>

      {/* Modals */}
      {showDeviceConflict && conflictData && (
        <DeviceConflictModal
          isOpen={showDeviceConflict}
          onClose={() => setShowDeviceConflict(false)}
          onCancelLogin={() => {
            setShowDeviceConflict(false);
            window.location.href = '/api/auth/logout';
          }}
          onForceLogout={handleForceLogout}
          currentSessions={conflictData.current_sessions || []}
          maxDevices={conflictData.max_devices || 2}
          newDeviceInfo={{
            user_agent: navigator.userAgent,
            ip_address: 'Current Device'
          }}
        />
      )}

      {showLogoutNotification && (
        <LogoutNotification
          isOpen={showLogoutNotification}
          onClose={() => setShowLogoutNotification(false)}
          reason={logoutReason as any}
          autoClose={false}
        />
      )}
    </div>
  );
}

// Wrap with Auth0's page protection
export default withPageAuthRequired(DashboardPage);