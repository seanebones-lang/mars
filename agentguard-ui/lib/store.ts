import { create } from 'zustand';

export interface TestResult {
  id: string;
  scenario_id?: string;
  category?: string;
  hallucination_risk: number;
  details: {
    claude_score: number;
    claude_explanation: string;
    hallucinated_segments: string[];
    statistical_score: number;
    needs_review: boolean;
    ensemble_weights?: {
      claude: number;
      statistical: number;
    };
  };
  confidence_interval: [number, number];
  uncertainty: number;
  timestamp: string;
  latency_seconds?: number;
}

export interface MetricsSummary {
  total_tests: number;
  avg_accuracy: number;
  avg_latency: number;
  high_risk_count: number;
  needs_review_count: number;
}

export interface RealtimeResult {
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

interface AgentGuardStore {
  // Test results
  results: TestResult[];
  addResult: (result: TestResult) => void;
  clearResults: () => void;
  
  // Real-time results
  realtimeResults: RealtimeResult[];
  addRealtimeResult: (result: RealtimeResult) => void;
  clearRealtimeResults: () => void;
  
  // Metrics
  metrics: MetricsSummary;
  updateMetrics: (metrics: Partial<MetricsSummary>) => void;
  
  // Settings
  apiUrl: string;
  setApiUrl: (url: string) => void;
  ensembleWeights: { claude: number; statistical: number };
  setEnsembleWeights: (weights: { claude: number; statistical: number }) => void;
  
  // UI State
  darkMode: boolean;
  toggleDarkMode: () => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const useStore = create<AgentGuardStore>((set) => ({
  // Test results
  results: [],
  addResult: (result) => set((state) => {
    const newResults = [{ ...result, id: `${Date.now()}-${Math.random()}` }, ...state.results];
    return { results: newResults };
  }),
  clearResults: () => set({ results: [] }),
  
  // Real-time results
  realtimeResults: [],
  addRealtimeResult: (result) => set((state) => ({
    realtimeResults: [...state.realtimeResults.slice(-99), result], // Keep last 100
  })),
  clearRealtimeResults: () => set({ realtimeResults: [] }),
  
  // Metrics
  metrics: {
    total_tests: 0,
    avg_accuracy: 0,
    avg_latency: 0,
    high_risk_count: 0,
    needs_review_count: 0,
  },
  updateMetrics: (metrics) => set((state) => ({
    metrics: { ...state.metrics, ...metrics }
  })),
  
  // Settings
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  setApiUrl: (url) => set({ apiUrl: url }),
  ensembleWeights: { claude: 0.6, statistical: 0.4 },
  setEnsembleWeights: (weights) => set({ ensembleWeights: weights }),
  
  // UI State
  darkMode: false,
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  loading: false,
  setLoading: (loading) => set({ loading }),
}));

