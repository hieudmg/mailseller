import { StockProvider, useStock } from '@/context/StockContext';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import React from 'react';

type actionFunction = ({ key }: { key: string }) => React.ReactNode;

function StockTableInner({ action }: { action?: actionFunction }) {
  const { stock } = useStock();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <h1 className="text-2xl font-bold">Products</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Products</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Price</TableHead>
            <TableHead>Stock</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.keys(stock).map(
            (key) =>
              stock?.[key] && (
                <TableRow key={key}>
                  <TableCell>{stock[key].name}</TableCell>
                  <TableCell>{stock[key].lifetime}</TableCell>
                  <TableCell>${stock[key].price} / account</TableCell>
                  <TableCell>{stock[key].pool_size ?? 0}</TableCell>
                  <TableCell className="py-4 text-right">{action?.({ key })}</TableCell>
                </TableRow>
              ),
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function StockTable({ action }: { action?: actionFunction }) {
  return (
    <StockProvider>
      <StockTableInner action={action} />
    </StockProvider>
  );
}
