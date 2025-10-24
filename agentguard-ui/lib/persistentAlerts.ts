/**
 * Watcher-AI Persistent Alert System
 * Enterprise-grade persistent notifications that stay visible until acknowledged
 */

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertCategory = 'hallucination' | 'system' | 'connection' | 'performance';

export interface PersistentAlert {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  category: AlertCategory;
  timestamp: Date;
  agentId?: string;
  riskScore?: number;
  flaggedSegments?: string[];
  mitigation?: string;
  acknowledged: boolean;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
  autoEscalateAt?: Date;
  escalated: boolean;
  metadata?: Record<string, any>;
}

export interface AlertSettings {
  enabled: boolean;
  maxVisibleAlerts: number;
  autoEscalateTimeout: number; // minutes
  persistentCategories: AlertCategory[];
  minimumSeverity: AlertSeverity;
  showOnAllPages: boolean;
  playAudioOnNew: boolean;
  blinkOnCritical: boolean;
}

class PersistentAlertManager {
  private alerts: Map<string, PersistentAlert> = new Map();
  private settings: AlertSettings;
  private listeners: Set<(alerts: PersistentAlert[]) => void> = new Set();
  private escalationTimer: NodeJS.Timeout | null = null;

  constructor() {
    this.settings = this.getDefaultSettings();
    this.startEscalationTimer();
    this.loadPersistedAlerts();
  }

  private getDefaultSettings(): AlertSettings {
    const defaultSettings = {
      enabled: true,
      maxVisibleAlerts: 5,
      autoEscalateTimeout: 5, // 5 minutes
      persistentCategories: ['hallucination', 'system'] as AlertCategory[],
      minimumSeverity: 'medium' as AlertSeverity,
      showOnAllPages: true,
      playAudioOnNew: true,
      blinkOnCritical: true
    };

    if (typeof window === 'undefined') {
      return defaultSettings;
    }

    const saved = localStorage.getItem('watcher-alert-settings');
    if (saved) {
      try {
        return { ...defaultSettings, ...JSON.parse(saved) };
      } catch (error) {
        console.warn('Failed to parse saved alert settings:', error);
      }
    }

    return defaultSettings;
  }

