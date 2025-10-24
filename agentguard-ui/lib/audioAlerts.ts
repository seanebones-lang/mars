/**
 * Watcher-AI Audio Alert System
 * Professional enterprise-grade audio notifications for hallucination detection
 */

export type AlertLevel = 'low' | 'medium' | 'high' | 'critical';
export type AlertType = 'detection' | 'system' | 'connection' | 'success';

export interface AudioSettings {
  enabled: boolean;
  volume: number; // 0-1
  alertCooldown: number; // seconds
  riskThresholds: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  soundProfile: 'professional' | 'subtle' | 'urgent';
}

export interface AlertSound {
  level: AlertLevel;
  type: AlertType;
  frequency: number;
  duration: number;
  pattern: 'single' | 'double' | 'triple' | 'pulse';
}

class AudioAlertManager {
  private audioContext: AudioContext | null = null;
  private settings: AudioSettings;
  private lastAlertTime: Map<string, number> = new Map();
  private isInitialized = false;

  constructor() {
    this.settings = this.getDefaultSettings();
    this.initializeAudio();
  }

  private getDefaultSettings(): AudioSettings {
    const defaultSettings = {
      enabled: true,
      volume: 0.3,
      alertCooldown: 2, // 2 seconds between similar alerts
      riskThresholds: {
        low: 0.3,
        medium: 0.5,
        high: 0.7,
        critical: 0.85
      },
      soundProfile: 'professional' as const
    };

    if (typeof window === 'undefined') {
      return defaultSettings;
    }

    const saved = localStorage.getItem('watcher-audio-settings');
    if (saved) {
      try {
        return { ...defaultSettings, ...JSON.parse(saved) };
      } catch (error) {
        console.warn('Failed to parse saved audio settings:', error);
      }
    }

    return defaultSettings;
  }

