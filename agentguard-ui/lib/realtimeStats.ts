/**
 * Watcher-AI Real-time Statistics Manager
 * Tracks and calculates live system performance metrics
 */

export interface SystemMetrics {
  // Detection Performance
  totalResponses: number;
  responsesPerMinute: number;
  flaggedResponses: number;
  flaggedRate: number;
  averageRiskScore: number;
  
  // Timing Metrics
  averageLatency: number;
  minLatency: number;
  maxLatency: number;
  
  // System Health
  systemHealth: number; // 0-100 score
  connectionQuality: number; // 0-100 score
  apiUsage: number; // requests per minute
  errorRate: number; // 0-1
  
  // Agent Performance
  activeAgents: number;
  agentStats: Record<string, AgentMetrics>;
  
  // Session Stats
  sessionDuration: number; // seconds
  sessionStartTime: Date;
  lastUpdateTime: Date;
  
  // Trends (last 5 minutes)
  responseTrend: number[];
  riskTrend: number[];
  latencyTrend: number[];
}

export interface AgentMetrics {
  agentId: string;
  totalResponses: number;
  flaggedResponses: number;
  flaggedRate: number;
  averageRiskScore: number;
  averageLatency: number;
  lastResponseTime: Date;
  isActive: boolean;
  responsesPerMinute: number;
  trend: 'improving' | 'stable' | 'degrading';
}

export interface StatsSettings {
  enabled: boolean;
  updateInterval: number; // milliseconds
  trendWindow: number; // minutes
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'floating';
  compact: boolean;
  showTrends: boolean;
  showAgentBreakdown: boolean;
  autoHide: boolean;
  transparency: number; // 0-1
}

class RealtimeStatsManager {
  private metrics: SystemMetrics;
  private settings: StatsSettings;
  private listeners: Set<(metrics: SystemMetrics) => void> = new Set();
  private updateTimer: NodeJS.Timeout | null = null;
  private responseHistory: Array<{ timestamp: Date; riskScore: number; latency: number; agentId: string; flagged: boolean }> = [];
  private maxHistorySize = 1000;

  constructor() {
    this.settings = this.getDefaultSettings();
    this.metrics = this.initializeMetrics();
    this.startUpdateTimer();
  }

  private getDefaultSettings(): StatsSettings {
    const defaultSettings = {
      enabled: true,
      updateInterval: 2000, // 2 seconds (less aggressive)
      trendWindow: 5, // 5 minutes
      position: 'top-left' as const,
      compact: true, // Start compact
      showTrends: false, // Hide trends by default
      showAgentBreakdown: false, // Hide agent breakdown by default
      autoHide: false,
      transparency: 0.9
    };

    if (typeof window === 'undefined') {
      return defaultSettings;
    }

    const saved = localStorage.getItem('watcher-stats-settings');
    if (saved) {
      try {
        return { ...defaultSettings, ...JSON.parse(saved) };
      } catch (error) {
        console.warn('Failed to parse saved stats settings:', error);
      }
    }

    return defaultSettings;
  }

  private initializeMetrics(): SystemMetrics {
    const now = new Date();
    return {
      totalResponses: 0,
      responsesPerMinute: 0,
      flaggedResponses: 0,
      flaggedRate: 0,
      averageRiskScore: 0,
      averageLatency: 0,
      minLatency: Infinity,
      maxLatency: 0,
      systemHealth: 100,
      connectionQuality: 100,
      apiUsage: 0,
      errorRate: 0,
      activeAgents: 0,
      agentStats: {},
      sessionDuration: 0,
      sessionStartTime: now,
      lastUpdateTime: now,
      responseTrend: [],
      riskTrend: [],
      latencyTrend: []
    };
  }

