# Login Page Setup and Usage

## Overview

The Grantha frontend now includes a modern, responsive login page at `/login` that integrates with the backend API authentication system.

## Features

✅ **Modern Design**
- Clean, responsive layout with light/dark mode support
- Smooth animations and transitions
- Mobile-friendly design with proper accessibility

✅ **Dual Authentication Methods**
- Traditional username/password credentials
- Authorization code authentication (integrates with existing backend)
- Easy toggle between methods

✅ **Enhanced UX**
- Real-time form validation with debounced feedback
- Password visibility toggle
- Loading states and error handling
- Auto-redirect after successful login
- Remembers intended destination before login redirect

✅ **Security & Validation**
- Input sanitization
- Comprehensive form validation
- Proper autocomplete attributes
- ARIA accessibility labels

## Authentication Flow

### Method 1: Authorization Code (Default Backend)
1. User enters authorization code
2. Frontend calls `/auth/validate` with the code
3. On success, user is authenticated and redirected

### Method 2: Username/Password (Demo Implementation)
1. User enters username/email and password
2. System attempts authentication using password as auth code
3. Falls back to combined credentials as auth code if needed
4. On success, user is authenticated and redirected

## File Structure

```
src/routes/login/
├── +layout.svelte          # Login-specific layout (no app chrome)
└── +page.svelte           # Main login page component

src/lib/utils/
└── validation.ts          # Form validation utilities

src/lib/stores/
└── auth.ts               # Updated with redirect handling

src/lib/components/auth/
└── AuthGuard.svelte      # Updated to redirect to login
```

## Integration Points

### Authentication Store (`src/lib/stores/auth.ts`)
- Handles login state management
- Manages redirect paths for post-login navigation
- Integrates with existing `/auth/validate` endpoint

### Layout System
- Main layout detects login page and skips app chrome
- Login page has standalone layout without header/sidebar
- Seamless transition between authenticated/unauthenticated states

### API Client (`src/lib/api/client.ts`)
- Works with existing `/auth/validate` endpoint
- Maintains compatibility with current backend implementation

## Usage

### For Users
1. Navigate to any protected route
2. Automatically redirected to `/login`
3. Choose authentication method (credentials or auth code)
4. Enter credentials and submit
5. On success, redirected to intended destination or dashboard

### For Developers

#### Customizing Validation
```typescript
// Add custom validation rules in validation.ts
export const customValidationRules: ValidationRules = {
  customField: [
    validationRules.required('Custom field is required'),
    validationRules.minLength(5, 'Must be at least 5 characters'),
  ],
};
```

#### Adding New Authentication Methods
```typescript
// In login page component
let loginMethod: 'credentials' | 'code' | 'sso' = 'credentials';

// Add new case in handleSubmit()
if (loginMethod === 'sso') {
  // Handle SSO authentication
}
```

## Backend Integration

The login page is designed to work with the current backend `/auth/validate` endpoint:

```typescript
// Current API call
await apiClient.validateAuthCode({ code: authCode });
```

To fully implement username/password authentication, the backend would need:

1. **New endpoint**: `POST /auth/login`
   ```json
   {
     "username": "user@example.com",
     "password": "securepassword"
   }
   ```

2. **Response format**:
   ```json
   {
     "success": true,
     "token": "jwt_token_here",
     "user": {
       "id": "user_id",
       "username": "username",
       "email": "user@example.com"
     }
   }
   ```

## Customization

### Styling
The login page uses Tailwind CSS with the existing theme system:
- Light/dark mode support via CSS custom properties
- Consistent with app design system
- Mobile-responsive breakpoints

### Branding
Update branding elements in the login page:
- Logo/icon (currently uses Shield icon)
- Colors via Tailwind theme
- Copy/messaging

### Validation Rules
Customize validation in `src/lib/utils/validation.ts`:
- Password strength requirements
- Username format rules
- Custom error messages

## Security Considerations

- All inputs are sanitized before processing
- Password fields use appropriate input types
- Autocomplete attributes follow security best practices
- Form validation prevents common injection attempts
- Secure redirect handling prevents open redirect vulnerabilities

## Accessibility

- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatible
- High contrast color ratios
- Focus management

## Browser Support

- Modern browsers (ES2020+)
- Mobile browsers
- Progressive enhancement for older browsers
- Graceful fallbacks for disabled JavaScript