  private async initializeAudio() {
    if (typeof window === 'undefined') return;

    try {
      // Request user permission for audio
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // Resume context if suspended (required by browser policies)
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }
      
      this.isInitialized = true;
      console.log('Audio Alert System initialized');
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
    }
  }

  public async enableAudio() {
    if (!this.audioContext || this.audioContext.state === 'suspended') {
      await this.initializeAudio();
    }
  }

  private getSoundConfig(level: AlertLevel, type: AlertType): AlertSound {
    const configs = {
      professional: {
        low: { frequency: 800, duration: 0.2, pattern: 'single' as const },
        medium: { frequency: 1000, duration: 0.3, pattern: 'double' as const },
        high: { frequency: 1200, duration: 0.4, pattern: 'triple' as const },
        critical: { frequency: 1400, duration: 0.6, pattern: 'pulse' as const }
      },
      subtle: {
        low: { frequency: 600, duration: 0.15, pattern: 'single' as const },
        medium: { frequency: 750, duration: 0.25, pattern: 'single' as const },
        high: { frequency: 900, duration: 0.35, pattern: 'double' as const },
        critical: { frequency: 1100, duration: 0.5, pattern: 'triple' as const }
      },
      urgent: {
        low: { frequency: 1000, duration: 0.3, pattern: 'double' as const },
        medium: { frequency: 1300, duration: 0.4, pattern: 'triple' as const },
        high: { frequency: 1600, duration: 0.5, pattern: 'pulse' as const },
        critical: { frequency: 2000, duration: 0.8, pattern: 'pulse' as const }
      }
    };

    const config = configs[this.settings.soundProfile][level];
    return {
      level,
      type,
      ...config
    };
  }

  private async playTone(frequency: number, duration: number, volume: number = 1) {
    if (!this.audioContext || !this.isInitialized) {
      await this.enableAudio();
      if (!this.audioContext) return;
    }

    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    // Configure oscillator
    oscillator.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
    oscillator.type = 'sine';

    // Configure volume envelope
    const now = this.audioContext.currentTime;
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(volume * this.settings.volume, now + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + duration);

    // Play the tone
    oscillator.start(now);
    oscillator.stop(now + duration);
  }

  private async playPattern(sound: AlertSound) {
    const { frequency, duration, pattern } = sound;
    const baseVolume = this.getVolumeForLevel(sound.level);

    switch (pattern) {
      case 'single':
        await this.playTone(frequency, duration, baseVolume);
        break;

      case 'double':
        await this.playTone(frequency, duration * 0.6, baseVolume);
        await new Promise(resolve => setTimeout(resolve, 100));
        await this.playTone(frequency, duration * 0.6, baseVolume);
        break;

      case 'triple':
        for (let i = 0; i < 3; i++) {
          await this.playTone(frequency, duration * 0.4, baseVolume);
          if (i < 2) await new Promise(resolve => setTimeout(resolve, 80));
        }
        break;

      case 'pulse':
        for (let i = 0; i < 5; i++) {
          await this.playTone(frequency + (i * 50), duration * 0.2, baseVolume * (1 - i * 0.1));
          await new Promise(resolve => setTimeout(resolve, 50));
        }
        break;
    }
  }

  private getVolumeForLevel(level: AlertLevel): number {
    const volumes = {
      low: 0.4,
      medium: 0.6,
      high: 0.8,
      critical: 1.0
    };
    return volumes[level];
  }

  private shouldPlayAlert(alertKey: string): boolean {
    if (!this.settings.enabled) return false;

    const now = Date.now();
    const lastAlert = this.lastAlertTime.get(alertKey);
    
    if (lastAlert && (now - lastAlert) < (this.settings.alertCooldown * 1000)) {
      return false; // Still in cooldown period
    }

    this.lastAlertTime.set(alertKey, now);
    return true;
  }

  public getRiskLevel(riskScore: number): AlertLevel {
    const { riskThresholds } = this.settings;
    
    if (riskScore >= riskThresholds.critical) return 'critical';
    if (riskScore >= riskThresholds.high) return 'high';
    if (riskScore >= riskThresholds.medium) return 'medium';
    return 'low';
  }

  public async playHallucinationAlert(agentId: string, riskScore: number, segments: string[] = []) {
    const level = this.getRiskLevel(riskScore);
    const alertKey = `hallucination-${agentId}-${level}`;

    if (!this.shouldPlayAlert(alertKey)) return;

    const sound = this.getSoundConfig(level, 'detection');
    
    try {
      await this.playPattern(sound);
      
      // Log alert for debugging
      console.log(`🔊 Audio Alert: ${level.toUpperCase()} risk detected for ${agentId} (${(riskScore * 100).toFixed(1)}%)`);
      
      // Show visual feedback
      this.showAudioFeedback(level, `${agentId}: ${segments.join(', ')}`);
    } catch (error) {
      console.error('Failed to play hallucination alert:', error);
    }
  }

  public async playSystemAlert(type: 'connection_lost' | 'connection_restored' | 'monitoring_started' | 'monitoring_stopped') {
    const alertKey = `system-${type}`;
    if (!this.shouldPlayAlert(alertKey)) return;

    const configs = {
      connection_lost: { level: 'high' as AlertLevel, frequency: 400, duration: 0.8 },
      connection_restored: { level: 'low' as AlertLevel, frequency: 800, duration: 0.4 },
      monitoring_started: { level: 'medium' as AlertLevel, frequency: 1000, duration: 0.3 },
      monitoring_stopped: { level: 'medium' as AlertLevel, frequency: 600, duration: 0.5 }
    };

    const config = configs[type];
    const sound = this.getSoundConfig(config.level, 'system');
    
    try {
      await this.playPattern(sound);
      console.log(`🔊 System Alert: ${type.replace('_', ' ')}`);
    } catch (error) {
      console.error('Failed to play system alert:', error);
    }
  }

  private showAudioFeedback(level: AlertLevel, message: string) {
    // Create temporary visual indicator
    const indicator = document.createElement('div');
    indicator.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: ${level === 'critical' ? '#f44336' : level === 'high' ? '#ff9800' : level === 'medium' ? '#ff9800' : '#4caf50'};
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 14px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      animation: slideIn 0.3s ease-out;
      max-width: 300px;
      word-wrap: break-word;
    `;
    
    indicator.innerHTML = `🔊 ${level.toUpperCase()}: ${message}`;
    document.body.appendChild(indicator);

    // Remove after 3 seconds
    setTimeout(() => {
      if (indicator.parentNode) {
        indicator.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => indicator.remove(), 300);
      }
    }, 3000);
  }

  // Settings management
  public updateSettings(newSettings: Partial<AudioSettings>) {
    this.settings = { ...this.settings, ...newSettings };
    if (typeof window !== 'undefined') {
      localStorage.setItem('watcher-audio-settings', JSON.stringify(this.settings));
    }
  }

  public getSettings(): AudioSettings {
    return { ...this.settings };
  }

  public setEnabled(enabled: boolean) {
    this.updateSettings({ enabled });
  }

  public setVolume(volume: number) {
    this.updateSettings({ volume: Math.max(0, Math.min(1, volume)) });
  }

  public setSoundProfile(profile: AudioSettings['soundProfile']) {
    this.updateSettings({ soundProfile: profile });
  }

  // Test methods for settings UI
  public async testAlert(level: AlertLevel) {
    const sound = this.getSoundConfig(level, 'detection');
    await this.playPattern(sound);
    this.showAudioFeedback(level, `Test ${level} alert`);
  }
}

// Global instance
export const audioAlerts = new AudioAlertManager();

// Add CSS for animations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
}
