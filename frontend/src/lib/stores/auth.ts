/**
 * Authentication Store
 * Manages JWT-based user authentication state and token management
 */

import { writable, derived, get } from "svelte/store";
import { browser } from "$app/environment";
import { apiClient } from "$lib/api/client.js";
import type { AuthStatus, AuthValidationResponse } from "$lib/types/api.js";

interface AuthState {
  isAuthenticated: boolean;
  authRequired: boolean;
  isLoading: boolean;
  error: string | null;
  redirectTo?: string;
  user: {
    id: string;
    username: string;
  } | null;
}

interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_at: number; // Timestamp when access token expires
  user_id: string;
}

// Initialize auth state
const initialState: AuthState = {
  isAuthenticated: false,
  authRequired: false,
  isLoading: false,
  error: null,
  redirectTo: undefined,
  user: null,
};

// Create writable stores
export const authState = writable<AuthState>(initialState);
export const authCode = writable<string>("");  // Keep for backward compatibility

// Derived store for computed values
export const canAccessApp = derived(
  authState,
  ($authState) => !$authState.authRequired || $authState.isAuthenticated,
);

export const isAuthLoading = derived(
  authState,
  ($authState) => $authState.isLoading,
);

// Token management utilities
const TOKEN_STORAGE_KEY = "grantha-tokens";
const LEGACY_AUTH_CODE_KEY = "grantha-auth-code";

function getStoredTokens(): TokenData | null {
  if (!browser) return null;
  
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!stored) return null;
    
    return JSON.parse(stored);
  } catch (error) {
    console.error("Failed to parse stored tokens:", error);
    return null;
  }
}

function storeTokens(tokens: TokenData): void {
  if (!browser) return;
  
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
  } catch (error) {
    console.error("Failed to store tokens:", error);
  }
}

function clearStoredTokens(): void {
  if (!browser) return;
  
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(LEGACY_AUTH_CODE_KEY);  // Clean up legacy storage
}

function isTokenExpired(expiresAt: number): boolean {
  return Date.now() >= expiresAt * 1000;  // Convert to milliseconds
}

/**
 * Authentication actions
 */
