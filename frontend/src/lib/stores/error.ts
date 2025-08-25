// Error handling store for global error management
import { writable } from 'svelte/store';

export interface AppError {
  id: string;
  message: string;
  type: 'error' | 'warning' | 'info' | 'success';
  timestamp: number;
  autoHide?: boolean;
  duration?: number;
}

const createErrorStore = () => {
  const { subscribe, set, update } = writable<AppError[]>([]);

  return {
    subscribe,
    
    // Add an error
    add: (message: string, type: AppError['type'] = 'error', options: Partial<AppError> = {}) => {
      const error: AppError = {
        id: `error_${Date.now()}_${Math.random().toString(36).slice(2)}`,
        message,
        type,
        timestamp: Date.now(),
        autoHide: type !== 'error',
        duration: 5000,
        ...options
      };

      update(errors => [...errors, error]);

      // Auto-hide non-error messages
      if (error.autoHide) {
        setTimeout(() => {
          update(errors => errors.filter(e => e.id !== error.id));
        }, error.duration);
      }

      return error.id;
    },

    // Remove an error
    remove: (id: string) => {
      update(errors => errors.filter(error => error.id !== id));
    },

    // Clear all errors
    clear: () => {
      set([]);
    },

    // Clear errors by type
    clearByType: (type: AppError['type']) => {
      update(errors => errors.filter(error => error.type !== type));
    }
  };
};

export const errorStore = createErrorStore();

// Convenience functions
export const showError = (message: string, options?: Partial<AppError>) => 
  errorStore.add(message, 'error', options);

export const showWarning = (message: string, options?: Partial<AppError>) => 
  errorStore.add(message, 'warning', options);

export const showInfo = (message: string, options?: Partial<AppError>) => 
  errorStore.add(message, 'info', options);

export const showSuccess = (message: string, options?: Partial<AppError>) => 
  errorStore.add(message, 'success', options);