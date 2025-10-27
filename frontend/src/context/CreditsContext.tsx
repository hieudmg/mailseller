import React, { createContext, useContext, useEffect, useState, useMemo, useCallback, useRef, ReactNode } from 'react';
import { api } from '@/lib/api';

export type TierData = {
  tier_code: string;
  tier_name: string;
  tier_discount: number;
  deposit_amount: number;
  next_tier: {
    tier_code: string;
    tier_name: string;
    tier_discount: number;
    required_deposit: number;
    remaining: number;
  } | null;
  custom_discount: number | null;
  final_discount: number;
  discount_source: 'custom' | 'tier';
};

type CreditsContextType = {
  credits: number;
  tierData: TierData | null;
  refresh: () => Promise<void>;
  loading: boolean;
  error?: string;
  token?: string;
};

const CreditsContext = createContext<CreditsContextType | undefined>(undefined);

export const CreditsProvider = ({ children }: { children: ReactNode }) => {
  const [credits, setCredits] = useState<number>(0);
  const [tierData, setTierData] = useState<TierData | null>(null);
  const [token, setToken] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);
  const isInitialLoad = useRef(true);

  const getCreditsAndTier = useCallback(async () => {
    // Only set loading on initial load, not on polling refreshes
    if (isInitialLoad.current) {
      setLoading(true);
    }

    try {
      // Fetch credits and tier data in parallel
      const [creditsResponse, tierResponse, tokenResponse] = await Promise.all([
        api.getCredits(),
        api.getTier(),
        api.getToken(),
      ]);

      const newCredits = creditsResponse?.data?.credits ?? 0;
      const newTierData = tierResponse?.data ?? null;

      // Only update state if data actually changed
      setCredits((prev) => (prev !== newCredits ? newCredits : prev));
      setTierData((prev) => {
        // Deep comparison for tier data
        if (!newTierData && !prev) return prev;
        if (!newTierData || !prev) return newTierData;
        if (JSON.stringify(prev) === JSON.stringify(newTierData)) return prev;
        return newTierData;
      });
      setToken((prev) => {
        const newToken = tokenResponse?.data?.token;
        return prev !== newToken ? newToken : prev;
      });

      setError(undefined);
    } catch (err: unknown) {
      // normalize unknown error
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err ?? 'Failed to fetch credits and tier data'));
      }
    } finally {
      if (isInitialLoad.current) {
        setLoading(false);
        isInitialLoad.current = false;
      }
    }
  }, []);

  useEffect(() => {
    getCreditsAndTier();
    const id = setInterval(getCreditsAndTier, 60000);
    return () => clearInterval(id);
  }, [getCreditsAndTier]);

  // Memoize context value to prevent unnecessary re-renders
  const value = useMemo(
    () => ({ credits, tierData, refresh: getCreditsAndTier, loading, error, token }),
    [credits, tierData, getCreditsAndTier, loading, error, token],
  );

  return <CreditsContext.Provider value={value}>{children}</CreditsContext.Provider>;
};

export const useCredits = (): CreditsContextType => {
  const ctx = useContext(CreditsContext);
  if (!ctx) throw new Error('useCredits must be used within a CreditsProvider');
  return ctx;
};
