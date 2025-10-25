/**
 * React Hook for Workspace Data
 * Provides easy access to workspace API with caching and state management
 */

import { useState, useEffect, useCallback } from 'react';
import { workspaceAPI, UserWorkspace, Project, Favorite, APIKey, DashboardStats } from '@/lib/workspace-api';

interface UseWorkspaceReturn {
  workspace: UserWorkspace | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useWorkspace(): UseWorkspaceReturn {
  const [workspace, setWorkspace] = useState<UserWorkspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadWorkspace = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workspaceAPI.getWorkspace();
      setWorkspace(data);
    } catch (err) {
      setError(err as Error);
      console.error('Error loading workspace:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkspace();
  }, [loadWorkspace]);

  return {
    workspace,
    loading,
    error,
    refresh: loadWorkspace,
  };
}

interface UseProjectsReturn {
  projects: Project[];
  loading: boolean;
  error: Error | null;
  createProject: (data: { name: string; description?: string; tags?: string[] }) => Promise<Project>;
  updateProject: (id: string, data: Partial<Project>) => Promise<Project>;
  deleteProject: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useProjects(): UseProjectsReturn {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workspaceAPI.listProjects();
      setProjects(data);
    } catch (err) {
      setError(err as Error);
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const createProject = useCallback(async (data: { name: string; description?: string; tags?: string[] }) => {
    const project = await workspaceAPI.createProject(data);
    setProjects((prev) => [project, ...prev]);
    return project;
  }, []);

  const updateProject = useCallback(async (id: string, data: Partial<Project>) => {
    const updated = await workspaceAPI.updateProject(id, data);
    setProjects((prev) => prev.map((p) => (p.project_id === id ? updated : p)));
    return updated;
  }, []);

  const deleteProject = useCallback(async (id: string) => {
    await workspaceAPI.deleteProject(id);
    setProjects((prev) => prev.filter((p) => p.project_id !== id));
  }, []);

  return {
    projects,
    loading,
    error,
    createProject,
    updateProject,
    deleteProject,
    refresh: loadProjects,
  };
}

interface UseFavoritesReturn {
  favorites: Favorite[];
  loading: boolean;
  error: Error | null;
  addFavorite: (data: { item_type: string; item_id: string; item_name: string }) => Promise<Favorite>;
  removeFavorite: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useFavorites(): UseFavoritesReturn {
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadFavorites = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workspaceAPI.listFavorites();
      setFavorites(data);
    } catch (err) {
      setError(err as Error);
      console.error('Error loading favorites:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, [loadFavorites]);

  const addFavorite = useCallback(async (data: { item_type: string; item_id: string; item_name: string }) => {
    const favorite = await workspaceAPI.addFavorite(data);
    setFavorites((prev) => [favorite, ...prev]);
    return favorite;
  }, []);

  const removeFavorite = useCallback(async (id: string) => {
    await workspaceAPI.removeFavorite(id);
    setFavorites((prev) => prev.filter((f) => f.favorite_id !== id));
  }, []);

  return {
    favorites,
    loading,
    error,
    addFavorite,
    removeFavorite,
    refresh: loadFavorites,
  };
}

interface UseAPIKeysReturn {
  apiKeys: APIKey[];
  loading: boolean;
  error: Error | null;
  createAPIKey: (data: { name: string; description?: string }) => Promise<{ key: string; keyData: APIKey }>;
  revokeAPIKey: (id: string) => Promise<void>;
  deleteAPIKey: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useAPIKeys(): UseAPIKeysReturn {
  const [apiKeys, setAPIKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadAPIKeys = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workspaceAPI.listAPIKeys();
      setAPIKeys(data);
    } catch (err) {
      setError(err as Error);
      console.error('Error loading API keys:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAPIKeys();
  }, [loadAPIKeys]);

  const createAPIKey = useCallback(async (data: { name: string; description?: string }) => {
    const response = await workspaceAPI.createAPIKey(data);
    
    // Convert APIKeyResponse to APIKey format for state
    const keyData: APIKey = {
      key_id: response.key_id,
      user_id: '', // Will be filled by backend
      name: response.name,
      key_prefix: response.key_prefix,
      scopes: response.scopes,
      is_active: true,
      created_at: response.created_at,
      expires_at: response.expires_at,
    };
    
    setAPIKeys((prev) => [keyData, ...prev]);
    
    return { key: response.api_key, keyData };
  }, []);

  const revokeAPIKey = useCallback(async (id: string) => {
    await workspaceAPI.revokeAPIKey(id);
    setAPIKeys((prev) => prev.map((k) => (k.key_id === id ? { ...k, is_active: false } : k)));
  }, []);

  const deleteAPIKey = useCallback(async (id: string) => {
    await workspaceAPI.deleteAPIKey(id);
    setAPIKeys((prev) => prev.filter((k) => k.key_id !== id));
  }, []);

  return {
    apiKeys,
    loading,
    error,
    createAPIKey,
    revokeAPIKey,
    deleteAPIKey,
    refresh: loadAPIKeys,
  };
}

interface UseDashboardStatsReturn {
  stats: DashboardStats | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useDashboardStats(): UseDashboardStatsReturn {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workspaceAPI.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err as Error);
      console.error('Error loading stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return {
    stats,
    loading,
    error,
    refresh: loadStats,
  };
}