  private saveSettings() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('watcher-alert-settings', JSON.stringify(this.settings));
    }
  }

  private saveAlerts() {
    if (typeof window !== 'undefined') {
      const alertsArray = Array.from(this.alerts.values()).map(alert => ({
        ...alert,
        timestamp: alert.timestamp.toISOString(),
        acknowledgedAt: alert.acknowledgedAt?.toISOString(),
        autoEscalateAt: alert.autoEscalateAt?.toISOString()
      }));
      localStorage.setItem('watcher-persistent-alerts', JSON.stringify(alertsArray));
    }
  }

  private loadPersistedAlerts() {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const saved = localStorage.getItem('watcher-persistent-alerts');
      if (saved) {
        const alertsArray = JSON.parse(saved);
        alertsArray.forEach((alertData: any) => {
          const alert: PersistentAlert = {
            ...alertData,
            timestamp: new Date(alertData.timestamp),
            acknowledgedAt: alertData.acknowledgedAt ? new Date(alertData.acknowledgedAt) : undefined,
            autoEscalateAt: alertData.autoEscalateAt ? new Date(alertData.autoEscalateAt) : undefined
          };
          
          // Only load unacknowledged alerts from the last 24 hours
          const isRecent = Date.now() - alert.timestamp.getTime() < 24 * 60 * 60 * 1000;
          if (!alert.acknowledged && isRecent) {
            this.alerts.set(alert.id, alert);
          }
        });
        this.notifyListeners();
      }
    } catch (error) {
      console.error('Failed to load persisted alerts:', error);
    }
  }

  private generateId(): string {
    return `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private getSeverityLevel(severity: AlertSeverity): number {
    const levels = { low: 1, medium: 2, high: 3, critical: 4 };
    return levels[severity];
  }

  private shouldPersistAlert(category: AlertCategory, severity: AlertSeverity): boolean {
    if (!this.settings.enabled) return false;
    if (!this.settings.persistentCategories.includes(category)) return false;
    return this.getSeverityLevel(severity) >= this.getSeverityLevel(this.settings.minimumSeverity);
  }

  private notifyListeners() {
    const alertsArray = this.getVisibleAlerts();
    this.listeners.forEach(listener => {
      try {
        listener(alertsArray);
      } catch (error) {
        console.error('Error in alert listener:', error);
      }
    });
  }

  private startEscalationTimer() {
    if (typeof window === 'undefined') {
      return;
    }

    if (this.escalationTimer) {
      clearInterval(this.escalationTimer);
    }

    // Check for escalations every minute
    this.escalationTimer = setInterval(() => {
      this.checkForEscalations();
    }, 60000);
  }

  private checkForEscalations() {
    const now = new Date();
    let hasEscalations = false;

    this.alerts.forEach(alert => {
      if (!alert.acknowledged && !alert.escalated && alert.autoEscalateAt && now >= alert.autoEscalateAt) {
        alert.escalated = true;
        alert.severity = alert.severity === 'critical' ? 'critical' : 
                        alert.severity === 'high' ? 'critical' :
                        alert.severity === 'medium' ? 'high' : 'medium';
        
        // Create escalation alert
        this.createAlert({
          title: `ESCALATED: ${alert.title}`,
          message: `Alert has been unacknowledged for ${this.settings.autoEscalateTimeout} minutes`,
          severity: 'critical',
          category: 'system',
          metadata: { originalAlertId: alert.id, escalatedFrom: alert.severity }
        });

        hasEscalations = true;
        console.warn(`Alert escalated: ${alert.id}`);
      }
    });

    if (hasEscalations) {
      this.saveAlerts();
      this.notifyListeners();
    }
  }

  public createAlert(params: {
    title: string;
    message: string;
    severity: AlertSeverity;
    category: AlertCategory;
    agentId?: string;
    riskScore?: number;
    flaggedSegments?: string[];
    mitigation?: string;
    metadata?: Record<string, any>;
  }): string | null {
    
    if (!this.shouldPersistAlert(params.category, params.severity)) {
      return null;
    }

    const id = this.generateId();
    const now = new Date();
    const autoEscalateAt = new Date(now.getTime() + this.settings.autoEscalateTimeout * 60000);

    const alert: PersistentAlert = {
      id,
      title: params.title,
      message: params.message,
      severity: params.severity,
      category: params.category,
      timestamp: now,
      agentId: params.agentId,
      riskScore: params.riskScore,
      flaggedSegments: params.flaggedSegments,
      mitigation: params.mitigation,
      acknowledged: false,
      autoEscalateAt: params.severity !== 'low' ? autoEscalateAt : undefined,
      escalated: false,
      metadata: params.metadata
    };

    this.alerts.set(id, alert);
    this.saveAlerts();
    this.notifyListeners();

    console.log(`Created persistent alert: ${params.severity.toUpperCase()} - ${params.title}`);
    return id;
  }

  public createHallucinationAlert(agentId: string, riskScore: number, segments: string[], mitigation?: string): string | null {
    const severity: AlertSeverity = 
      riskScore >= 0.85 ? 'critical' :
      riskScore >= 0.7 ? 'high' :
      riskScore >= 0.5 ? 'medium' : 'low';

    return this.createAlert({
      title: `Hallucination Detected: ${agentId}`,
      message: `Risk: ${(riskScore * 100).toFixed(1)}% - ${segments.join(', ')}`,
      severity,
      category: 'hallucination',
      agentId,
      riskScore,
      flaggedSegments: segments,
      mitigation,
      metadata: {
        detectionTime: new Date().toISOString(),
        agentType: agentId.replace('_', ' ').toUpperCase()
      }
    });
  }

  public acknowledgeAlert(id: string, acknowledgedBy?: string): boolean {
    const alert = this.alerts.get(id);
    if (!alert || alert.acknowledged) {
      return false;
    }

    alert.acknowledged = true;
    alert.acknowledgedAt = new Date();
    alert.acknowledgedBy = acknowledgedBy || 'user';

    this.saveAlerts();
    this.notifyListeners();

    console.log(`Alert acknowledged: ${id} by ${alert.acknowledgedBy}`);
    return true;
  }

  public acknowledgeAll(acknowledgedBy?: string): number {
    let count = 0;
    this.alerts.forEach(alert => {
      if (!alert.acknowledged) {
        alert.acknowledged = true;
        alert.acknowledgedAt = new Date();
        alert.acknowledgedBy = acknowledgedBy || 'user';
        count++;
      }
    });

    if (count > 0) {
      this.saveAlerts();
      this.notifyListeners();
      console.log(`Acknowledged ${count} alerts`);
    }

    return count;
  }

  public dismissAlert(id: string): boolean {
    const deleted = this.alerts.delete(id);
    if (deleted) {
      this.saveAlerts();
      this.notifyListeners();
      console.log(`Alert dismissed: ${id}`);
    }
    return deleted;
  }

  public getVisibleAlerts(): PersistentAlert[] {
    const unacknowledged = Array.from(this.alerts.values())
      .filter(alert => !alert.acknowledged)
      .sort((a, b) => {
        // Sort by severity (critical first), then by timestamp (newest first)
        const severityDiff = this.getSeverityLevel(b.severity) - this.getSeverityLevel(a.severity);
        if (severityDiff !== 0) return severityDiff;
        return b.timestamp.getTime() - a.timestamp.getTime();
      });

    return unacknowledged.slice(0, this.settings.maxVisibleAlerts);
  }

  public getAllAlerts(): PersistentAlert[] {
    return Array.from(this.alerts.values()).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  public getAlertStats() {
    const all = Array.from(this.alerts.values());
    const unacknowledged = all.filter(a => !a.acknowledged);
    const critical = unacknowledged.filter(a => a.severity === 'critical');
    const escalated = all.filter(a => a.escalated);

    return {
      total: all.length,
      unacknowledged: unacknowledged.length,
      critical: critical.length,
      escalated: escalated.length,
      oldestUnacknowledged: unacknowledged.length > 0 ? 
        Math.min(...unacknowledged.map(a => a.timestamp.getTime())) : null
    };
  }

  public subscribe(listener: (alerts: PersistentAlert[]) => void): () => void {
    this.listeners.add(listener);
    // Immediately call with current alerts
    listener(this.getVisibleAlerts());
    
    return () => {
      this.listeners.delete(listener);
    };
  }

  public updateSettings(newSettings: Partial<AlertSettings>) {
    this.settings = { ...this.settings, ...newSettings };
    this.saveSettings();
    
    // Restart escalation timer if timeout changed
    if (newSettings.autoEscalateTimeout !== undefined) {
      this.startEscalationTimer();
    }
  }

  public getSettings(): AlertSettings {
    return { ...this.settings };
  }

  public clearAll(): void {
    this.alerts.clear();
    this.saveAlerts();
    this.notifyListeners();
    console.log('All alerts cleared');
  }

  public cleanup(): void {
    if (this.escalationTimer) {
      clearInterval(this.escalationTimer);
    }
  }
}

// Global instance
export const persistentAlerts = new PersistentAlertManager();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    persistentAlerts.cleanup();
  });
}
