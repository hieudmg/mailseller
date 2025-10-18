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
import React from 'react';
import { api } from '@/lib/api';

interface BuyDialogProps {
  trigger?: React.ReactNode;
}

export default function BuyDialog({ trigger }: BuyDialogProps) {
  const [buyQuantity, setBuyQuantity] = React.useState<number | ''>(1);
  const [boughtData, setBoughtData] = React.useState<string[]>(['1']);

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
          <AlertDialogTitle>Buy Data</AlertDialogTitle>
          {boughtData.length <= 0 && (
            <AlertDialogDescription>Buy some data directly without using the API.</AlertDialogDescription>
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

              const buyResult = await api.purchaseData(buyQuantity);

              if (buyResult?.data) {
                // Purchase successful, update stock
                setBoughtData(buyResult.data.data);
              } else {
                // Handle purchase failure
                alert('Purchase failed. Please try again.');
              }

              setBuyQuantity(1);
            }}
          >
            Confirm
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
