/**
 * Form validation utilities
 */

export interface ValidationRule {
  test: (value: string) => boolean;
  message: string;
}

export interface ValidationRules {
  [field: string]: ValidationRule[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

// Common validation rules
export const validationRules = {
  required: (message = 'This field is required'): ValidationRule => ({
    test: (value) => value.trim().length > 0,
    message,
  }),

  minLength: (min: number, message?: string): ValidationRule => ({
    test: (value) => value.trim().length >= min,
    message: message || `Must be at least ${min} characters`,
  }),

  maxLength: (max: number, message?: string): ValidationRule => ({
    test: (value) => value.trim().length <= max,
    message: message || `Must be no more than ${max} characters`,
  }),

  email: (message = 'Please enter a valid email address'): ValidationRule => ({
    test: (value) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(value.trim());
    },
    message,
  }),

  username: (message = 'Username must contain only letters, numbers, and underscores'): ValidationRule => ({
    test: (value) => {
      const usernameRegex = /^[a-zA-Z0-9_]+$/;
      return usernameRegex.test(value.trim());
    },
    message,
  }),

  strongPassword: (message = 'Password must contain at least 8 characters with uppercase, lowercase, and numbers'): ValidationRule => ({
    test: (value) => {
      const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
      return strongPasswordRegex.test(value);
    },
    message,
  }),

  authCode: (message = 'Authorization code must be alphanumeric'): ValidationRule => ({
    test: (value) => {
      const authCodeRegex = /^[a-zA-Z0-9\-_:.]+$/;
      return authCodeRegex.test(value.trim());
    },
    message,
  }),
};

/**
 * Validates form data against defined rules
 */
export function validateForm(
  formData: Record<string, string>, 
  rules: ValidationRules
): ValidationResult {
  const errors: Record<string, string> = {};

  for (const [field, fieldRules] of Object.entries(rules)) {
    const value = formData[field] || '';
    
    for (const rule of fieldRules) {
      if (!rule.test(value)) {
        errors[field] = rule.message;
        break; // Stop at first error for this field
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Sanitizes input string by trimming whitespace and removing potentially harmful characters
 */
export function sanitizeInput(input: string): string {
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove basic HTML characters
    .slice(0, 255); // Limit length
}

/**
 * Checks if a field should show an error (after user interaction)
 */
export function shouldShowError(
  fieldName: string,
  errors: Record<string, string>,
  touchedFields: Set<string>
): boolean {
  return touchedFields.has(fieldName) && !!errors[fieldName];
}

/**
 * Debounce function for validation
 */
export function debounce<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T {
  let timeoutId: NodeJS.Timeout;
  
  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  }) as T;
}

/**
 * Gets appropriate input type based on field name
 */
export function getInputType(fieldName: string): string {
  const typeMap: Record<string, string> = {
    email: 'email',
    password: 'password',
    authCode: 'password',
    confirmPassword: 'password',
    url: 'url',
    phone: 'tel',
  };

  return typeMap[fieldName] || 'text';
}

/**
 * Gets appropriate autocomplete value based on field name
 */
export function getAutocomplete(fieldName: string): string {
  const autocompleteMap: Record<string, string> = {
    email: 'email',
    username: 'username',
    password: 'current-password',
    newPassword: 'new-password',
    confirmPassword: 'new-password',
    firstName: 'given-name',
    lastName: 'family-name',
    fullName: 'name',
  };

  return autocompleteMap[fieldName] || 'off';
}

/**
 * Formats error message for display
 */
export function formatErrorMessage(error: string): string {
  if (!error) return '';
  
  // Capitalize first letter and ensure proper punctuation
  const formatted = error.charAt(0).toUpperCase() + error.slice(1);
  return formatted.endsWith('.') ? formatted : `${formatted}.`;
}

/**
 * Login-specific validation rules
 */
export const loginValidationRules: ValidationRules = {
  username: [
    validationRules.required('Username is required'),
    validationRules.minLength(3, 'Username must be at least 3 characters'),
  ],
  email: [
    validationRules.required('Email is required'),
    validationRules.email(),
  ],
  password: [
    validationRules.required('Password is required'),
    validationRules.minLength(3, 'Password must be at least 3 characters'),
  ],
  authCode: [
    validationRules.required('Authorization code is required'),
    validationRules.authCode(),
  ],
};

/**
 * Registration-specific validation rules
 */
export const registrationValidationRules: ValidationRules = {
  username: [
    validationRules.required('Username is required'),
    validationRules.minLength(3, 'Username must be at least 3 characters'),
    validationRules.maxLength(20, 'Username must be no more than 20 characters'),
    validationRules.username(),
  ],
  email: [
    validationRules.required('Email is required'),
    validationRules.email(),
  ],
  password: [
    validationRules.required('Password is required'),
    validationRules.strongPassword(),
  ],
  confirmPassword: [
    validationRules.required('Please confirm your password'),
  ],
};