'use client';

import { useEffect, useState } from 'react';
import { useCredits } from '@/context/CreditsContext';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import Header from '@/components/dashboard/header';
import Image from 'next/image';
import { formatAmount } from '@/lib/utils';

const TIER_COLORS: Record<string, string> = {
  iron: 'bg-gray-400',
  bronze: 'bg-amber-600',
  silver: 'bg-gray-300',
  gold: 'bg-yellow-500',
  diamond: 'bg-blue-400',
};

type Tier = {
  code: string;
  name: string;
  discount: number;
  threshold: number;
};

export default function RankingPage() {
  const { tierData, loading } = useCredits();
  const [tiers, setTiers] = useState<Tier[]>([]);
  const [tiersLoading, setTiersLoading] = useState(true);

  useEffect(() => {
    const fetchTiers = async () => {
      const response = await api.getTiers();
      if (response.data?.tiers) {
        setTiers(response.data.tiers);
      }
      setTiersLoading(false);
    };

    fetchTiers();
  }, []);

  if (loading || tiersLoading) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-4">
        <h1 className="text-2xl font-bold">Your Ranking</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!tierData || tiers.length === 0) {
    return (
      <div className="flex flex-1 flex-col gap-4 p-4">
        <h1 className="text-2xl font-bold">Your Ranking</h1>
        <p className="text-muted-foreground">Unable to load tier information.</p>
      </div>
    );
  }

  const progressToNextTier = tierData.next_tier
    ? (tierData.deposit_amount / tierData.next_tier.required_deposit) * 100
    : 100;

  return (
    <div className="flex flex-col gap-6">
      <Header title="Your Ranking" subtitle="View your current tier and progress to the next tier." />

      {/* Current Tier Card */}
      <Card className="border-2">
        <CardContent className="space-y-4">
          {tierData.custom_discount !== null ? (
            /* Custom Discount View - No tier/progress shown */
            <>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">Custom Discount</div>
                  <div className="text-muted-foreground mt-1 text-sm">
                    Special discount applied by admin
                  </div>
                </div>
                <Badge className={`px-4 py-2 text-lg`}>{tierData.final_discount * 100}% OFF</Badge>
              </div>

              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">🎁 Custom Discount Active</p>
                <p className="mt-1 text-xs text-blue-700 dark:text-blue-300">
                  You have a custom {tierData.custom_discount * 100}% discount applied by an admin. This overrides the
                  tier-based discount system.
                </p>
              </div>
            </>
          ) : (
            /* Normal Tier View - Show tier and progress */
            <>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-bold">{tierData.tier_name}</div>
                  <div className="text-muted-foreground mt-1 text-sm">
                    {formatAmount(tierData.deposit_amount)} deposited in last 7 days
                  </div>
                </div>
                <Badge className={`px-4 py-2 text-lg`}>{tierData.final_discount * 100}% OFF</Badge>
              </div>

              {tierData.next_tier && (
                <div className="space-y-2 border-t pt-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Progress to {tierData.next_tier.tier_name}</span>
                    <span className="font-medium">
                      {formatAmount(tierData.deposit_amount)} / {formatAmount(tierData.next_tier.required_deposit)}
                    </span>
                  </div>
                  <Progress value={progressToNextTier} className="h-2" />
                  <p className="text-muted-foreground text-xs">
                    {formatAmount(tierData.next_tier.remaining)} more to unlock {tierData.next_tier.tier_discount * 100}
                    % discount
                  </p>
                </div>
              )}

              {!tierData.next_tier && (
                <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-800 dark:bg-green-950">
                  <p className="text-sm font-medium text-green-900 dark:text-green-100">🏆 Maximum Tier Reached!</p>
                  <p className="mt-1 text-xs text-green-700 dark:text-green-300">
                    You have reached the highest tier available
                  </p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* All Tiers Card */}
      <Card>
        <CardHeader>
          <CardTitle>All Tiers</CardTitle>
          <CardDescription>Deposit more in the next 7 days to unlock better discounts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {tiers.map((tier) => {
              // Don't highlight current tier if custom discount is set
              const isCurrentTier = tierData.custom_discount === null && tier.code === tierData.tier_code;
              return (
                <div
                  key={tier.code}
                  className={`flex items-center justify-between rounded-lg border-2 p-4 transition-all ${
                    isCurrentTier
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-border hover:border-muted-foreground/30'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`h-12 w-12 rounded-full ${TIER_COLORS[tier.code] || 'bg-gray-400'} flex items-center justify-center font-bold text-white`}
                    >
                      <Image src={`/ranks/${tier.code}.png`} alt={tier.code} width={48} height={48} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 font-semibold">
                        {tier.name}
                        {isCurrentTier && (
                          <Badge variant="default" className="text-xs">
                            Current
                          </Badge>
                        )}
                      </div>
                      <div className="text-muted-foreground text-sm">{formatAmount(tier.threshold)}+ in 7 days</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{tier.discount * 100}%</div>
                    <div className="text-muted-foreground text-xs">discount</div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
