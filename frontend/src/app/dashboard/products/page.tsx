'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { StockProvider, useStock } from '@/context/StockContext';
import { Button } from '@/components/ui/button';
import React from 'react';
import BuyDialog from '@/components/dashboard/buy-dialog';

function ProductsPageContent() {
  const { stock } = useStock();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <h1 className="text-2xl font-bold">Products</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Products</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Stock</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Short Live Emails</TableCell>
            <TableCell>1 credit / account</TableCell>
            <TableCell>{stock}</TableCell>
            <TableCell className="py-4 text-right">
              <BuyDialog trigger={<Button>Buy</Button>} />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}

export default function ProductsPage() {
  return (
    <StockProvider>
      <ProductsPageContent />
    </StockProvider>
  );
}
