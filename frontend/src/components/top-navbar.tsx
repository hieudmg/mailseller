'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Menu } from 'lucide-react';
import Icon from '@/components/icon';

export function TopNavbar() {
  const [isOpen, setIsOpen] = useState(false);
  const { user, loading, logout } = useAuth();

  const isLoggedIn = !!user;
  const userEmail = user?.email ?? null;

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/api-docs', label: 'API docs' },
    { href: '/tos', label: 'ToS' },
    { href: '/privacy', label: 'Privacy' },
    { href: '/telegram', label: 'Our Telegram' },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = '/';
  };

  const renderAuthButtons = (mobile: boolean = false) => {
    if (loading) {
      return <div className="text-muted-foreground text-sm">Loading...</div>;
    }

    if (isLoggedIn) {
      return (
        <>
          {mobile ? (
            <div className="text-foreground/60 px-2 py-1 text-sm">{userEmail}</div>
          ) : (
            <span className="text-foreground/60 text-sm">{userEmail}</span>
          )}
          <Button variant="ghost" asChild className={mobile ? 'justify-start' : ''}>
            <Link href="/dashboard" onClick={() => mobile && setIsOpen(false)}>
              Dashboard
            </Link>
          </Button>
          <Button
            variant="outline"
            className={mobile ? 'justify-start' : ''}
            onClick={async () => {
              await handleLogout();
              if (mobile) setIsOpen(false);
            }}
          >
            Logout
          </Button>
        </>
      );
    }

    return (
      <>
        <Button variant="ghost" asChild className={mobile ? 'justify-start' : ''}>
          <Link href="/login" onClick={() => mobile && setIsOpen(false)}>
            Login
          </Link>
        </Button>
        <Button asChild className={mobile ? 'justify-start' : ''}>
          <Link href="/register" onClick={() => mobile && setIsOpen(false)}>
            Register
          </Link>
        </Button>
      </>
    );
  };

  return (
    <header className="bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50 w-full border-b backdrop-blur">
      <div className="container mx-auto flex h-14 items-center">
        {/* Left zone: Icon */}
        <div className="mr-4">
          <Link href="/" className="flex items-center space-x-2">
            <Icon />
          </Link>
        </div>

        {/* Center zone: Navigation links (hidden on mobile) */}
        <nav className="hidden flex-1 items-center justify-center space-x-6 text-sm font-medium md:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="hover:text-foreground/80 text-foreground/60 transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Right zone: Login and Register (hidden on mobile) */}
        <div className="ml-auto hidden items-center space-x-4 md:flex">{renderAuthButtons()}</div>

        {/* Mobile hamburger menu */}
        <div className="ml-auto md:hidden">
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="sm" className="px-2">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <nav className="flex flex-col space-y-4">
                {navLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="block px-2 py-1 text-lg"
                    onClick={() => setIsOpen(false)}
                  >
                    {link.label}
                  </Link>
                ))}
                <div className="flex flex-col space-y-2 border-t pt-4">{renderAuthButtons(true)}</div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
