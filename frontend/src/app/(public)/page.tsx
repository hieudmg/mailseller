'use client';

import Link from 'next/link';
import { StockTable } from '@/components/stock-table';

export default function Home() {
  return (
    <StockTable
      action={() => (
        <Link className="bg-primary text-accent rounded px-4 py-2" href="/dashboard/products">
          Buy
        </Link>
      )}
    />
  );
}
