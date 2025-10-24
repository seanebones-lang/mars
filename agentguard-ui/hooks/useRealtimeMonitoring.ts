/**
 * React hook for real-time agent monitoring via WebSocket.
 * Handles connection management, message processing, and alert notifications.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useStore } from '@/lib/store';
import toast from 'react-hot-toast';

export interface RealtimeData {
  type: string;
  agent_id: string;
  query: string;
  output: string;
  hallucination_risk: number;
  flagged: boolean;
  confidence: number;
  flagged_segments: string[];
  mitigation?: string;
  timestamp: string;
  claude_explanation: string;
  processing_time_ms: number;
  expected_hallucination?: boolean;
  detection_accuracy?: boolean;
}

export interface ConnectionStats {
  total_responses: number;
  flagged_responses: number;
  flagged_rate: number;
  session_duration_seconds: number;
  responses_per_minute: number;
  agents: Record<string, { responses: number; flagged: number }>;
  is_monitoring: boolean;
}

export interface UseRealtimeMonitoringReturn {
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
  connectionState: 'disconnected' | 'connecting' | 'connected' | 'error';
  lastMessage: RealtimeData | null;
  connectionStats: ConnectionStats | null;
  error: string | null;
  reconnectAttempts: number;
}

export function useRealtimeMonitoring(): UseRealtimeMonitoringReturn {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connectionState, setConnectionState] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const [lastMessage, setLastMessage] = useState<RealtimeData | null>(null);
  const [connectionStats, setConnectionStats] = useState<ConnectionStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  
  const { addRealtimeResult } = useStore();
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const maxReconnectAttempts = 5;
  const reconnectDelay = 2000; // 2 seconds

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const showNotification = useCallback((data: RealtimeData) => {
    if (data.flagged && 'Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(`🚨 Hallucination Detected: ${data.agent_id}`, {
        body: `Risk: ${(data.hallucination_risk * 100).toFixed(1)}% - ${data.flagged_segments.join(', ')}`,
        icon: '/warning-icon.png',
        tag: `hallucination-${data.agent_id}`, // Prevent duplicate notifications
        requireInteraction: true
      });

      // Auto-close after 5 seconds
      setTimeout(() => notification.close(), 5000);
    }
  }, []);

  const playAlertSound = useCallback(() => {
    try {
      const audio = new Audio('/alert-sound.mp3');
      audio.volume = 0.3; // Moderate volume
      audio.play().catch(() => {
        // Ignore audio play failures (user interaction required, etc.)
      });
    } catch (error) {
      // Ignore audio errors
    }
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'detection_result':
          setLastMessage(data);
          addRealtimeResult(data);
          
          // Show alerts for flagged responses
          if (data.flagged) {
            toast.error(
              `🚨 ${data.agent_id}: ${data.flagged_segments.join(', ')}`,
              {
                duration: 5000,
                position: 'top-right',
                style: {
                  background: '#f44336',
                  color: 'white',
                  fontWeight: 'bold'
                }
              }
            );
            
            playAlertSound();
            showNotification(data);
          } else {
            // Show success toast for clean responses (less prominent)
            toast.success(
              `✅ ${data.agent_id}: Clean response`,
              {
                duration: 2000,
                position: 'bottom-right',
                style: {
                  background: '#4caf50',
                  color: 'white'
                }
              }
            );
          }
          break;
          
        case 'monitoring_started':
          toast.success('🟢 Live monitoring started', { duration: 3000 });
          setError(null);
          break;
          
        case 'monitoring_stopped':
          toast('🔴 Live monitoring stopped', { duration: 3000 });
          if (data.stats) {
            setConnectionStats(data.stats);
          }
          break;
          
        case 'connection_established':
          console.log('WebSocket connection established');
          setError(null);
          setReconnectAttempts(0);
          break;
          
        case 'keepalive':
          // Handle keepalive pings
          break;
          
        case 'error':
          console.error('Server error:', data.message);
          setError(data.message);
          toast.error(`Server error: ${data.message}`);
          break;
          
        case 'processing_error':
          console.error('Processing error:', data.error);
          toast.error(`Processing error for ${data.agent_id}: ${data.error}`);
          break;
          
        default:
          console.log('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, [addRealtimeResult, playAlertSound, showNotification]);

  const attemptReconnect = useCallback(() => {
    if (reconnectAttempts < maxReconnectAttempts) {
      setReconnectAttempts(prev => prev + 1);
      
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`Reconnection attempt ${reconnectAttempts + 1}/${maxReconnectAttempts}`);
        // Call connect directly without dependency
        if (socket && socket.readyState === WebSocket.OPEN) {
          console.log('WebSocket already connected');
          setConnectionState('connected');
          return;
        }

        // Close existing socket if it exists
        if (socket) {
          socket.close();
          setSocket(null);
        }

        setConnectionState('connecting');
        setError(null);

        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
          const wsUrl = apiUrl.replace(/^http/, 'ws') + '/ws/monitor';
          
          console.log('Reconnecting to WebSocket:', wsUrl);
          const ws = new WebSocket(wsUrl);

          ws.onopen = () => {
            console.log('WebSocket reconnected successfully');
            setConnectionState('connected');
            setSocket(ws);
            setError(null);
            setReconnectAttempts(0);
            
            // Send initial ping
            ws.send(JSON.stringify({ type: 'ping' }));
          };

          ws.onmessage = handleMessage;

          ws.onclose = (event) => {
            console.log('WebSocket closed during reconnect:', event.code, event.reason);
            setConnectionState('disconnected');
            setSocket(null);
          };

          ws.onerror = (error) => {
            console.error('WebSocket error during reconnect:', error);
            setConnectionState('error');
            setError('WebSocket reconnection error');
          };

        } catch (error) {
          console.error('Failed to reconnect WebSocket:', error);
          setConnectionState('error');
          setError('Failed to create WebSocket reconnection');
        }
      }, reconnectDelay * Math.pow(2, reconnectAttempts)); // Exponential backoff
    } else {
      setConnectionState('error');
      setError('Maximum reconnection attempts reached');
      toast.error('Connection failed - please refresh the page');
    }
  }, [reconnectAttempts, socket, handleMessage]);

  const connect = useCallback(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      setConnectionState('connected');
      return;
    }

    // Close existing socket if it exists
    if (socket) {
      socket.close();
      setSocket(null);
    }

    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    setConnectionState('connecting');
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const wsUrl = apiUrl.replace(/^http/, 'ws') + '/ws/monitor';
      
      console.log('Connecting to WebSocket:', wsUrl);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setConnectionState('connected');
        setSocket(ws);
        setError(null);
        setReconnectAttempts(0);
        
        // Send initial ping
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setConnectionState('disconnected');
        setSocket(null);
        
        // Only attempt reconnect if it wasn't a manual disconnect
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          setTimeout(() => {
            console.log(`Reconnection attempt after close`);
            // Trigger reconnection
            setConnectionState('connecting');
          }, reconnectDelay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState('error');
        setError('WebSocket connection error');
        
        // Attempt reconnect on error
        if (reconnectAttempts < maxReconnectAttempts) {
          setReconnectAttempts(prev => prev + 1);
          setTimeout(() => {
            console.log(`Reconnection attempt after error`);
            setConnectionState('connecting');
          }, reconnectDelay);
        }
      };

      // Set up periodic ping to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        } else {
          clearInterval(pingInterval);
        }
      }, 30000); // Ping every 30 seconds

      // Clean up ping interval when socket closes
      ws.addEventListener('close', () => {
        clearInterval(pingInterval);
      });

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionState('error');
      setError('Failed to create WebSocket connection');
    }
  }, [socket, handleMessage, attemptReconnect, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.close(1000, 'Manual disconnect'); // Normal closure
      setSocket(null);
    }
    
    setConnectionState('disconnected');
    setError(null);
    setReconnectAttempts(0);
    console.log('WebSocket disconnected manually');
  }, [socket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  return {
    connect,
    disconnect,
    isConnected: connectionState === 'connected',
    connectionState,
    lastMessage,
    connectionStats,
    error,
    reconnectAttempts
  };
}
