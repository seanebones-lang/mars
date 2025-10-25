/**
 * Workspace API Client
 * Handles all API calls to the workspace backend
 */

import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Project {
  project_id: string;
  name: string;
  description: string;
  status: string;
  tags: string[];
  test_count: number;
  agent_count: number;
  created_at: string;
  updated_at: string;
}

interface ProjectCreate {
  name: string;
  description?: string;
  tags?: string[];
  settings?: Record<string, any>;
}

interface Favorite {
  favorite_id: string;
  user_id: string;
  item_type: string;
  item_id: string;
  item_name: string;
  item_metadata: Record<string, any>;
  created_at: string;
}

interface FavoriteCreate {
  item_type: string;
  item_id: string;
  item_name: string;
  item_metadata?: Record<string, any>;
}

interface WorkspaceSetting {
  setting_id: string;
  user_id: string;
  key: string;
  value: any;
  category: string;
  created_at: string;
  updated_at: string;
}

interface APIKey {
  key_id: string;
  user_id: string;
  name: string;
  description?: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  last_used_at?: string;
  expires_at?: string;
  created_at: string;
}

interface APIKeyCreate {
  name: string;
  description?: string;
  scopes?: string[];
  expires_at?: string;
}

interface APIKeyResponse {
  key_id: string;
  name: string;
  api_key: string;
  key_prefix: string;
  scopes: string[];
  created_at: string;
  expires_at?: string;
}

interface DashboardStats {
  total_projects: number;
  total_tests: number;
  total_agents: number;
  total_favorites: number;
  queries_this_month: number;
  queries_limit: number;
  avg_accuracy: number;
  avg_latency_ms: number;
  last_test_at?: string;
}

interface RecentActivity {
  activity_id: string;
  activity_type: string;
  title: string;
  description?: string;
  metadata: Record<string, any>;
  created_at: string;
}

interface UserWorkspace {
  user_id: string;
  email: string;
  subscription_tier: string;
  stats: DashboardStats;
  recent_activity: RecentActivity[];
  active_projects: Project[];
  favorites: Favorite[];
  api_keys: APIKey[];
}

class WorkspaceAPIClient {
  private client: AxiosInstance;
  private apiKey: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/workspace`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use((config) => {
      const token = this.getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('agentguard_token');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('agentguard_token');
  }

  setAuthToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('agentguard_token', token);
    }
    this.apiKey = token;
  }

  clearAuthToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('agentguard_token');
    }
    this.apiKey = null;
  }

  // Workspace Overview
  async getWorkspace(): Promise<UserWorkspace> {
    const response = await this.client.get('/');
    return response.data;
  }

  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get('/stats');
    return response.data;
  }

  async getRecentActivity(limit: number = 10): Promise<RecentActivity[]> {
    const response = await this.client.get('/activity', { params: { limit } });
    return response.data;
  }

  // Projects
  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await this.client.post('/projects', data);
    return response.data;
  }

  async listProjects(status?: string): Promise<Project[]> {
    const response = await this.client.get('/projects', { params: { status } });
    return response.data;
  }

  async getProject(projectId: string): Promise<Project> {
    const response = await this.client.get(`/projects/${projectId}`);
    return response.data;
  }

  async updateProject(projectId: string, data: Partial<ProjectCreate>): Promise<Project> {
    const response = await this.client.patch(`/projects/${projectId}`, data);
    return response.data;
  }

  async deleteProject(projectId: string): Promise<void> {
    await this.client.delete(`/projects/${projectId}`);
  }

  // Favorites
  async addFavorite(data: FavoriteCreate): Promise<Favorite> {
    const response = await this.client.post('/favorites', data);
    return response.data;
  }

  async listFavorites(itemType?: string): Promise<Favorite[]> {
    const response = await this.client.get('/favorites', { params: { item_type: itemType } });
    return response.data;
  }

  async removeFavorite(favoriteId: string): Promise<void> {
    await this.client.delete(`/favorites/${favoriteId}`);
  }

  // Settings
  async setSetting(key: string, value: any, category: string = 'general'): Promise<WorkspaceSetting> {
    const response = await this.client.put('/settings', { key, value, category });
    return response.data;
  }

  async getSetting(key: string): Promise<WorkspaceSetting> {
    const response = await this.client.get(`/settings/${key}`);
    return response.data;
  }

  async listSettings(): Promise<WorkspaceSetting[]> {
    const response = await this.client.get('/settings');
    return response.data;
  }

  // API Keys
  async createAPIKey(data: APIKeyCreate): Promise<APIKeyResponse> {
    const response = await this.client.post('/api-keys', data);
    return response.data;
  }

  async listAPIKeys(): Promise<APIKey[]> {
    const response = await this.client.get('/api-keys');
    return response.data;
  }

  async revokeAPIKey(keyId: string): Promise<void> {
    await this.client.post(`/api-keys/${keyId}/revoke`);
  }

  async deleteAPIKey(keyId: string): Promise<void> {
    await this.client.delete(`/api-keys/${keyId}`);
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const workspaceAPI = new WorkspaceAPIClient();

// Export types
export type {
  Project,
  ProjectCreate,
  Favorite,
  FavoriteCreate,
  WorkspaceSetting,
  APIKey,
  APIKeyCreate,
  APIKeyResponse,
  DashboardStats,
  RecentActivity,
  UserWorkspace,
};

