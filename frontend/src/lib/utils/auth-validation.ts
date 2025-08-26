/**
 * Enhanced validation schemas for authentication forms
 */

export interface ValidationRule {
  test: (value: string, formData?: Record<string, any>) => boolean;
  message: string;
}

export interface ValidationSchema {
  [field: string]: ValidationRule[];
}

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
}

// Enhanced validation rules
export const authValidationRules = {
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
      return !value || emailRegex.test(value.trim());
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

  strongPassword: (message?: string): ValidationRule => ({
    test: (value) => {
      // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
      const strongPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
      return strongPasswordRegex.test(value);
    },
    message: message || 'Password must be at least 8 characters with uppercase, lowercase, and numbers',
  }),

  passwordComplexity: (message?: string): ValidationRule => ({
    test: (value) => {
      // More complex: at least 8 chars, 1 upper, 1 lower, 1 number, 1 special char
      const complexPasswordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&].{8,}$/;
      return complexPasswordRegex.test(value);
    },
    message: message || 'Password must contain uppercase, lowercase, numbers, and special characters',
  }),

  passwordMatch: (confirmField = 'confirmPassword', message = 'Passwords do not match'): ValidationRule => ({
    test: (value, formData) => {
      if (!formData) return false;
      return value === formData[confirmField];
    },
    message,
  }),

  notSameAsOther: (otherField: string, message?: string): ValidationRule => ({
    test: (value, formData) => {
      if (!formData) return true;
      return value !== formData[otherField];
    },
    message: message || `Must be different from ${otherField}`,
  }),

  authCode: (message = 'Authorization code must be alphanumeric'): ValidationRule => ({
    test: (value) => {
      const authCodeRegex = /^[a-zA-Z0-9\-_:.]+$/;
      return authCodeRegex.test(value.trim());
    },
    message,
  }),

  usernameOrEmail: (message = 'Please enter a valid username or email'): ValidationRule => ({
    test: (value) => {
      const trimmed = value.trim();
      if (!trimmed) return false;
      
      // Check if it's an email
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (emailRegex.test(trimmed)) return true;
      
      // Check if it's a valid username
      const usernameRegex = /^[a-zA-Z0-9_]{3,}$/;
      return usernameRegex.test(trimmed);
    },
    message,
  }),

  fullName: (message = 'Full name should only contain letters and spaces'): ValidationRule => ({
    test: (value) => {
      if (!value.trim()) return true; // Optional field
      const nameRegex = /^[a-zA-Z\s'-]+$/;
      return nameRegex.test(value.trim());
    },
    message,
  }),

  bio: (maxLength = 500, message?: string): ValidationRule => ({
    test: (value) => {
      return value.trim().length <= maxLength;
    },
    message: message || `Bio must be no more than ${maxLength} characters`,
  }),
};

// Validation schemas for different forms
export const loginSchema: ValidationSchema = {
  username: [
    authValidationRules.required('Username or email is required'),
    authValidationRules.usernameOrEmail(),
  ],
  password: [
    authValidationRules.required('Password is required'),
  ],
};

export const registrationSchema: ValidationSchema = {
  username: [
    authValidationRules.required('Username is required'),
    authValidationRules.minLength(3, 'Username must be at least 3 characters'),
    authValidationRules.maxLength(20, 'Username must be no more than 20 characters'),
    authValidationRules.username(),
  ],
  email: [
    authValidationRules.email(),
  ],
  fullName: [
    authValidationRules.fullName(),
  ],
  password: [
    authValidationRules.required('Password is required'),
    authValidationRules.strongPassword(),
  ],
  confirmPassword: [
    authValidationRules.required('Please confirm your password'),
    authValidationRules.passwordMatch('password'),
  ],
  bio: [
    authValidationRules.bio(),
  ],
};

export const changePasswordSchema: ValidationSchema = {
  currentPassword: [
    authValidationRules.required('Current password is required'),
  ],
  newPassword: [
    authValidationRules.required('New password is required'),
    authValidationRules.strongPassword(),
    authValidationRules.notSameAsOther('currentPassword', 'New password must be different from current password'),
  ],
  confirmNewPassword: [
    authValidationRules.required('Please confirm your new password'),
    authValidationRules.passwordMatch('newPassword'),
  ],
};

export const authCodeSchema: ValidationSchema = {
  authCode: [
    authValidationRules.required('Authorization code is required'),
    authValidationRules.authCode(),
  ],
};

/**
 * Enhanced form validation with warnings
 */
