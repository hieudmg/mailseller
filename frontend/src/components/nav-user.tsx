'use client';

import { LogOut } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import UserCredits from '@/components/user-credits';
import { CreditsProvider } from '@/context/CreditsContext';

export function NavUser({ email }: { email: string }) {
  const handleLogout = async () => {
    await api.logout();
    window.location.href = '/';
  };

  return (
    <CreditsProvider>
      <div className="flex items-center justify-between gap-4 px-2 py-2">
        <div className="flex items-center gap-4">
          <div className="truncate text-sm">
            <div>Welcome,</div>
            <div>{email}</div>
          </div>
          <UserCredits />
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleLogout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </CreditsProvider>
  );
}
