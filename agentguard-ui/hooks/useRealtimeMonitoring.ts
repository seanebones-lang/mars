/**
 * React hook for real-time agent monitoring via WebSocket.
 * Handles connection management, message processing, and alert notifications.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useStore } from '@/lib/store';
import toast from 'react-hot-toast';
import { audioAlerts } from '@/lib/audioAlerts';
import { persistentAlerts } from '@/lib/persistentAlerts';
import { realtimeStats } from '@/lib/realtimeStats';

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
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
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
      const notification = new Notification(`Hallucination Detected: ${data.agent_id}`, {
        body: `Risk: ${(data.hallucination_risk * 100).toFixed(1)}% - ${data.flagged_segments.join(', ')}`,
        icon: '/warning-icon.png',
        tag: `hallucination-${data.agent_id}`, // Prevent duplicate notifications
        requireInteraction: true
      });

      // Auto-close after 5 seconds
      setTimeout(() => notification.close(), 5000);
    }
  }, []);

  const playAlertSound = useCallback(async (agentId: string, riskScore: number, segments: string[] = []) => {
    try {
      await audioAlerts.playHallucinationAlert(agentId, riskScore, segments);
    } catch (error) {
      console.error('Failed to play audio alert:', error);
    }
  }, []);

  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'detection_result':
          setLastMessage(data);
          addRealtimeResult(data);
          
          // Track stats
          realtimeStats.addResponse({
            agentId: data.agent_id,
            riskScore: data.hallucination_risk,
            latency: data.processing_time_ms,
            flagged: data.flagged,
            timestamp: new Date(data.timestamp)
          });
          
          // Show alerts for flagged responses
          if (data.flagged) {
            toast.error(
              `${data.agent_id}: ${data.flagged_segments.join(', ')}`,
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
            
            playAlertSound(data.agent_id, data.hallucination_risk, data.flagged_segments);
            showNotification(data);
            
            // Create persistent alert for high-risk detections
            if (data.hallucination_risk >= 0.5) {
              persistentAlerts.createHallucinationAlert(
                data.agent_id,
                data.hallucination_risk,
                data.flagged_segments,
                data.mitigation
              );
            }
          } else {
            // Show success toast for clean responses (less prominent)
            toast.success(
              `${data.agent_id}: Clean response`,
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
          toast.success('Live monitoring started', { duration: 3000 });
          audioAlerts.playSystemAlert('monitoring_started');
          setError(null);
          break;
          
        case 'monitoring_stopped':
          toast('Live monitoring stopped', { duration: 3000 });
          audioAlerts.playSystemAlert('monitoring_stopped');
          if (data.stats) {
            setConnectionStats(data.stats);
          }
          break;
          
        case 'connection_established':
          console.log('WebSocket connection established');
          audioAlerts.playSystemAlert('connection_restored');
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
          realtimeStats.recordError();
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
        
        // Play connection lost alert if it wasn't a manual disconnect
        if (event.code !== 1000) {
          audioAlerts.playSystemAlert('connection_lost');
          persistentAlerts.createAlert({
            title: 'Connection Lost',
            message: 'WebSocket connection to monitoring service has been lost',
            severity: 'high',
            category: 'connection',
            metadata: { code: event.code, reason: event.reason }
          });
        }
        
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
        audioAlerts.playSystemAlert('connection_lost');
        persistentAlerts.createAlert({
          title: 'Connection Error',
          message: 'Failed to establish WebSocket connection to monitoring service',
          severity: 'critical',
          category: 'connection',
          metadata: { error: error.toString() }
        });
        
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
