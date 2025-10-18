'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import Link from 'next/link';
import { StockProvider, useStock } from '@/context/StockContext';

function HomeContent() {
  const { stock } = useStock();

  return (
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
              <Link className="bg-primary text-accent rounded px-4 py-2" href="/dashboard/products">
                Buy
              </Link>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export default function Home() {
  return (
    <StockProvider>
      <HomeContent />
    </StockProvider>
  );
}
