'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { StockProvider, useStock } from '@/context/StockContext';
import { Button } from '@/components/ui/button';
import React from 'react';
import BuyDialog from '@/components/dashboard/buy-dialog';
import Link from 'next/link';

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
          {Object.keys(stock).map((key) => (
            <TableRow key={key}>
              <TableCell>{key}</TableCell>
              <TableCell>1 credit / account</TableCell>
              <TableCell>{stock[key] ?? 0}</TableCell>
              <TableCell className="py-4 text-right">
                <BuyDialog type={key} trigger={<Button>Buy</Button>} />
              </TableCell>
            </TableRow>
          ))}
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
