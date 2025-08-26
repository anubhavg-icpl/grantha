/**
 * Authentication Store
 * Manages user authentication state and API key validation
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
}

// Initialize auth state
const initialState: AuthState = {
  isAuthenticated: false,
  authRequired: false,
  isLoading: false,
  error: null,
  redirectTo: undefined,
};

// Create writable stores
export const authState = writable<AuthState>(initialState);
export const authCode = writable<string>("");

// Derived store for computed values
export const canAccessApp = derived(
  authState,
  ($authState) => !$authState.authRequired || $authState.isAuthenticated,
);

export const isAuthLoading = derived(
  authState,
  ($authState) => $authState.isLoading,
);

/**
 * Authentication actions
 */
export const authActions = {
  // Check authentication status
  async checkAuthStatus(): Promise<void> {
    if (!browser) return;

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const status: AuthStatus = await apiClient.getAuthStatus();

      // Check if we have a stored valid auth code
      const storedCode = localStorage.getItem("grantha-auth-code");
      let isAuthenticated = false;

      if (status.auth_required && storedCode) {
        try {
          const validationResult = await apiClient.validateAuthCode({
            code: storedCode,
          });
          isAuthenticated = validationResult.success;
          if (isAuthenticated) {
            authCode.set(storedCode);
          } else {
            localStorage.removeItem("grantha-auth-code");
          }
        } catch (error) {
          localStorage.removeItem("grantha-auth-code");
          console.error("Auth validation failed:", error);
        }
      } else if (!status.auth_required) {
        isAuthenticated = true;
      }

      authState.update((state) => ({
        ...state,
        authRequired: status.auth_required,
        isAuthenticated,
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

  // Validate authentication code
  async validateCode(code: string): Promise<boolean> {
    if (!browser) return false;

    authState.update((state) => ({ ...state, isLoading: true, error: null }));

    try {
      const result: AuthValidationResponse = await apiClient.validateAuthCode({
        code,
      });

      if (result.success) {
        // Store the valid code
        localStorage.setItem("grantha-auth-code", code);
        authCode.set(code);

        authState.update((state) => ({
          ...state,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        }));

        return true;
      } else {
        authState.update((state) => ({
          ...state,
          isAuthenticated: false,
          isLoading: false,
          error: "Invalid authentication code",
        }));

        return false;
      }
    } catch (error) {
      console.error("Code validation failed:", error);
      authState.update((state) => ({
        ...state,
        isAuthenticated: false,
        isLoading: false,
        error: error instanceof Error ? error.message : "Validation failed",
      }));

      return false;
    }
  },

  // Logout
  logout(): void {
    if (!browser) return;

    localStorage.removeItem("grantha-auth-code");
    authCode.set("");

    authState.update((state) => ({
      ...state,
      isAuthenticated: false,
      error: null,
    }));
  },

  // Clear error
  clearError(): void {
    authState.update((state) => ({ ...state, error: null }));
  },
};

// Auto-check auth status on store initialization
if (browser) {
  authActions.checkAuthStatus();
}