export function validateFormWithWarnings(
  formData: Record<string, any>,
  schema: ValidationSchema
): ValidationResult {
  const errors: Record<string, string> = {};
  const warnings: Record<string, string> = {};

  for (const [field, rules] of Object.entries(schema)) {
    const value = formData[field] || '';
    
    for (const rule of rules) {
      if (!rule.test(value, formData)) {
        errors[field] = rule.message;
        break; // Stop at first error for this field
      }
    }

    // Add field-specific warnings
    if (!errors[field]) {
      if (field === 'password' && value) {
        const strength = getPasswordStrength(value);
        if (strength.score < 4) {
          warnings[field] = `Password strength: ${strength.label}`;
        }
      }
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
    warnings,
  };
}

/**
 * Password strength calculator
 */
export function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
  suggestions: string[];
} {
  if (!password) return { score: 0, label: '', color: '', suggestions: [] };
  
  let score = 0;
  const suggestions: string[] = [];
  
  // Length check
  if (password.length >= 8) score += 1;
  else suggestions.push('At least 8 characters');
  
  // Lowercase check
  if (/[a-z]/.test(password)) score += 1;
  else suggestions.push('Include lowercase letters');
  
  // Uppercase check
  if (/[A-Z]/.test(password)) score += 1;
  else suggestions.push('Include uppercase letters');
  
  // Number check
  if (/\d/.test(password)) score += 1;
  else suggestions.push('Include numbers');
  
  // Special character check
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  else suggestions.push('Include special characters');
  
  const strengthMap = {
    0: { label: '', color: '', suggestions },
    1: { label: 'Very Weak', color: 'text-red-600', suggestions },
    2: { label: 'Weak', color: 'text-orange-600', suggestions },
    3: { label: 'Fair', color: 'text-yellow-600', suggestions },
    4: { label: 'Good', color: 'text-blue-600', suggestions },
    5: { label: 'Strong', color: 'text-green-600', suggestions: [] }
  };
  
  return { score, ...strengthMap[score as keyof typeof strengthMap] };
}

/**
 * Sanitize form input
 */
export function sanitizeFormInput(input: string, options: {
  maxLength?: number;
  allowHtml?: boolean;
  trimWhitespace?: boolean;
} = {}): string {
  const {
    maxLength = 255,
    allowHtml = false,
    trimWhitespace = true
  } = options;

  let sanitized = input;

  // Trim whitespace
  if (trimWhitespace) {
    sanitized = sanitized.trim();
  }

  // Remove HTML if not allowed
  if (!allowHtml) {
    sanitized = sanitized.replace(/[<>]/g, '');
  }

  // Limit length
  if (maxLength && sanitized.length > maxLength) {
    sanitized = sanitized.slice(0, maxLength);
  }

  return sanitized;
}

/**
 * Check if field should show error (after user interaction)
 */
export function shouldShowFieldError(
  fieldName: string,
  errors: Record<string, string>,
  touchedFields: Set<string>
): boolean {
  return touchedFields.has(fieldName) && !!errors[fieldName];
}

/**
 * Check if field should show warning
 */
export function shouldShowFieldWarning(
  fieldName: string,
  warnings: Record<string, string>,
  touchedFields: Set<string>
): boolean {
  return touchedFields.has(fieldName) && !!warnings[fieldName];
}

/**
 * Debounce function for validation
 */
export function createDebouncer<T extends (...args: any[]) => void>(
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
 * Format validation error message for display
 */
export function formatValidationError(error: string): string {
  if (!error) return '';
  
  // Capitalize first letter and ensure proper punctuation
  const formatted = error.charAt(0).toUpperCase() + error.slice(1);
  return formatted.endsWith('.') ? formatted : `${formatted}.`;
}

/**
 * Get appropriate autocomplete value for form fields
 */
export function getFieldAutocomplete(fieldName: string): string {
  const autocompleteMap: Record<string, string> = {
    username: 'username',
    email: 'email',
    password: 'current-password',
    newPassword: 'new-password',
    confirmPassword: 'new-password',
    confirmNewPassword: 'new-password',
    currentPassword: 'current-password',
    fullName: 'name',
    firstName: 'given-name',
    lastName: 'family-name',
    authCode: 'one-time-code',
  };

  return autocompleteMap[fieldName] || 'off';
}

/**
 * Check if form has any changes from original data
 */
export function hasFormChanges(
  currentData: Record<string, any>,
  originalData: Record<string, any>
): boolean {
  return JSON.stringify(currentData) !== JSON.stringify(originalData);
}

/**
 * Extract changed fields from form data
 */
export function getChangedFields(
  currentData: Record<string, any>,
  originalData: Record<string, any>
): Record<string, any> {
  const changes: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(currentData)) {
    if (value !== originalData[key]) {
      changes[key] = value;
    }
  }
  
  return changes;
}