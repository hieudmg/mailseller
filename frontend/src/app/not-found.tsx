'use client';
import Link from 'next/link';
import { TopNavbar } from '@/components/top-navbar';
import { ArrowLeft, Home } from 'lucide-react';

export default function NotFound() {
  return (
    <>
      <TopNavbar />
      <main className="container mx-auto">
        <div className="flex min-h-[80vh] flex-col items-center justify-center text-center">
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-2 text-purple-300">
            <span>Error 404</span>
          </div>

          <h1 className="mb-6 bg-gradient-to-r from-red-400 via-purple-400 to-blue-400 bg-clip-text pb-2 text-5xl text-transparent md:text-7xl">
            Page Not Found
          </h1>

          <p className="mx-auto mb-12 max-w-2xl text-xl text-slate-300">
            The page you are looking for does not exist or has been moved.
          </p>

          <div className="flex gap-4">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-6 py-3 text-white transition-colors hover:bg-purple-700"
            >
              <Home className="h-5 w-5" />
              Go Home
            </Link>
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center gap-2 rounded-lg border border-purple-500/20 bg-purple-500/10 px-6 py-3 text-purple-300 transition-colors hover:bg-purple-500/20"
            >
              <ArrowLeft className="h-5 w-5" />
              Go Back
            </button>
          </div>
        </div>
      </main>
    </>
  );
}
