'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RefreshCw, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

export default function SettingsPage() {
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [error, setError] = useState<string>('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchToken();
  }, []);

  const fetchToken = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.getToken();
      setToken(response?.data?.token || '');
    } catch (error) {
      toast.error('Failed to load API token');
    } finally {
      setLoading(false);
    }
  };

  const rotateToken = async () => {
    setRotating(true);
    setError('');
    try {
      const response = await api.rotateToken();
      const tokenValue = response?.data?.token || null;
      if (!tokenValue) {
        setError('Token not found in response');
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
    if (!token || error) {
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

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <h1 className="text-2xl font-bold">Account Settings</h1>
      <p className="text-muted-foreground">Manage your account settings here.</p>

      <div className="mt-6 max-w-2xl space-y-4">
        <div className="space-y-2">
          <Label htmlFor="api-token">API Token</Label>
          <div className="flex gap-2">
            <Input
              id="api-token"
              type="text"
              value={loading ? 'Loading...' : token || (error ? 'Error loading token' : '')}
              readOnly
              className={`font-mono ${error ? 'border-red-500 text-red-500' : ''}`}
            />
            <Button
              onClick={copyToken}
              disabled={loading || !token || !!error}
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
          {error && <p className="text-sm font-medium text-red-500">⚠️ {error}</p>}
          <p className="text-muted-foreground text-sm">
            Use this token to authenticate API requests. Click the rotate button to generate a new token.
          </p>
        </div>
      </div>
    </div>
  );
}
