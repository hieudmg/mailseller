import { StockProvider, useStock } from '@/context/StockContext';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import React from 'react';
import { Stock } from '@/types/api';
import LightSkeleton from '@/components/light-skeleton';
import { formatAmount } from '@/lib/utils';

type actionFunction = (stock: Stock, type: string) => React.ReactNode;

function renderLifetime(lifetime: string) {
  switch (lifetime) {
    case 'short':
      return '1-5 hours';
    case 'long':
    default:
      return '6-12 months';
  }
}

function renderName({ name, code }: { name: string; code: string }) {
  return (
    <div className="flex items-center gap-2">
      <img src={`/mail/${code}.svg`} className="h-6 w-6" /> {name}
    </div>
  );
}

function renderProtocols(protocols?: string[]) {
  return protocols?.join(', ');
}

function StockTableInner({ action, header }: { action?: actionFunction; header?: React.ReactNode }) {
  const { stock } = useStock();

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      {header || <h1 className="text-2xl font-bold">Products</h1>}
      {Object.keys(stock).length <= 0 && (
        <div className="space-y-4">
          <LightSkeleton className="h-8 w-full" />
          <div className="flex gap-4">
            <LightSkeleton className="h-8 flex-1" />
            <LightSkeleton className="h-8 w-12" />
          </div>
          <div className="flex gap-4">
            <LightSkeleton className="h-8 flex-1" />
            <LightSkeleton className="h-8 w-12" />
          </div>
          <div className="flex gap-4">
            <LightSkeleton className="h-8 flex-1" />
            <LightSkeleton className="h-8 w-12" />
          </div>
        </div>
      )}
      {Object.keys(stock).length > 0 && (
        <>
          <div className="space-y-4 md:hidden">
            {Object.keys(stock).map(
              (key) =>
                stock?.[key] && (
                  <div key={key} className="rounded-lg border p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h2 className="text-lg font-semibold">{renderName(stock[key])}</h2>
                      <div>{action?.(stock[key], key)}</div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-muted-foreground text-sm">Lifetime:</div>
                        <div>{renderLifetime(stock[key].lifetime)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground text-sm">Enable:</div>
                        <div>{renderProtocols(stock[key].protocols)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground text-sm">Price:</div>
                        <div>
                          ${stock[key].price} <span className="opacity-75">/ acc.</span>
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground text-sm">Stock:</div>
                        <div>{stock[key].pool_size ?? 0}</div>
                      </div>
                    </div>
                  </div>
                ),
            )}
          </div>
          <Table className="hidden md:table">
            <TableHeader>
              <TableRow>
                <TableHead className="font-bold opacity-75">Products</TableHead>
                <TableHead className="font-bold opacity-75">Lifetime</TableHead>
                <TableHead className="font-bold opacity-75">Enable</TableHead>
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
                      <TableCell>{renderName(stock[key])}</TableCell>
                      <TableCell>{renderLifetime(stock[key].lifetime)}</TableCell>
                      <TableCell>{renderProtocols(stock[key].protocols)}</TableCell>
                      <TableCell>
                        {formatAmount(stock[key].price)} <span className="opacity-75">/ account</span>
                      </TableCell>
                      <TableCell>{stock[key].pool_size ?? 0}</TableCell>
                      <TableCell className="py-4 text-right">{action?.(stock[key], key)}</TableCell>
                    </TableRow>
                  ),
              )}
            </TableBody>
          </Table>
        </>
      )}
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
