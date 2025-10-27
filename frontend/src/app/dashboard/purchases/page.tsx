'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Search } from 'lucide-react';
import { toast } from 'sonner';
import { TransactionLayout, formatDate, getTransactionTypeColor, formatAmount } from '@/components/transaction-layout';
import { Transaction } from '@/types/api';

export default function PurchasesPage() {
  const [viewData, setViewData] = useState<string | null>(null);

  const columns = [
    {
      header: 'Date',
      render: (transaction: Transaction) => (
        <span className="font-mono text-sm">{formatDate(transaction.timestamp)}</span>
      ),
    },
    {
      header: 'Description',
      render: (transaction: Transaction) => <span>{transaction.description}</span>,
    },
    {
      header: 'Amount',
      className: 'text-right',
      render: (transaction: Transaction) => (
        <span className={`font-semibold ${getTransactionTypeColor(transaction.amount)}`}>
          {formatAmount(transaction.amount)}
        </span>
      ),
    },
    {
      header: 'Data',
      render: (transaction: Transaction) => (
        <div className="text-muted-foreground flex items-center gap-2 truncate text-xs">
          {transaction.data_id && (
            <button
              className="rounded p-1 hover:bg-gray-100"
              title="View full data"
              onClick={() => setViewData('' + transaction.data_id)}
            >
              <Search className="h-4 w-4" />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <TransactionLayout
        title="Purchase History"
        description="View all your data purchases and spending history."
        cardTitle="Recent Purchases"
        transactionType="purchase"
        columns={columns}
        emptyMessage="No purchases found."
        emptySubtext="Your purchase history will appear here when you buy data."
        errorMessage="Failed to fetch purchases"
      />
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
    </>
  );
}
