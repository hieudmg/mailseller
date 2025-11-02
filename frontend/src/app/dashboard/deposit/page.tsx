'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { ExternalLink, Clock, DollarSign, History } from 'lucide-react';
import { InvoiceResponse, Transaction } from '@/types/api';
import Header from '@/components/dashboard/header';
import { formatAmount } from '@/lib/utils';

export default function DepositPage() {
  const [amount, setAmount] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [invoice, setInvoice] = useState<InvoiceResponse | null>(null);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [transactionsLoading, setTransactionsLoading] = useState(false);

  // Fetch recent heleket transactions
  useEffect(() => {
    fetchTransactions();
  }, []);

  // Countdown timer for invoice expiry
  useEffect(() => {
    if (!invoice) return;

    const interval = setInterval(() => {
      const now = Math.floor(Date.now() / 1000);
      const remaining = invoice.expires_at - now;

      if (remaining <= 0) {
        setTimeLeft(0);
        setInvoice(null);
      } else {
        setTimeLeft(remaining);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [invoice]);

  const fetchTransactions = async () => {
    try {
      setTransactionsLoading(true);
      const result = await api.getTransactions({ types: ['heleket'], limit: 10 });
      setTransactions(result?.data?.transactions || []);
    } catch (error: unknown) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setTransactionsLoading(false);
    }
  };

  const handleCreateInvoice = async () => {
    const amountNum = parseFloat(amount);

    if (!amount || isNaN(amountNum) || amountNum < 1) {
      toast.error('Please enter a valid amount (minimum $1)');
      return;
    }

    try {
      setLoading(true);
      const result = await api.createInvoice(amountNum);

      if (result.error) {
        toast.error(result.error);
        return;
      }

      if (!result.data) {
        toast.error('Failed to create invoice');
        return;
      }

      setInvoice(result.data);
      const now = Math.floor(Date.now() / 1000);
      setTimeLeft(result.data.expires_at - now);
      toast.success('Invoice created! Click the button to pay with crypto.');
    } catch (error) {
      // @ts-expect-error error type
      toast.error(error?.message || 'Failed to create invoice');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const parseHeleketData = (dataId: string | null) => {
    if (!dataId) return null;
    try {
      return JSON.parse(dataId);
    } catch {
      return null;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <Header
        title="Deposit Credits"
        subtitle="Add funds to your account using cryptocurrency via Heleket payment gateway"
      />

      {/* Create Invoice Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            Create Payment Invoice
          </CardTitle>
          <CardDescription>
            Enter the amount in USD you want to deposit. You will receive credits equal to the amount paid.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="amount">Amount (USD)</Label>
            <Input
              id="amount"
              type="number"
              min="1"
              step="0.01"
              placeholder="10.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              disabled={loading || !!invoice}
            />
            <p className="text-muted-foreground text-sm">Minimum deposit: {formatAmount(1)}</p>
          </div>
          <Button onClick={handleCreateInvoice} disabled={loading || !!invoice} className="w-full">
            {loading ? 'Creating Invoice...' : 'Create Invoice'}
          </Button>
        </CardContent>
      </Card>

      {/* Active Invoice */}
      {invoice && (
        <Card className="border-primary">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Active Payment Invoice</span>
              <div className="flex items-center gap-2 text-sm font-normal">
                <Clock className="h-4 w-4" />
                <span className={timeLeft < 300 ? 'text-destructive' : ''}>Expires in {formatTime(timeLeft)}</span>
              </div>
            </CardTitle>
            <CardDescription>Complete your payment using cryptocurrency</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-muted-foreground text-sm">Order ID</p>
              <p className="font-mono text-sm">{invoice.order_id}</p>
            </div>

            <Button asChild className="w-full" size="lg">
              <a
                href={invoice.invoice_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Pay with Cryptocurrency
              </a>
            </Button>

            <div className="bg-muted space-y-2 rounded-lg p-4">
              <p className="text-sm font-medium">Instructions:</p>
              <ul className="text-muted-foreground list-inside list-disc space-y-1 text-sm">
                <li>Click the button above to open the payment page</li>
                <li>Select your preferred cryptocurrency</li>
                <li>Complete the payment</li>
                <li>Credits will be added to your account automatically</li>
              </ul>
            </div>

            <Button
              variant="outline"
              onClick={() => {
                setInvoice(null);
                setAmount('');
                fetchTransactions();
              }}
              className="w-full"
            >
              Cancel Invoice
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Recent Deposits */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Recent Deposits
          </CardTitle>
          <CardDescription>Your recent Heleket payment transactions</CardDescription>
        </CardHeader>
        <CardContent>
          {transactionsLoading ? (
            <p className="text-muted-foreground py-4 text-center">Loading...</p>
          ) : transactions.length === 0 ? (
            <p className="text-muted-foreground py-4 text-center">No deposits yet</p>
          ) : (
            <div className="space-y-3">
              {transactions.map((tx) => {
                const heleketData = parseHeleketData(`${tx.data_id}`);
                return (
                  <div key={tx.id} className="flex items-start justify-between border-b pb-3 last:border-0">
                    <div className="space-y-1">
                      <p className="font-medium">{tx.description}</p>
                      <p className="text-muted-foreground text-sm">{formatDate(tx.timestamp)}</p>
                      {heleketData && (
                        <p className="text-muted-foreground font-mono text-xs">
                          {heleketData.payer_currency} via {heleketData.network}
                          {heleketData.txid && ` • ${heleketData.txid.substring(0, 10)}...`}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-green-600">+${tx.amount.toFixed(2)}</p>
                      {heleketData && heleketData.payment_amount_usd && (
                        <p className="text-muted-foreground text-xs">${heleketData.payment_amount_usd} USD</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
