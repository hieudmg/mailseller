import { PoolSize, Tier, TransactionsResponse, ApiResponse, InvoiceResponse } from '@/types/api';

class ApiClient {
  private baseUrl = '/api';

  private async request<T>(
    endpoint: string,
    options?: RequestInit,
    errorMessage: string = 'Request failed',
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        credentials: 'include',
        ...options,
        headers: {
          ...options?.headers,
        },
      });

      if (!response.ok) {
        return { error: errorMessage };
      }

      if (response.status === 204 || options?.method === 'POST') {
        const text = await response.text();
        return { data: (text ? JSON.parse(text) : undefined) as T };
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return { error: 'Network error' };
    }
  }

  async login(email: string, password: string): Promise<ApiResponse<void>> {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    return this.request(
      '/account/login',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      },
      'Invalid email or password',
    );
  }

  async register(email: string, password: string): Promise<ApiResponse<void>> {
    return this.request(
      '/account/register',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      },
      'Registration failed. Please try again.',
    );
  }

  async logout(): Promise<ApiResponse<void>> {
    return this.request('/account/logout', { method: 'POST' }, 'Logout failed');
  }

  async getCurrentUser(): Promise<ApiResponse<{ email: string; id: number }>> {
    return this.request('/account/me');
  }

  async getPoolSize(): Promise<ApiResponse<{ total: number; sizes: PoolSize }>> {
    return this.request(`/datapool/size`);
  }

  async getDataTypes(): Promise<ApiResponse<{ types: string[] }>> {
    return this.request('/datapool/types');
  }

  async getToken(): Promise<ApiResponse<{ token: string }>> {
    return this.request('/token');
  }

  async rotateToken(): Promise<ApiResponse<{ token: string }>> {
    return this.request('/token/rotate', { method: 'POST' }, 'Token rotation failed');
  }

  async purchaseData(
    amount: number,
    type: string,
  ): Promise<ApiResponse<{ data: string[]; type: string; cost: number; credit_remaining: number }>> {
    // Get token first
    const tokenResponse = await this.getToken();
    if (!tokenResponse.data?.token) {
      return { error: 'Unable to get authentication token' };
    }

    const token = tokenResponse.data.token;

    // Build query string
    const params = new URLSearchParams({
      amount: amount.toString(),
      type: type,
      token: token,
    });

    return this.request(`/purchase?${params.toString()}`, undefined, 'Purchase failed');
  }

  async getCredits(): Promise<ApiResponse<{ credits: number }>> {
    return this.request('/credits', {
      headers: {
        Authorization: 'bearer ' + (await this.getToken().then((res) => res.data?.token || '')),
      },
    });
  }

  async getTier(): Promise<ApiResponse<Tier>> {
    return this.request('/tier');
  }

  async getTiers(): Promise<
    ApiResponse<{
      tiers: Array<{
        code: string;
        name: string;
        discount: number;
        threshold: number;
      }>;
    }>
  > {
    return this.request('/tiers');
  }

  async createInvoice(amount: number): Promise<ApiResponse<InvoiceResponse>> {
    return this.request(
      '/payment/invoice',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount }),
      },
      'Failed to create invoice',
    );
  }

  async getTransactions(options?: {
    page?: number;
    limit?: number;
    types?: string[];
  }): Promise<ApiResponse<TransactionsResponse>> {
    const params = new URLSearchParams();
    if (options?.page) params.append('page', options.page.toString());
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.types) {
      options.types.forEach((type) => params.append('types', type));
    }

    const queryString = params.toString();
    const endpoint = queryString ? `/transactions?${queryString}` : '/transactions';

    return this.request(endpoint);
  }
}

export const api = new ApiClient();
