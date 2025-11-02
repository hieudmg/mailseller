import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import React, { useEffect } from 'react';
import { api } from '@/lib/api';
import { useCredits } from '@/context/CreditsContext';
import { toast } from 'sonner';
import { Stock } from '@/types/api';

interface BuyDialogProps {
  trigger?: React.ReactNode;
  stock: Stock;
  type: string;
}

export default function BuyDialog({ trigger, stock, type }: BuyDialogProps) {
  const [buyQuantity, setBuyQuantity] = React.useState<number | ''>(1);
  const [boughtData, setBoughtData] = React.useState<string[]>(['1']);
  const [apiPath, setApiPath] = React.useState<string>('');
  const { refresh, token } = useCredits();

  useEffect(() => {
    // validate buyQuantity is numeric and greater than 0
    if (buyQuantity === '' || buyQuantity < 1) {
      setApiPath('');
      return;
    }

    setApiPath(
      'amount=' +
        buyQuantity +
        '&type=' +
        encodeURIComponent(type) +
        (token ? '&token=' + encodeURIComponent(token) : ''),
    );
  }, [buyQuantity, token]);

  return (
    <AlertDialog
      onOpenChange={(open) => {
        setTimeout(
          () => {
            setBuyQuantity(1);
            setBoughtData([]);
          },
          open ? 0 : 200,
        );
      }}
    >
      <AlertDialogTrigger asChild>{trigger}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Buy {stock.name}</AlertDialogTitle>
          {boughtData.length <= 0 && (
            <AlertDialogDescription>
              <span className="block">Buy some {stock.name} data directly using the API.</span>
              <span className="bg-accent text-foreground mt-4 block p-4 text-sm break-all">
                Direct URL: <br />
                <a
                  href={'/api/purchase?' + apiPath}
                  target="_blank"
                  className="text-primary-foreground underline"
                  title="Click to buy directly in new tab"
                  rel="noreferrer"
                >
                  {'/api/purchase?' + apiPath}
                </a>
              </span>
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <div>
          {boughtData.length <= 0 && (
            <Input
              type="number"
              placeholder="Qty"
              min={1}
              step={1}
              // Always pass a defined value (string | number) to avoid uncontrolled -> controlled
              value={buyQuantity === '' ? '' : buyQuantity}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const v = e.target.value;
                if (v === '') {
                  // allow clearing the field while keeping it controlled
                  setBuyQuantity('');
                  return;
                }
                const n = Number(v);
                if (Number.isNaN(n)) {
                  setBuyQuantity('');
                } else {
                  // coerce to integer and enforce a minimum of 1
                  setBuyQuantity(Math.max(1, Math.floor(n)));
                }
              }}
            />
          )}
          {boughtData.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="font-medium">Purchased Data:</p>
              <textarea
                className="border-input bg-background focus:border-primary focus:ring-primary w-full resize-none rounded-md border p-2 text-sm shadow-sm focus:ring-1 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                rows={Math.min(10, boughtData.length)}
                readOnly
                value={boughtData.join('\n')}
              />
            </div>
          )}
        </div>
        <AlertDialogFooter className="flex">
          <AlertDialogCancel>Close</AlertDialogCancel>
          <Button
            // @ts-expect-error test
            className={{ hidden: boughtData.length > 0 }}
            disabled={buyQuantity === '' || buyQuantity < 1}
            onClick={async () => {
              if (buyQuantity === '' || buyQuantity < 1) {
                return;
              }

              const buyResult = await api.purchaseData(buyQuantity, type);

              if (buyResult?.data) {
                // Purchase successful, update stock
                setBoughtData(buyResult.data.data);
              } else {
                // Handle purchase failure
                toast.error('Purchase failed. Please try again.');
              }

              setBuyQuantity(1);

              await refresh();
            }}
          >
            Confirm
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
