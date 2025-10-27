'use client';

import { useState, useEffect, useMemo, ReactNode } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { RefreshCw } from 'lucide-react';
import { Paginate } from '@/components/paginate';
import throttle from 'lodash/throttle';
import { api } from '@/lib/api';
import { Transaction, TransactionsResponse } from '@/types/api';

interface ColumnConfig {
  header: string;
  className?: string;
  render: (transaction: Transaction) => ReactNode;
}

interface TransactionLayoutProps {
  title: string;
  description: string;
  cardTitle: string;
  transactionType: 'purchase' | 'admin_deposit' | 'heleket';
  columns: ColumnConfig[];
  emptyMessage: string;
  emptySubtext: string;
  errorMessage: string;
}

export function TransactionLayout({
  title,
  description,
  cardTitle,
  transactionType,
  columns,
  emptyMessage,
  emptySubtext,
  errorMessage,
}: TransactionLayoutProps) {
  const [results, setResults] = useState<TransactionsResponse>();
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const throttledFetch = useMemo(() => throttle((p: number) => fetchTransactions(p), 200), []);

  useEffect(() => {
    throttledFetch(page);
  }, [page, throttledFetch]);

  useEffect(() => {
    return () => throttledFetch.cancel();
  }, [throttledFetch]);

  const fetchTransactions = async (page: number = 1) => {
    setLoading(true);
    setError('');
    try {
      const transactions = await api.getTransactions({ page, limit: pageSize, types: [transactionType] });
      setResults(transactions.data);
    } catch (error) {
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div className="flex items-center gap-2 space-y-2">
        <h1 className="text-2xl font-bold">{title}</h1>
        <button
          type="button"
          className="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
          title="Refresh"
          aria-label="Refresh"
          onClick={() => fetchTransactions()}
          disabled={loading}
        >
          <RefreshCw className={`h-5 w-5 ${loading ? 'text-muted-foreground animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-muted-foreground">{description}</p>
      <Card>
        <CardHeader>
          <CardTitle>{cardTitle}</CardTitle>
          <CardDescription>{loading ? 'Loading...' : `${results?.total || 0} transaction(s) found`}</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="py-8 text-center">
              <p className="font-medium text-red-500">⚠️ {error}</p>
              <button onClick={() => fetchTransactions()} className="mt-4 text-sm text-blue-500 hover:underline">
                Try again
              </button>
            </div>
          ) : loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : results?.total === 0 ? (
            <div className="text-muted-foreground py-8 text-center">
              <p>{emptyMessage}</p>
              <p className="mt-2 text-sm">{emptySubtext}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    {columns.map((col, index) => (
                      <TableHead key={index} className={col.className}>
                        {col.header}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results?.transactions?.map((transaction) => (
                    <TableRow key={transaction.id}>
                      {columns.map((col, index) => (
                        <TableCell key={index} className={col.className}>
                          {col.render(transaction)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <Paginate
                className="mt-4"
                page={page}
                total={results?.total || 0}
                limit={pageSize}
                onPageChange={(page) => setPage(page)}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// Utility functions for common formatting
export const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getTransactionTypeColor = (amount: number) => {
  if (amount < 0) return 'text-red-500';
  if (amount > 0) return 'text-green-500';
  return 'text-gray-500';
};

export const formatAmount = (amount: number) => {
  const absoluteAmount = Math.abs(amount);
  const sign = amount > 0 ? '+' : '-';
  return `${sign} $${absoluteAmount.toFixed(2)}`;
};