  private saveSettings() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('watcher-stats-settings', JSON.stringify(this.settings));
    }
  }

  private startUpdateTimer() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }

    this.updateTimer = setInterval(() => {
      this.updateMetrics();
    }, this.settings.updateInterval);
  }

  private updateMetrics() {
    const now = new Date();
    const windowMs = this.settings.trendWindow * 60 * 1000;
    const cutoffTime = new Date(now.getTime() - windowMs);

    // Filter recent responses
    const recentResponses = this.responseHistory.filter(r => r.timestamp >= cutoffTime);
    
    // Calculate basic metrics
    this.metrics.totalResponses = this.responseHistory.length;
    this.metrics.flaggedResponses = this.responseHistory.filter(r => r.flagged).length;
    this.metrics.flaggedRate = this.metrics.totalResponses > 0 ? 
      this.metrics.flaggedResponses / this.metrics.totalResponses : 0;

    // Calculate averages
    if (this.responseHistory.length > 0) {
      this.metrics.averageRiskScore = this.responseHistory.reduce((sum, r) => sum + r.riskScore, 0) / this.responseHistory.length;
      this.metrics.averageLatency = this.responseHistory.reduce((sum, r) => sum + r.latency, 0) / this.responseHistory.length;
      this.metrics.minLatency = Math.min(...this.responseHistory.map(r => r.latency));
      this.metrics.maxLatency = Math.max(...this.responseHistory.map(r => r.latency));
    }

    // Calculate per-minute rates
    const oneMinuteAgo = new Date(now.getTime() - 60000);
    const lastMinuteResponses = this.responseHistory.filter(r => r.timestamp >= oneMinuteAgo);
    this.metrics.responsesPerMinute = lastMinuteResponses.length;
    this.metrics.apiUsage = this.metrics.responsesPerMinute; // Simplified

    // Calculate agent stats
    const activeAgentIds = new Set(recentResponses.map(r => r.agentId));
    this.metrics.activeAgents = activeAgentIds.size;
    
    this.metrics.agentStats = {};
    activeAgentIds.forEach(agentId => {
      const agentResponses = this.responseHistory.filter(r => r.agentId === agentId);
      const recentAgentResponses = recentResponses.filter(r => r.agentId === agentId);
      const lastMinuteAgentResponses = lastMinuteResponses.filter(r => r.agentId === agentId);
      
      if (agentResponses.length > 0) {
        const flaggedCount = agentResponses.filter(r => r.flagged).length;
        const avgRisk = agentResponses.reduce((sum, r) => sum + r.riskScore, 0) / agentResponses.length;
        const avgLatency = agentResponses.reduce((sum, r) => sum + r.latency, 0) / agentResponses.length;
        
        // Calculate trend
        const oldResponses = agentResponses.filter(r => r.timestamp < cutoffTime);
        const oldAvgRisk = oldResponses.length > 0 ? 
          oldResponses.reduce((sum, r) => sum + r.riskScore, 0) / oldResponses.length : avgRisk;
        
        let trend: 'improving' | 'stable' | 'degrading' = 'stable';
        const riskDiff = avgRisk - oldAvgRisk;
        if (Math.abs(riskDiff) > 0.1) {
          trend = riskDiff > 0 ? 'degrading' : 'improving';
        }

        this.metrics.agentStats[agentId] = {
          agentId,
          totalResponses: agentResponses.length,
          flaggedResponses: flaggedCount,
          flaggedRate: flaggedCount / agentResponses.length,
          averageRiskScore: avgRisk,
          averageLatency: avgLatency,
          lastResponseTime: agentResponses[agentResponses.length - 1].timestamp,
          isActive: recentAgentResponses.length > 0,
          responsesPerMinute: lastMinuteAgentResponses.length,
          trend
        };
      }
    });

    // Calculate trends
    this.updateTrends(recentResponses);

    // Calculate system health (simplified scoring)
    this.metrics.systemHealth = this.calculateSystemHealth();
    this.metrics.connectionQuality = this.calculateConnectionQuality();

    // Update session duration
    this.metrics.sessionDuration = Math.floor((now.getTime() - this.metrics.sessionStartTime.getTime()) / 1000);
    this.metrics.lastUpdateTime = now;

    // Notify listeners
    this.notifyListeners();
  }

  private updateTrends(recentResponses: typeof this.responseHistory) {
    const now = new Date();
    const bucketSize = 30000; // 30 seconds
    const numBuckets = Math.floor((this.settings.trendWindow * 60 * 1000) / bucketSize);
    
    // Initialize trend arrays
    this.metrics.responseTrend = Array(numBuckets).fill(0);
    this.metrics.riskTrend = Array(numBuckets).fill(0);
    this.metrics.latencyTrend = Array(numBuckets).fill(0);
    
    const bucketCounts = Array(numBuckets).fill(0);

    recentResponses.forEach(response => {
      const timeDiff = now.getTime() - response.timestamp.getTime();
      const bucketIndex = Math.floor(timeDiff / bucketSize);
      
      if (bucketIndex >= 0 && bucketIndex < numBuckets) {
        const idx = numBuckets - 1 - bucketIndex; // Reverse for chronological order
        this.metrics.responseTrend[idx]++;
        this.metrics.riskTrend[idx] += response.riskScore;
        this.metrics.latencyTrend[idx] += response.latency;
        bucketCounts[idx]++;
      }
    });

    // Calculate averages for risk and latency trends
    for (let i = 0; i < numBuckets; i++) {
      if (bucketCounts[i] > 0) {
        this.metrics.riskTrend[i] /= bucketCounts[i];
        this.metrics.latencyTrend[i] /= bucketCounts[i];
      }
    }
  }

  private calculateSystemHealth(): number {
    let health = 100;
    
    // Penalize high error rates
    health -= this.metrics.errorRate * 50;
    
    // Penalize high flagged rates
    if (this.metrics.flaggedRate > 0.5) health -= 20;
    else if (this.metrics.flaggedRate > 0.3) health -= 10;
    
    // Penalize high latency
    if (this.metrics.averageLatency > 5000) health -= 20;
    else if (this.metrics.averageLatency > 2000) health -= 10;
    
    // Penalize inactive agents
    if (this.metrics.activeAgents === 0) health -= 30;
    
    return Math.max(0, Math.min(100, health));
  }

  private calculateConnectionQuality(): number {
    // Simplified connection quality based on latency and error rate
    let quality = 100;
    
    quality -= this.metrics.errorRate * 60;
    quality -= Math.min(30, this.metrics.averageLatency / 100);
    
    return Math.max(0, Math.min(100, quality));
  }

  private notifyListeners() {
    if (!this.settings.enabled) return;
    
    this.listeners.forEach(listener => {
      try {
        listener({ ...this.metrics });
      } catch (error) {
        console.error('Error in stats listener:', error);
      }
    });
  }

  public addResponse(data: {
    agentId: string;
    riskScore: number;
    latency: number;
    flagged: boolean;
    timestamp?: Date;
  }) {
    const response = {
      timestamp: data.timestamp || new Date(),
      riskScore: data.riskScore,
      latency: data.latency,
      agentId: data.agentId,
      flagged: data.flagged
    };

    this.responseHistory.push(response);
    
    // Trim history to prevent memory issues
    if (this.responseHistory.length > this.maxHistorySize) {
      this.responseHistory = this.responseHistory.slice(-this.maxHistorySize);
    }

    // Immediate update for responsiveness
    this.updateMetrics();
  }

  public recordError() {
    const recentErrors = this.responseHistory.filter(r => 
      new Date().getTime() - r.timestamp.getTime() < 60000
    ).length;
    
    this.metrics.errorRate = Math.min(1, recentErrors / Math.max(1, this.metrics.responsesPerMinute));
  }

  public subscribe(listener: (metrics: SystemMetrics) => void): () => void {
    this.listeners.add(listener);
    // Immediately call with current metrics
    listener({ ...this.metrics });
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  public updateSettings(newSettings: Partial<StatsSettings>) {
    this.settings = { ...this.settings, ...newSettings };
    this.saveSettings();
    
    // Restart timer if interval changed
    if (newSettings.updateInterval !== undefined) {
      this.startUpdateTimer();
    }
  }

  public getSettings(): StatsSettings {
    return { ...this.settings };
  }

  public getMetrics(): SystemMetrics {
    return { ...this.metrics };
  }

  public reset() {
    this.responseHistory = [];
    this.metrics = this.initializeMetrics();
    this.notifyListeners();
  }

  public cleanup() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }
  }
}

// Global instance
export const realtimeStats = new RealtimeStatsManager();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    realtimeStats.cleanup();
  });
}