export const authActions = {
  // Check authentication status and validate stored tokens
  async checkAuthStatus(): Promise<void> {
    if (!browser) return;

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const status: AuthStatus = await apiClient.getAuthStatus();
      let isAuthenticated = false;
      let user = null;

      // First check for JWT tokens
      const storedTokens = getStoredTokens();
      
      if (status.auth_required && storedTokens) {
        // Check if access token is expired
        if (isTokenExpired(storedTokens.expires_at)) {
          try {
            // Try to refresh the token
            const refreshed = await authActions.refreshToken();
            if (refreshed) {
              isAuthenticated = true;
              user = {
                id: storedTokens.user_id,
                username: storedTokens.user_id
              };
            } else {
              clearStoredTokens();
            }
          } catch (error) {
            console.error("Token refresh failed:", error);
            clearStoredTokens();
          }
        } else {
          // Token is still valid
          isAuthenticated = true;
          user = {
            id: storedTokens.user_id,
            username: storedTokens.user_id
          };
          
          // Update API client with the token
          apiClient.setToken(storedTokens.access_token);
        }
      } else if (!status.auth_required) {
        // If auth not required, create anonymous session
        try {
          await authActions.loginAnonymous();
          isAuthenticated = true;
        } catch (error) {
          console.error("Anonymous login failed:", error);
        }
      } else {
        // Fallback: Check for legacy auth code
        const storedCode = localStorage.getItem(LEGACY_AUTH_CODE_KEY);
        if (storedCode) {
          try {
            const validationResult = await apiClient.validateAuthCode({
              code: storedCode,
            });
            if (validationResult.success) {
              // Convert legacy auth to JWT
              await authActions.loginWithCode(storedCode);
              isAuthenticated = true;
            } else {
              localStorage.removeItem(LEGACY_AUTH_CODE_KEY);
            }
          } catch (error) {
            localStorage.removeItem(LEGACY_AUTH_CODE_KEY);
            console.error("Legacy auth validation failed:", error);
          }
        }
      }

      authState.update((state) => ({
        ...state,
        authRequired: status.auth_required,
        isAuthenticated,
        user,
        isLoading: false,
        error: null,
      }));
    } catch (error) {
      console.error("Auth status check failed:", error);
      authState.update((state) => ({
        ...state,
        isLoading: false,
        error:
          error instanceof Error
            ? error.message
            : "Authentication check failed",
      }));
    }
  },

  // Login with username/password
  async login(username: string, password: string, rememberMe: boolean = false): Promise<boolean> {
    if (!browser) return false;

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username,
          password,
          remember_me: rememberMe
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `Login failed: ${response.status}`);
      }

      const loginResult = await response.json();
      
      // Store tokens
      const tokenData: TokenData = {
        access_token: loginResult.access_token,
        refresh_token: loginResult.refresh_token,
        expires_at: Math.floor(Date.now() / 1000) + loginResult.expires_in,
        user_id: loginResult.user_id
      };
      
      storeTokens(tokenData);
      apiClient.setToken(loginResult.access_token);

      authState.update((state) => ({
        ...state,
        isAuthenticated: true,
        user: {
          id: loginResult.user_id,
          username: username
        },
        isLoading: false,
        error: null,
      }));

      return true;
    } catch (error) {
      console.error("Login failed:", error);
      authState.update((state) => ({
        ...state,
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: error instanceof Error ? error.message : "Login failed",
      }));

      return false;
    }
  },

  // Login with auth code (for backward compatibility)
  async loginWithCode(code: string): Promise<boolean> {
    return await authActions.login("user", code, false);
  },

  // Anonymous login (when auth not required)
  async loginAnonymous(): Promise<boolean> {
    return await authActions.login("anonymous", "anonymous", false);
  },

  // Validate authentication code (legacy method)
  async validateCode(code: string): Promise<boolean> {
    return await authActions.loginWithCode(code);
  },

  // Refresh access token
  async refreshToken(): Promise<boolean> {
    if (!browser) return false;

    const storedTokens = getStoredTokens();
    if (!storedTokens?.refresh_token) {
      return false;
    }

    try {
      const response = await fetch("/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          refresh_token: storedTokens.refresh_token
        })
      });

      if (!response.ok) {
        return false;
      }

      const refreshResult = await response.json();
      
      // Update stored tokens
      const updatedTokens: TokenData = {
        ...storedTokens,
        access_token: refreshResult.access_token,
        expires_at: Math.floor(Date.now() / 1000) + refreshResult.expires_in
      };
      
      storeTokens(updatedTokens);
      apiClient.setToken(refreshResult.access_token);

      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      return false;
    }
  },

  // Logout
  async logout(revokeAll: boolean = false): Promise<void> {
    if (!browser) return;

    const storedTokens = getStoredTokens();
    
    try {
      // Call logout endpoint to revoke tokens on server
      if (storedTokens) {
        await fetch("/auth/logout", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${storedTokens.access_token}`
          },
          body: JSON.stringify({
            refresh_token: storedTokens.refresh_token,
            revoke_all: revokeAll
          })
        });
      }
    } catch (error) {
      console.error("Logout API call failed:", error);
      // Continue with client-side cleanup even if server call fails
    }

    // Clear stored tokens and update state
    clearStoredTokens();
    apiClient.clearToken();
    authCode.set("");

    authState.update((state) => ({
      ...state,
      isAuthenticated: false,
      user: null,
      error: null,
      redirectTo: undefined,
    }));

    // Redirect to login page
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  },

  // Clear error
  clearError(): void {
    authState.update((state) => ({ ...state, error: null }));
  },

  // Set redirect path for post-login navigation
  setRedirectPath(path: string): void {
    authState.update((state) => ({ ...state, redirectTo: path }));
  },

  // Get and clear redirect path
  getAndClearRedirectPath(): string | undefined {
    const currentState = get(authState);
    const redirectTo = currentState.redirectTo;
    if (redirectTo) {
      authState.update((state) => ({ ...state, redirectTo: undefined }));
    }
    return redirectTo;
  },
};

// Auto-check auth status on store initialization
if (browser) {
  authActions.checkAuthStatus();
}
