import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api } from '@/lib/api';
import { PoolSize } from '@/types/api';

type StockContextType = {
  stock: PoolSize;
  refresh: () => Promise<void>;
  loading: boolean;
  error?: string;
};
const StockContext = createContext<StockContextType | undefined>(undefined);

export const StockProvider = ({ children }: { children: ReactNode }) => {
  const [stock, setStock] = useState<PoolSize>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | undefined>(undefined);

  const getPoolSize = async () => {
    setLoading(true);
    try {
      const response = await api.getPoolSize();
      setStock(response?.data?.sizes || {});
      setError(undefined);
    } catch (err: unknown) {
      // normalize unknown error
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(err ?? 'Failed to fetch pool size'));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getPoolSize();
    const id = setInterval(getPoolSize, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <StockContext.Provider value={{ stock, refresh: getPoolSize, loading, error }}>{children}</StockContext.Provider>
  );
};

export const useStock = (): StockContextType => {
  const ctx = useContext(StockContext);
  if (!ctx) throw new Error('useStock must be used within a StockProvider');
  return ctx;
};
