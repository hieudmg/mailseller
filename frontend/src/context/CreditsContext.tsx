import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api } from '@/lib/api';

type CreditsContextType = {
  credits: number;
  refresh: () => Promise<void>;
  loading: boolean;
  error?: string;
};

const CreditsContext = createContext<CreditsContextType | undefined>(undefined);

export const CreditsProvider = ({ children }: { children: ReactNode }) => {
  const [credits, setCredits] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  const getCredits = async () => {
    setLoading(true);
    try {
      const response = await api.getCredits();
      setCredits(response?.data?.credits ?? 0);
      setError(undefined);
    } catch (err: unknown) {
      // normalize unknown error
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err ?? 'Failed to fetch credits'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getCredits();
    const id = setInterval(getCredits, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <CreditsContext.Provider value={{ credits: credits, refresh: getCredits, loading, error }}>
      {children}
    </CreditsContext.Provider>
  );
};

export const useCredits = (): CreditsContextType => {
  const ctx = useContext(CreditsContext);
  if (!ctx) throw new Error('useCredits must be used within a CreditsProvider');
  return ctx;
};
