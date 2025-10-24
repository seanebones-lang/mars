'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Alert,
  AlertDescription,
  Progress,
  Switch,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { 
  User, 
  Shield, 
  Key, 
  Settings, 
  CreditCard, 
  Activity,
  Bell,
  Lock,
  Trash2,
  Plus,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react';

interface UserProfile {
  user_id: string;
  email: string;
  full_name: string;
  role: 'free' | 'pro' | 'enterprise' | 'admin';
  created_at: string;
  last_login: string;
  mfa_enabled: boolean;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    notifications: boolean;
    email_alerts: boolean;
    language: string;
  };
}

interface UsageStats {
  queries_this_month: number;
  queries_total: number;
  agents_created: number;
  api_calls_this_month: number;
  last_activity: string;
  plan_limits: {
    queries_per_month: number;
    agents: number;
    api_calls: number;
  };
}

interface ApiToken {
  id: string;
  name: string;
  created: string;
  last_used: string;
}

export default function UserProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [apiTokens, setApiTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showMfaSetup, setShowMfaSetup] = useState(false);
  const [showTokenDialog, setShowTokenDialog] = useState(false);
  const [newTokenName, setNewTokenName] = useState('');
  const [newToken, setNewToken] = useState('');
  const [showToken, setShowToken] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await fetch('/api/auth/profile', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setProfile(data.user);
        setUsageStats(data.usage_stats);
        setApiTokens(data.api_tokens);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async (updates: Partial<UserProfile>) => {
    setSaving(true);
    try {
      const response = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        await loadProfile();
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const setupMfa = async () => {
    try {
      const response = await fetch('/api/auth/mfa/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ method: 'totp' })
      });

      if (response.ok) {
        const data = await response.json();
        // Handle MFA setup response (QR code, secret, etc.)
        setShowMfaSetup(true);
      }
    } catch (error) {
      console.error('Failed to setup MFA:', error);
    }
  };

  const generateApiToken = async () => {
    if (!newTokenName.trim()) return;

    try {
      const response = await fetch('/api/auth/api-tokens', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({ token_name: newTokenName })
      });

      if (response.ok) {
        const data = await response.json();
        setNewToken(data.token);
        setNewTokenName('');
        await loadProfile();
      }
    } catch (error) {
      console.error('Failed to generate API token:', error);
    }
  };

  const revokeApiToken = async (tokenId: string) => {
    try {
      const response = await fetch(`/api/auth/api-tokens/${tokenId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        await loadProfile();
      }
    } catch (error) {
      console.error('Failed to revoke API token:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert>
          <AlertDescription>Failed to load user profile</AlertDescription>
        </Alert>
      </div>
    );
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-red-100 text-red-800';
      case 'enterprise': return 'bg-purple-100 text-purple-800';
      case 'pro': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getUsagePercentage = (used: number, limit: number) => {
    return Math.min((used / limit) * 100, 100);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">User Profile</h1>
        <p className="text-gray-600 mt-2">Manage your account settings and preferences</p>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Security
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Access
          </TabsTrigger>
          <TabsTrigger value="usage" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Usage
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Profile Information
                <Badge className={getRoleColor(profile.role)}>
                  {profile.role.toUpperCase()}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    value={profile.email}
                    disabled
                    className="bg-gray-50"
                  />
                </div>
                <div>
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input
                    id="fullName"
                    value={profile.full_name}
                    onChange={(e) => setProfile({...profile, full_name: e.target.value})}
                  />
                </div>
                <div>
                  <Label htmlFor="created">Member Since</Label>
                  <Input
                    id="created"
                    value={new Date(profile.created_at).toLocaleDateString()}
                    disabled
                    className="bg-gray-50"
                  />
                </div>
                <div>
                  <Label htmlFor="lastLogin">Last Login</Label>
                  <Input
                    id="lastLogin"
                    value={new Date(profile.last_login).toLocaleString()}
                    disabled
                    className="bg-gray-50"
                  />
                </div>
              </div>
              <Button 
                onClick={() => updateProfile({ full_name: profile.full_name })}
                disabled={saving}
                className="w-full md:w-auto"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Security Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Lock className="h-5 w-5 text-gray-600" />
                  <div>
                    <h3 className="font-medium">Two-Factor Authentication</h3>
                    <p className="text-sm text-gray-600">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {profile.mfa_enabled ? (
                    <Badge className="bg-green-100 text-green-800">Enabled</Badge>
                  ) : (
                    <Badge className="bg-yellow-100 text-yellow-800">Disabled</Badge>
                  )}
                  <Button
                    variant={profile.mfa_enabled ? "outline" : "default"}
                    onClick={setupMfa}
                  >
                    {profile.mfa_enabled ? 'Manage' : 'Enable'}
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Key className="h-5 w-5 text-gray-600" />
                  <div>
                    <h3 className="font-medium">Password</h3>
                    <p className="text-sm text-gray-600">
                      Change your account password
                    </p>
                  </div>
                </div>
                <Button variant="outline">
                  Change Password
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                API Tokens
                <Dialog open={showTokenDialog} onOpenChange={setShowTokenDialog}>
                  <DialogTrigger asChild>
                    <Button className="flex items-center gap-2">
                      <Plus className="h-4 w-4" />
                      Generate Token
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Generate API Token</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="tokenName">Token Name</Label>
                        <Input
                          id="tokenName"
                          placeholder="e.g., Production API"
                          value={newTokenName}
                          onChange={(e) => setNewTokenName(e.target.value)}
                        />
                      </div>
                      {newToken && (
                        <div>
                          <Label>Your New Token</Label>
                          <div className="flex items-center gap-2 mt-1">
                            <Input
                              value={newToken}
                              type={showToken ? "text" : "password"}
                              readOnly
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setShowToken(!showToken)}
                            >
                              {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(newToken)}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                          <p className="text-sm text-yellow-600 mt-1">
                            Save this token now. You won't be able to see it again.
                          </p>
                        </div>
                      )}
                      <Button 
                        onClick={generateApiToken}
                        disabled={!newTokenName.trim()}
                        className="w-full"
                      >
                        Generate Token
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {profile.role === 'free' ? (
                <Alert>
                  <AlertDescription>
                    API access is available for Pro and Enterprise plans only.
                    <Button variant="link" className="p-0 h-auto ml-1">
                      Upgrade your plan
                    </Button>
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-3">
                  {apiTokens.length === 0 ? (
                    <p className="text-gray-600">No API tokens created yet.</p>
                  ) : (
                    apiTokens.map((token) => (
                      <div key={token.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <h4 className="font-medium">{token.name}</h4>
                          <p className="text-sm text-gray-600">
                            Created: {new Date(token.created).toLocaleDateString()} • 
                            Last used: {new Date(token.last_used).toLocaleDateString()}
                          </p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => revokeApiToken(token.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          {usageStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Queries This Month</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{usageStats.queries_this_month}</span>
                      <span>{usageStats.plan_limits.queries_per_month}</span>
                    </div>
                    <Progress 
                      value={getUsagePercentage(usageStats.queries_this_month, usageStats.plan_limits.queries_per_month)}
                      className="h-2"
                    />
                    <p className="text-xs text-gray-600">
                      {Math.round(getUsagePercentage(usageStats.queries_this_month, usageStats.plan_limits.queries_per_month))}% used
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">API Calls</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{usageStats.api_calls_this_month}</span>
                      <span>{usageStats.plan_limits.api_calls}</span>
                    </div>
                    <Progress 
                      value={getUsagePercentage(usageStats.api_calls_this_month, usageStats.plan_limits.api_calls)}
                      className="h-2"
                    />
                    <p className="text-xs text-gray-600">
                      {Math.round(getUsagePercentage(usageStats.api_calls_this_month, usageStats.plan_limits.api_calls))}% used
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Agents Created</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{usageStats.agents_created}</span>
                      <span>{usageStats.plan_limits.agents}</span>
                    </div>
                    <Progress 
                      value={getUsagePercentage(usageStats.agents_created, usageStats.plan_limits.agents)}
                      className="h-2"
                    />
                    <p className="text-xs text-gray-600">
                      {Math.round(getUsagePercentage(usageStats.agents_created, usageStats.plan_limits.agents))}% used
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Total Queries</Label>
                  <p className="text-2xl font-bold text-blue-600">{usageStats?.queries_total}</p>
                </div>
                <div>
                  <Label>Last Activity</Label>
                  <p className="text-lg">{usageStats ? new Date(usageStats.last_activity).toLocaleString() : 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Theme</Label>
                  <p className="text-sm text-gray-600">Choose your preferred theme</p>
                </div>
                <Select
                  value={profile.preferences.theme}
                  onValueChange={(value) => updateProfile({
                    preferences: { ...profile.preferences, theme: value as any }
                  })}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-gray-600">Receive email alerts for important events</p>
                </div>
                <Switch
                  checked={profile.preferences.email_alerts}
                  onCheckedChange={(checked) => updateProfile({
                    preferences: { ...profile.preferences, email_alerts: checked }
                  })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Push Notifications</Label>
                  <p className="text-sm text-gray-600">Receive browser notifications</p>
                </div>
                <Switch
                  checked={profile.preferences.notifications}
                  onCheckedChange={(checked) => updateProfile({
                    preferences: { ...profile.preferences, notifications: checked }
                  })}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
