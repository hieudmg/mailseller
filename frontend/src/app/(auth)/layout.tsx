'use client';

import React, { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import Icon from '@/components/icon';

function AuthLayoutContent({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (!loading && user) {
      const next = searchParams.get('next') || '/dashboard';
      router.push(next);
    }
  }, [loading, user, router, searchParams]);

  if (loading) {
    return <div className="flex h-full items-center justify-center p-4">Loading...</div>;
  }

  if (user) {
    // While redirecting, render nothing
    return null;
  }

  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex justify-center gap-2 md:justify-start">
          <Link href="/" className="flex items-center gap-2 font-medium">
            <Icon />
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-xs">{children}</div>
        </div>
      </div>
      <div className="relative hidden bg-[radial-gradient(#408CFF_3px,transparent_3px),radial-gradient(#408CFF_3px,rgba(0,0,0,0)_3px)] bg-[length:80px_80px] bg-[position:0_0,40px_40px] lg:block"></div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="flex h-full items-center justify-center p-4">Loading...</div>}>
      <AuthLayoutContent>{children}</AuthLayoutContent>
    </Suspense>
  );
}
