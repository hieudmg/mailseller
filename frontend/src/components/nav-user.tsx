'use client';

import { LogOut } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { SidebarMenu, SidebarMenuItem } from '@/components/ui/sidebar';
import UserCredits from '@/components/user-credits';

export function NavUser({
  user,
}: {
  user: {
    name: string;
    email: string;
    avatar: string;
  };
}) {
  const handleLogout = async () => {
    await api.logout();
    window.location.href = '/';
  };

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <div className="flex items-center justify-between px-2 py-2">
          <div className="flex flex-col">
            <div className="truncate text-sm">{user.email}</div>
            <UserCredits />
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
