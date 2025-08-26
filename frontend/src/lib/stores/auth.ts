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
    email?: string;
    full_name?: string;
    is_verified?: boolean;
    is_superuser?: boolean;
    created_at?: string;
    last_login?: string;
  } | null;
  loginAttempts?: number;
  isAccountLocked?: boolean;
  sessionTimeout?: number;
  csrfToken?: string;
}

interface TokenData {
  access_token: string;
  refresh_token: string;
  expires_at: number; // Timestamp when access token expires
  user_id: string;
}

interface UserProfile {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  bio?: string;
  is_active?: boolean;
  is_verified?: boolean;
  is_superuser?: boolean;
  created_at?: string;
  last_login?: string;
}

interface SessionInfo {
  id: string;
  device_name?: string;
  ip_address?: string;
  user_agent?: string;
  last_activity: string;
  is_current: boolean;
}

// Initialize auth state
const initialState: AuthState = {
  isAuthenticated: false,
  authRequired: false,
  isLoading: false,
  error: null,
  redirectTo: undefined,
  user: null,
  loginAttempts: 0,
  isAccountLocked: false,
  sessionTimeout: undefined,
  csrfToken: undefined,
};

// Create writable stores
export const authState = writable<AuthState>(initialState);
export const authCode = writable<string>("");  // Keep for backward compatibility
export const userSessions = writable<SessionInfo[]>([]);

// Derived store for computed values
export const canAccessApp = derived(
  authState,
  ($authState) => !$authState.authRequired || $authState.isAuthenticated,
);

export const isAuthLoading = derived(
  authState,
  ($authState) => $authState.isLoading,
);

export const currentUser = derived(
  authState,
  ($authState) => $authState.user,
);

export const isAccountLocked = derived(
  authState,
  ($authState) => $authState.isAccountLocked || false,
);

