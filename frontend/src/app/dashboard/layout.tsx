'use client';

import React, { useEffect, Suspense } from 'react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { NavUser } from '@/components/nav-user';
import { Spinner } from '@/components/ui/spinner';
import FullScreenLoader from '@/components/full-screen-loader';

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
    return <FullScreenLoader />;
  }

  if (!user) {
    // While redirecting, render nothing
    return null;
  }

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="md:hidden" />
          <div className="ml-auto">
            <NavUser email={user.email} />
          </div>
        </header>
        {children}
      </SidebarInset>
    </SidebarProvider>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<FullScreenLoader />}>
      <DashboardContent>
        <div className="p-4 md:p-6">{children}</div>
      </DashboardContent>
    </Suspense>
  );
}
