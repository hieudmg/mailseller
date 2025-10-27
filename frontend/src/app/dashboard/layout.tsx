'use client';

import React, { useEffect, Suspense } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { CreditsProvider } from '@/context/CreditsContext';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (!loading && !user) {
      // Not authenticated -> redirect to login with next param = current url
      const query = searchParams ? searchParams.toString() : '';
      const currentUrl = `${pathname || ''}${query ? `?${query}` : ''}`;
      const params = new URLSearchParams({ next: currentUrl });
      router.push(`/login?${params.toString()}`);
    }
  }, [loading, user, router, pathname, searchParams]);

  if (loading) {
    return <div className="flex h-full items-center justify-center p-4">Loading...</div>;
  }

  if (!user) {
    // While redirecting, render nothing
    return null;
  }

  return (
    <CreditsProvider>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>{children}</SidebarInset>
      </SidebarProvider>
    </CreditsProvider>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center p-4">Loading...</div>}>
      <DashboardContent>
        <div className="p-4 md:p-6">{children}</div>
      </DashboardContent>
    </Suspense>
  );
}
