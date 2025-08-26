/**
 * HTTP Interceptor for automatic JWT token management
 * Handles token refresh and automatic retries for 401 responses
 */

interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  user_id: string;
}

interface InterceptorConfig {
  tokenStorageKey: string;
  refreshEndpoint: string;
  maxRetries: number;
  excludeUrls: string[];
}

class HTTPInterceptor {
  private config: InterceptorConfig;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }> = [];

  constructor(config: Partial<InterceptorConfig> = {}) {
    this.config = {
      tokenStorageKey: 'grantha-tokens',
      refreshEndpoint: '/auth/v2/refresh',
      maxRetries: 1,
      excludeUrls: [
        '/auth/login', '/auth/refresh', '/auth/status', '/health',
        '/auth/v2/login', '/auth/v2/refresh', '/auth/v2/status', '/auth/v2/register'
      ],
      ...config
    };

    // Only intercept fetch on the client side (browser)
    if (typeof window !== 'undefined') {
      this.interceptFetch();
    }
  }

  private interceptFetch(): void {
    const originalFetch = window.fetch;
    
    window.fetch = async (input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> => {
      // Check if this URL should be excluded from token handling
      const url = typeof input === 'string' ? input : input.toString();
      
      if (this.shouldExcludeUrl(url)) {
        return originalFetch(input, init);
      }

      // Add token to headers if available
      const modifiedInit = await this.addTokenToRequest(init);
      
      // Make the request
      let response = await originalFetch(input, modifiedInit);
      
      // Handle 401 responses by attempting token refresh
      if (response.status === 401 && !this.isRefreshing) {
        try {
          await this.refreshTokenAndRetry();
          
          // Retry the original request with new token
          const retryInit = await this.addTokenToRequest(init);
          response = await originalFetch(input, retryInit);
        } catch (error) {
          // If refresh fails, clear tokens and redirect to login
          this.handleAuthFailure();
          throw error;
        }
      }

      return response;
    };
  }

  private shouldExcludeUrl(url: string): boolean {
    return this.config.excludeUrls.some(excludeUrl => 
      url.includes(excludeUrl) || url.endsWith(excludeUrl)
    );
  }

  private async addTokenToRequest(init: RequestInit): Promise<RequestInit> {
    const tokens = this.getStoredTokens();
    
    if (tokens?.access_token) {
      const headers = new Headers(init.headers);
      headers.set('Authorization', `Bearer ${tokens.access_token}`);
      
      return {
        ...init,
        headers
      };
    }
    
    return init;
  }

  private getStoredTokens(): TokenData | null {
    if (typeof window === 'undefined') {
      return null;
    }
    try {
      const stored = localStorage.getItem(this.config.tokenStorageKey);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to parse stored tokens:', error);
      return null;
    }
  }

  private storeTokens(tokens: TokenData): void {
    if (typeof window === 'undefined') {
      return;
    }
    try {
      localStorage.setItem(this.config.tokenStorageKey, JSON.stringify(tokens));
    } catch (error) {
      console.error('Failed to store tokens:', error);
    }
  }

  private clearTokens(): void {
    if (typeof window === 'undefined') {
      return;
    }
    localStorage.removeItem(this.config.tokenStorageKey);
    // Also clear legacy auth code storage
    localStorage.removeItem('grantha-auth-code');
  }

  private isTokenExpired(expiresAt: number): boolean {
    // Add 30 second buffer to prevent edge cases
    return Date.now() >= (expiresAt * 1000) - 30000;
  }

  private async refreshTokenAndRetry(): Promise<void> {
    if (this.isRefreshing) {
      // If already refreshing, wait for the current refresh to complete
      return new Promise((resolve, reject) => {
        this.failedQueue.push({ resolve, reject });
      });
    }

    this.isRefreshing = true;

    try {
      const tokens = this.getStoredTokens();
      
      if (!tokens?.refresh_token) {
        throw new Error('No refresh token available');
      }

      // Try v2 refresh endpoint first, fallback to v1
      let response = await fetch(this.config.refreshEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          refresh_token: tokens.refresh_token
        })
      });

      // Fallback to v1 API if v2 fails
      if (!response.ok && response.status === 404) {
        response = await fetch('/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            refresh_token: tokens.refresh_token
          })
        });
      }

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.status}`);
      }

      const refreshResult = await response.json();
      
      // Update stored tokens
      const updatedTokens: TokenData = {
        ...tokens,
        access_token: refreshResult.access_token,
        expires_at: Math.floor(Date.now() / 1000) + refreshResult.expires_in
      };
      
      this.storeTokens(updatedTokens);
      
      // Resolve all queued requests
      this.failedQueue.forEach(({ resolve }) => resolve());
      this.failedQueue = [];
      
    } catch (error) {
      // Reject all queued requests
      this.failedQueue.forEach(({ reject }) => reject(error));
      this.failedQueue = [];
      
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  private handleAuthFailure(): void {
    this.clearTokens();
    
    // Dispatch custom event for auth failure
    window.dispatchEvent(new CustomEvent('auth:failure', {
      detail: { reason: 'token_refresh_failed' }
    }));
    
    // Redirect to login page if not already there
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  // Public methods for manual token management
  public async checkAndRefreshToken(): Promise<boolean> {
    const tokens = this.getStoredTokens();
    
    if (!tokens) {
      return false;
    }
    
    if (this.isTokenExpired(tokens.expires_at)) {
      try {
        await this.refreshTokenAndRetry();
        return true;
      } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
      }
    }
    
    return true; // Token is still valid
  }

  public getCurrentToken(): string | null {
    const tokens = this.getStoredTokens();
    
    // Check if token is expired
    if (tokens && this.isTokenExpired(tokens.expires_at)) {
      return null;
    }
    
    return tokens?.access_token || null;
  }

  public setTokens(tokens: TokenData): void {
    this.storeTokens(tokens);
  }

  public clearAllTokens(): void {
    this.clearTokens();
  }
}

// Create and export singleton instance
export const httpInterceptor = new HTTPInterceptor();