'use client';

import React from 'react';
import { StockTable } from '@/components/stock-table';
import BuyDialog from '@/components/dashboard/buy-dialog';
import { Button } from '@/components/ui/button';

export default function ProductsPage() {
  return (
    <StockTable action={(stock, type) => <BuyDialog type={type} stock={stock} trigger={<Button>Buy</Button>} />} />
  );
}