export const loginAttempts = derived(
  authState,
  ($authState) => $authState.loginAttempts || 0,
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

  // Login with username/password (v2 API)
  async login(username: string, password: string, rememberMe: boolean = false): Promise<boolean> {
    if (!browser) return false;

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      // Try v2 API first
      let response = await fetch("/auth/v2/login", {
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

      // Fallback to v1 API if v2 fails
      if (!response.ok && response.status === 404) {
        response = await fetch("/auth/login", {
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
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        // Handle account lockout
        if (response.status === 423) {
          authState.update((state) => ({ 
            ...state, 
            isAccountLocked: true,
            loginAttempts: 0,
            isLoading: false,
            error: errorData.detail || "Account temporarily locked due to multiple failed attempts"
          }));
          return false;
        }
        
        // Track login attempts
        if (response.status === 401) {
          authState.update((state) => ({ 
            ...state, 
            loginAttempts: (state.loginAttempts || 0) + 1,
            isLoading: false,
            error: errorData.detail || "Invalid credentials"
          }));
          return false;
        }
        
        throw new Error(errorData.detail || errorData.message || `Login failed: ${response.status}`);
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

      // Enhanced user data from v2 API
      const userData = {
        id: loginResult.user_id,
        username: loginResult.username || username,
        email: loginResult.email,
        full_name: loginResult.full_name,
        is_verified: loginResult.is_verified,
        is_superuser: loginResult.is_superuser
      };

      authState.update((state) => ({
        ...state,
        isAuthenticated: true,
        user: userData,
        isLoading: false,
        error: null,
        loginAttempts: 0,
        isAccountLocked: false,
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

  // Refresh access token (v2 API with fallback)
  async refreshToken(): Promise<boolean> {
    if (!browser) return false;

    const storedTokens = getStoredTokens();
    if (!storedTokens?.refresh_token) {
      return false;
    }

    try {
      // Try v2 API first
      let response = await fetch("/auth/v2/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          refresh_token: storedTokens.refresh_token
        })
      });

      // Fallback to v1 API if v2 fails
      if (!response.ok && response.status === 404) {
        response = await fetch("/auth/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            refresh_token: storedTokens.refresh_token
          })
        });
      }

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

  // Logout (v2 API with fallback)
  async logout(revokeAll: boolean = false): Promise<void> {
    if (!browser) return;

    const storedTokens = getStoredTokens();
    
    try {
      // Call logout endpoint to revoke tokens on server
      if (storedTokens) {
        // Try v2 API first
        let response = await fetch("/auth/v2/logout", {
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

        // Fallback to v1 API if v2 fails
        if (!response.ok && response.status === 404) {
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
      }
    } catch (error) {
      console.error("Logout API call failed:", error);
      // Continue with client-side cleanup even if server call fails
    }

    // Clear stored tokens and update state
    clearStoredTokens();
    apiClient.clearToken();
    authCode.set("");
    userSessions.set([]);

    authState.update((state) => ({
      ...state,
      isAuthenticated: false,
      user: null,
      error: null,
      redirectTo: undefined,
      loginAttempts: 0,
      isAccountLocked: false,
      sessionTimeout: undefined,
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

  // Register new user (v2 API only)
  async register(userData: {
    username: string;
    password: string;
    email?: string;
    full_name?: string;
    bio?: string;
  }): Promise<{success: boolean; user?: UserProfile; error?: string}> {
    if (!browser) return {success: false, error: "Not in browser environment"};

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response = await fetch("/auth/v2/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(userData)
      });

      const result = await response.json();

      if (!response.ok) {
        authState.update((state) => ({
          ...state,
          isLoading: false,
          error: result.detail || "Registration failed"
        }));
        return {success: false, error: result.detail || "Registration failed"};
      }

      authState.update((state) => ({ ...state, isLoading: false, error: null }));
      return {success: true, user: result};
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Registration failed";
      authState.update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage
      }));
      return {success: false, error: errorMessage};
    }
  },

  // Get current user profile (v2 API)
  async getCurrentUser(): Promise<UserProfile | null> {
    if (!browser) return null;

    const storedTokens = getStoredTokens();
    if (!storedTokens?.access_token) return null;

    try {
      const response = await fetch("/auth/v2/me", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${storedTokens.access_token}`
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired, try to refresh
          const refreshed = await authActions.refreshToken();
          if (refreshed) {
            return await authActions.getCurrentUser();
          }
        }
        return null;
      }

      const userProfile = await response.json();
      
      // Update auth state with current user data
      authState.update((state) => ({
        ...state,
        user: {
          id: userProfile.id,
          username: userProfile.username,
          email: userProfile.email,
          full_name: userProfile.full_name,
          is_verified: userProfile.is_verified,
          is_superuser: userProfile.is_superuser,
          created_at: userProfile.created_at,
          last_login: userProfile.last_login
        }
      }));

      return userProfile;
    } catch (error) {
      console.error("Failed to get current user:", error);
      return null;
    }
  },

  // Update user profile (v2 API)
  async updateUserProfile(updates: Partial<UserProfile>): Promise<{success: boolean; user?: UserProfile; error?: string}> {
    if (!browser) return {success: false, error: "Not in browser environment"};

    const storedTokens = getStoredTokens();
    if (!storedTokens?.access_token) {
      return {success: false, error: "Not authenticated"};
    }

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response = await fetch("/auth/v2/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${storedTokens.access_token}`
        },
        body: JSON.stringify(updates)
      });

      const result = await response.json();

      if (!response.ok) {
        authState.update((state) => ({
          ...state,
          isLoading: false,
          error: result.detail || "Update failed"
        }));
        return {success: false, error: result.detail || "Update failed"};
      }

      // Update auth state with new user data
      authState.update((state) => ({
        ...state,
        isLoading: false,
        error: null,
        user: {
          ...state.user,
          ...result
        }
      }));

      return {success: true, user: result};
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Update failed";
      authState.update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage
      }));
      return {success: false, error: errorMessage};
    }
  },

  // Change password (v2 API)
  async changePassword(currentPassword: string, newPassword: string): Promise<{success: boolean; error?: string}> {
    if (!browser) return {success: false, error: "Not in browser environment"};

    const storedTokens = getStoredTokens();
    if (!storedTokens?.access_token) {
      return {success: false, error: "Not authenticated"};
    }

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const response = await fetch("/auth/v2/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${storedTokens.access_token}`
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const result = await response.json();

      if (!response.ok) {
        authState.update((state) => ({
          ...state,
          isLoading: false,
          error: result.detail || "Password change failed"
        }));
        return {success: false, error: result.detail || "Password change failed"};
      }

      // Password changed successfully, all sessions logged out
      authState.update((state) => ({ ...state, isLoading: false, error: null }));
      
      // Clear tokens and redirect to login
      setTimeout(() => {
        authActions.logout(false);
      }, 1000);

      return {success: true};
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Password change failed";
      authState.update((state) => ({
        ...state,
        isLoading: false,
        error: errorMessage
      }));
      return {success: false, error: errorMessage};
    }
  },

  // Get user sessions (v2 API)
  async getUserSessions(): Promise<SessionInfo[]> {
    if (!browser) return [];

    const storedTokens = getStoredTokens();
    if (!storedTokens?.access_token) return [];

    try {
      const response = await fetch("/auth/v2/sessions", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${storedTokens.access_token}`
        }
      });

      if (!response.ok) return [];

      const result = await response.json();
      const sessions = result.sessions || [];
      
      userSessions.set(sessions);
      return sessions;
    } catch (error) {
      console.error("Failed to get user sessions:", error);
      return [];
    }
  },

  // Revoke session (v2 API)
  async revokeSession(sessionId: string): Promise<{success: boolean; error?: string}> {
    if (!browser) return {success: false, error: "Not in browser environment"};

    const storedTokens = getStoredTokens();
    if (!storedTokens?.access_token) {
      return {success: false, error: "Not authenticated"};
    }

    try {
      const response = await fetch(`/auth/v2/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${storedTokens.access_token}`
        }
      });

      if (!response.ok) {
        const result = await response.json().catch(() => ({}));
        return {success: false, error: result.detail || "Failed to revoke session"};
      }

      // Refresh sessions list
      await authActions.getUserSessions();
      return {success: true};
    } catch (error) {
      return {success: false, error: error instanceof Error ? error.message : "Failed to revoke session"};
    }
  },

  // Clear account lockout (for UI)
  clearAccountLockout(): void {
    authState.update((state) => ({
      ...state,
      isAccountLocked: false,
      loginAttempts: 0,
      error: null
    }));
  },
};

// Auto-check auth status on store initialization
if (browser) {
  authActions.checkAuthStatus();
}
