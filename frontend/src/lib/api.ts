import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Device fingerprinting utility
export const generateDeviceFingerprint = (): string => {
  if (typeof window === 'undefined') {
    return 'server-side-render';
  }

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);
  }
  
  const fingerprint = {
    userAgent: navigator.userAgent,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen: `${screen.width}x${screen.height}`,
    canvas: canvas.toDataURL(),
    platform: navigator.platform,
  };
  
  return btoa(JSON.stringify(fingerprint));
};

// Create axios instance with default configuration
const createApiClient = (accessToken?: string): AxiosInstance => {
  const config: AxiosRequestConfig = {
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  };

  if (accessToken) {
    config.headers!['Authorization'] = `Bearer ${accessToken}`;
  }

  const client = axios.create(config);

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add device fingerprint to headers for device management endpoints
      if (config.url?.includes('/device/')) {
        config.headers!['X-Device-Fingerprint'] = generateDeviceFingerprint();
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      // Handle common error scenarios
      if (error.response?.status === 401) {
        // Token expired or invalid - redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/api/auth/login';
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

// API service class
export class ApiService {
  private client: AxiosInstance;

  constructor(accessToken?: string) {
    this.client = createApiClient(accessToken);
  }

  // Update access token
  updateToken(accessToken: string) {
    this.client.defaults.headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Auth endpoints
  async validateToken(): Promise<any> {
    const response = await this.client.post('/auth/validate-token');
    return response.data;
  }

  async getUserProfile(): Promise<any> {
    const response = await this.client.get('/user/profile');
    return response.data;
  }

  // Device management endpoints
  async registerDevice(): Promise<any> {
    const response = await this.client.post('/device/register', {
      fingerprint: generateDeviceFingerprint(),
    });
    return response.data;
  }

  async getUserSessions(): Promise<any> {
    const response = await this.client.get('/device/sessions');
    return response.data;
  }

  async forceLogoutDevice(deviceId: string): Promise<any> {
    const response = await this.client.post('/device/force-logout', {
      device_id: deviceId,
    });
    return response.data;
  }

  async logoutCurrentDevice(): Promise<any> {
    const response = await this.client.delete('/device/logout');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/');
    return response.data;
  }
}

// WebSocket connection utility
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private userId: string;
  private onLogoutCallback?: (data: any) => void;
  private onDeviceConflictCallback?: (data: any) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(userId: string) {
    this.userId = userId;
  }

  connect() {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${this.userId}`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        
        // Send device registration
        this.send({
          type: 'device_registration',
          device_id: generateDeviceFingerprint(),
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.reconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.reconnect();
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'logout_notification':
        if (this.onLogoutCallback) {
          this.onLogoutCallback(data);
        }
        break;
      
      case 'device_conflict':
        if (this.onDeviceConflictCallback) {
          this.onDeviceConflictCallback(data);
        }
        break;
      
      case 'heartbeat_response':
        // Connection is alive
        break;
      
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Attempting to reconnect WebSocket (attempt ${this.reconnectAttempts})`);
        this.connect();
      }, delay);
    } else {
      console.error('Max WebSocket reconnection attempts reached');
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  sendHeartbeat() {
    this.send({ type: 'heartbeat' });
  }

  onLogout(callback: (data: any) => void) {
    this.onLogoutCallback = callback;
  }

  onDeviceConflict(callback: (data: any) => void) {
    this.onDeviceConflictCallback = callback;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Utility functions
export const handleApiError = (error: any): string => {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const isDeviceConflictError = (error: any): boolean => {
  return error.response?.data?.conflict === true;
};

// Export default API client
export const createApiClientWithToken = (accessToken?: string) => new ApiService(accessToken);