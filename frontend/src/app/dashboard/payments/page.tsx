'use client';

import { TransactionLayout, formatDate } from '@/components/transaction-layout';
import { Transaction } from '@/types/api';
import { formatAmount } from '@/lib/utils';

export default function PaymentsPage() {
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
      render: (transaction: Transaction) => <span className="text-green-500">{formatAmount(transaction.amount)}</span>,
    },
  ];

  return (
    <TransactionLayout
      title="Credit Deposits"
      description="View all your credit deposits and top-ups."
      cardTitle="Recent Deposits"
      transactionType="admin_deposit"
      columns={columns}
      emptyMessage="No credit deposits found."
      emptySubtext="Your deposit history will appear here when you add credits."
      errorMessage="Failed to fetch credit deposits"
    />
  );
}
