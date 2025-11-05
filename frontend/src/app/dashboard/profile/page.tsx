'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RefreshCw, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import Header from '@/components/dashboard/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [tokenError, setTokenError] = useState<string>('');
  const [copied, setCopied] = useState(false);

  // Password change state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);

  useEffect(() => {
    fetchToken();
  }, []);

  const fetchToken = async () => {
    setLoading(true);
    setTokenError('');
    try {
      const response = await api.getToken();
      setToken(response?.data?.token || '');
    } catch (error) {
      setTokenError('Failed to load token');
      toast.error('Failed to load API token');
    } finally {
      setLoading(false);
    }
  };

  const rotateToken = async () => {
    setRotating(true);
    setTokenError('');
    try {
      const response = await api.rotateToken();
      const tokenValue = response?.data?.token || null;
      if (!tokenValue) {
        setTokenError('Token not found in response');
        toast.error('Token not found in response');
      } else {
        setToken(tokenValue);
        toast.success('API token rotated successfully');
      }
    } catch (error) {
      toast.error('Failed to rotate API token');
    } finally {
      setRotating(false);
    }
  };

  const copyToken = async () => {
    if (!token || tokenError) {
      toast.error('No token to copy');
      return;
    }
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
      toast.success('Token copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy token');
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');

    // Validation
    if (!oldPassword || !newPassword || !confirmPassword) {
      setPasswordError('All fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters');
      return;
    }

    setPasswordLoading(true);

    try {
      const response = await api.changePassword(oldPassword, newPassword);

      if (response.error) {
        setPasswordError(response.error);
        toast.error(response.error);
        return;
      }

      toast.success('Password changed successfully');
      // Clear form
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      const message = 'Failed to change password: ' + (error instanceof Error ? error.message : String(error));
      setPasswordError(message);
      toast.error(message);
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <Header title="Profile" subtitle="Manage your account settings here." />

      {/* API Token Section */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Label className="text-xl font-semibold" htmlFor="api-token">
              API Token
            </Label>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              id="api-token"
              type="text"
              value={loading ? 'Loading...' : token || (tokenError ? 'Error loading token' : '')}
              readOnly
              className={`font-mono ${tokenError ? 'border-red-500 text-red-500' : ''}`}
            />
            <Button
              onClick={copyToken}
              disabled={loading || !token || !!tokenError}
              variant="outline"
              size="icon"
              title="Copy token"
            >
              {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
            <Button
              onClick={rotateToken}
              disabled={rotating || loading}
              variant="outline"
              size="icon"
              title="Rotate token"
            >
              <RefreshCw className={`h-4 w-4 ${rotating ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          {tokenError && <p className="text-sm font-medium text-red-500">⚠️ {tokenError}</p>}
          <p className="text-muted-foreground text-sm">
            Use this token to authenticate API requests. Click the rotate button to generate a new token.
          </p>
        </CardContent>
      </Card>

      {/* Password Change Section */}
      <Card>
        <CardHeader>
          <CardTitle>
            <h2 className="mb-4 text-xl font-semibold">Change Password</h2>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordChange} className="space-y-4">
            {passwordError && (
              <div className="bg-destructive/15 text-destructive rounded-md p-3 text-sm">{passwordError}</div>
            )}

            <div className="space-y-2">
              <Label htmlFor="old-password">Current Password</Label>
              <Input
                id="old-password"
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                disabled={passwordLoading}
                placeholder="Enter your current password"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={passwordLoading}
                placeholder="Enter new password (min 8 characters)"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-new-password">Confirm New Password</Label>
              <Input
                id="confirm-new-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={passwordLoading}
                placeholder="Confirm new password"
              />
            </div>

            <Button type="submit" disabled={passwordLoading}>
              {passwordLoading ? 'Changing Password...' : 'Change Password'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
