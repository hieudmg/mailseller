export type ApiResponse<T> = {
  data?: T;
  error?: string;
};

export type Stock = {
  pool_size: number;
  price: number;
  name: string;
  lifetime: string;
};

export type PoolSize = {
  [type: string]: Stock;
};

export type Transaction = {
  id: number;
  amount: number;
  type: 'purchase' | 'admin_deposit' | string;
  description: string;
  data_id: number | string | null;
  timestamp: string; // ISO format
};

export type TransactionsResponse = {
  page: number;
  limit: number;
  total: number;
  type_filter: string[]; // same as `types`
  transactions: Transaction[];
};

export type Tier = {
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
  credits: number;
};

export type InvoiceResponse = {
  invoice_url: string;
  uuid: string;
  expires_at: number;
  order_id: string;
};
