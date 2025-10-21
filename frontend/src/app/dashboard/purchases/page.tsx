'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Search, RefreshCw } from 'lucide-react';
import { Paginate } from '@/components/paginate';
import throttle from 'lodash/throttle';

interface Transaction {
  id: number;
  amount: number;
  description: string;
  data_id: string | null;
  timestamp: string;
}

interface TransactionsResponse {
  page: number | undefined;
  limit: number | undefined;
  total: number | undefined;
  transactions: Transaction[] | undefined;
}

export default function PurchasesPage() {
  const [results, setResults] = useState<TransactionsResponse>();
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [viewData, setViewData] = useState<string | null>(null);
  const throttledFetch = useMemo(() => throttle((p: number) => fetchTransactions(p), 200), []);

  useEffect(() => {
    throttledFetch(page);
  }, [page, throttledFetch]);

  // Optional cleanup: cancel pending throttled calls on unmount
  useEffect(() => {
    return () => throttledFetch.cancel();
  }, [throttledFetch]);

  const fetchTransactions = async (page: number = 1) => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/transactions?limit=${pageSize}&page=${page}`, {
        credentials: 'include',
      });
      if (!response.ok) {
        const errorMsg = 'Failed to fetch transactions';
        setError(errorMsg);
        throw new Error(errorMsg);
      }
      const data = await response.json();
      setResults(data || {});
    } catch (error) {
      toast.error('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getTransactionTypeColor = (amount: number) => {
    if (amount < 0) {
      return 'text-red-500';
    } else if (amount > 0) {
      return 'text-green-500';
    }
    return 'text-gray-500';
  };

  const formatAmount = (amount: number) => {
    const absoluteAmount = Math.abs(amount);
    const sign = amount > 0 ? '+' : '-';
    return `${sign} $${absoluteAmount}`;
  };

  return (
    <div className="flex flex-1 flex-col gap-4 p-4">
      <div className="flex items-center gap-2 space-y-2">
        <h1 className="text-2xl font-bold">Transaction History</h1>
        <button
          type="button"
          className="rounded p-2 hover:bg-gray-100"
          title="Refresh"
          aria-label="Refresh"
          onClick={() => fetchTransactions()}
          disabled={loading}
        >
          <RefreshCw className={`h-5 w-5 ${loading ? 'text-muted-foreground animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-muted-foreground">View all your credit transactions and purchases.</p>
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>{loading ? 'Loading...' : `${results?.total} transaction(s) found`}</CardDescription>
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
              <p>No transactions found.</p>
              <p className="mt-2 text-sm">Your transaction history will appear here.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Data</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results?.transactions?.map((transaction) => (
                    <TableRow key={transaction.id}>
                      <TableCell className="font-mono text-sm">{formatDate(transaction.timestamp)}</TableCell>
                      <TableCell>{transaction.description}</TableCell>
                      <TableCell className={`text-right font-semibold ${getTransactionTypeColor(transaction.amount)}`}>
                        {formatAmount(transaction.amount)}
                      </TableCell>
                      <TableCell className="text-muted-foreground flex items-center gap-2 truncate text-xs">
                        {transaction.data_id && (
                          <button
                            className="rounded p-1 hover:bg-gray-100"
                            title="View full data"
                            onClick={() => setViewData(transaction.data_id)}
                          >
                            <Search className="h-4 w-4" />
                          </button>
                        )}
                      </TableCell>
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
      <Dialog open={!!viewData} onOpenChange={() => setViewData(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Full Data</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-2">
            <div className="relative">
              <textarea
                readOnly
                value={viewData ? viewData.split(',').join('\n') : ''}
                className="bg-muted text-muted-foreground min-h-64 w-full resize-none rounded border p-2 text-sm"
              />
              <button
                className="absolute top-2 right-2 rounded border bg-white p-1 hover:bg-gray-100"
                title="Copy"
                onClick={() => {
                  if (viewData) {
                    navigator.clipboard.writeText(viewData);
                    toast.success('Copied to clipboard');
                  }
                }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" strokeWidth="2" />
                  <rect x="3" y="3" width="13" height="13" rx="2" strokeWidth="2" />
                </svg>
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
