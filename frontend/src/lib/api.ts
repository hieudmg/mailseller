type ApiResponse<T> = {
  data?: T;
  error?: string;
};

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

  async getPoolSize(): Promise<ApiResponse<{ pool_size: number }>> {
    return this.request('/datapool/size');
  }

  async getToken(): Promise<ApiResponse<{ token: string }>> {
    return this.request('/token');
  }

  async rotateToken(): Promise<ApiResponse<{ token: string }>> {
    return this.request('/token/rotate', { method: 'POST' }, 'Token rotation failed');
  }

  async purchaseData(amount: number): Promise<ApiResponse<{ data: string[] }>> {
    return this.request(
      '/purchase',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'bearer ' + (await this.getToken().then((res) => res.data?.token || '')),
        },
        body: JSON.stringify({ amount }),
      },
      'Purchase failed',
    );
  }

  async getCredits(): Promise<ApiResponse<{ credits: number }>> {
    return this.request('/credits', {
      headers: {
        Authorization: 'bearer ' + (await this.getToken().then((res) => res.data?.token || '')),
      },
    });
  }
}

export const api = new ApiClient();
