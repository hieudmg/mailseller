'use client';

import * as React from 'react';
import { useMemo } from 'react';
import { Package, Settings, CreditCard, ShoppingBag, DollarSign, Trophy, User } from 'lucide-react';

import { NavMain } from '@/components/nav-main';
import { NavUser } from '@/components/nav-user';
import { useAuth } from '@/context/AuthContext';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar';
import Icon from '@/components/icon';
import Link from 'next/link';

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const navMain = [
    {
      title: 'Profile',
      url: '/dashboard/profile',
      icon: User,
    },
    {
      title: 'Products',
      url: '/dashboard/products',
      icon: Package,
    },
    {
      title: 'Your Payments',
      url: '/dashboard/payments',
      icon: CreditCard,
    },
    {
      title: 'Your Purchases',
      url: '/dashboard/purchases',
      icon: ShoppingBag,
    },
    {
      title: 'Deposit',
      url: '/dashboard/deposit',
      icon: DollarSign,
    },
    {
      title: 'Your Ranking',
      url: '/dashboard/ranking',
      icon: Trophy,
    },
  ];

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton className="hover:bg-transparent" asChild>
                <Link href="/" className="py-6">
                  <Icon />
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
        <NavMain items={navMain} />
      </SidebarContent>
    </Sidebar>
  );
}
