'use client';

import { StockProvider } from '@/context/StockContext';
import React from 'react';
import { StockTable } from '@/components/stock-table';
import BuyDialog from '@/components/dashboard/buy-dialog';
import { Button } from '@/components/ui/button';

export default function ProductsPage() {
  return <StockTable action={({ key }) => <BuyDialog type={key} trigger={<Button>Buy</Button>} />} />;
}
