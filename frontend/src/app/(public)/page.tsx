'use client';

import Link from 'next/link';
import { StockTable } from '@/components/stock-table';
import { Card } from '@/components/ui/card';
import { ArrowDown, ArrowRight, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <div className="relative mt-20 mb-36 flex flex-col gap-4">
      <div className="mx-auto mb-36 max-w-4xl text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-4 py-2 text-purple-300">
            <Sparkles className="h-4 w-4" />
            <span>Premium Email Accounts</span>
          </div>

          <h1 className="mb-6 bg-gradient-to-r from-red-400 via-purple-400 to-blue-400 bg-clip-text text-5xl text-transparent md:text-7xl">
            Protect your identity with secure email
          </h1>

          <p className="mx-auto mb-12 max-w-2xl text-xl text-slate-300">Fast, secure, exclusive email accounts.</p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              size="lg"
              className="group cursor-pointer bg-gradient-to-r from-purple-500 to-blue-500 px-0 text-lg hover:from-purple-600 hover:to-blue-600"
              onClick={() => {
                document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Explore Accounts
              <ArrowDown className="ml-2 h-5 w-5 transition-transform" />
            </Button>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="mx-auto mt-24 grid max-w-3xl grid-cols-3 gap-8"
        >
          <div className="text-center">
            <div className="mb-2 text-4xl text-white">5,000+</div>
            <div className="text-slate-400">Hourly Stock</div>
          </div>
          <div className="text-center">
            <div className="mb-2 text-4xl text-white">1,000+</div>
            <div className="text-slate-400">Happy Customers</div>
          </div>
          <div className="text-center">
            <div className="mb-2 text-4xl text-white">100%</div>
            <div className="text-slate-400">Working Accounts</div>
          </div>
        </motion.div>
      </div>
      <StockTable
        action={() => (
          <Link className="bg-primary text-foreground rounded px-4 py-2" href="/dashboard/products">
            Buy
          </Link>
        )}
        header={
          <div className="mb-10 text-center">
            <h2 id="products" className="shadow-foreground gradient-text mb-6 text-5xl text-transparent">
              Get Your Secure Email Accounts Today
            </h2>
            <h3>
              Get up to 20% discount on purchases!{' '}
              <Link className="gradient-text" href="/dashboard/ranking">
                Learn More
              </Link>
            </h3>
          </div>
        }
      />
    </div>
  );
}
