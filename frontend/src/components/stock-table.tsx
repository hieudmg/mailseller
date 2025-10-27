import { StockProvider, useStock } from '@/context/StockContext';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import React from 'react';
import { Stock } from '@/types/api';

type actionFunction = (stock: Stock, type: string) => React.ReactNode;

function StockTableInner({ action, header }: { action?: actionFunction; header?: React.ReactNode }) {
  const { stock } = useStock();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      {header || <h1 className="text-2xl font-bold">Products</h1>}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="font-bold opacity-75">Products</TableHead>
            <TableHead className="font-bold opacity-75">Lifetime</TableHead>
            <TableHead className="font-bold opacity-75">Price</TableHead>
            <TableHead className="font-bold opacity-75">Stock</TableHead>
            <TableHead></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.keys(stock).map(
            (key) =>
              stock?.[key] && (
                <TableRow key={key}>
                  <TableCell>{stock[key].name}</TableCell>
                  <TableCell>{stock[key].lifetime === 'short' ? '1-5 hours' : '5-10 hours'}</TableCell>
                  <TableCell>
                    ${stock[key].price} <span className="opacity-75">/ account</span>
                  </TableCell>
                  <TableCell>{stock[key].pool_size ?? 0}</TableCell>
                  <TableCell className="py-4 text-right">{action?.(stock[key], key)}</TableCell>
                </TableRow>
              ),
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function StockTable({ action, header }: { action?: actionFunction; header?: React.ReactNode }) {
  return (
    <StockProvider>
      <StockTableInner action={action} header={header} />
    </StockProvider>
  );
}
