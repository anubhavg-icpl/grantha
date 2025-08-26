<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authState, authActions, canAccessApp, isAccountLocked, loginAttempts } from '$stores/auth';
  import Button from '$lib/components/ui/button.svelte';
  import Input from '$lib/components/ui/input.svelte';
  import ThemeToggle from '$lib/components/ThemeToggle.svelte';
  import RegistrationForm from '$lib/components/auth/RegistrationForm.svelte';
  import { 
    validateForm, 
    loginValidationRules, 
    sanitizeInput,
    shouldShowError,
    debounce,
    getAutocomplete
  } from '$lib/utils/validation';
  import { 
    Lock, 
    Shield, 
    Key, 
    Mail, 
    User, 
    Eye, 
    EyeOff, 
    ArrowRight,
    CheckCircle,
    AlertCircle,
    UserPlus,
    AlertTriangle
  } from 'lucide-svelte';

  // Form states
  let currentView = $state<'login' | 'register' | 'forgot-password'>('login');
  let loginMethod = $state<'credentials' | 'code'>('credentials');
  let formData = $state({
    username: '',
    email: '',
    password: '',
    authCode: ''
  });
  
  let showPassword = $state(false);
  let isLoading = $state(false);
  let formError = $state('');
  let validationErrors = $state<Record<string, string>>({});
  let touchedFields = $state(new Set<string>());
  let showSuccess = $state(false);
  let registrationSuccess = $state(false);

  // Check if user is already authenticated
  onMount(() => {
    if ($canAccessApp) {
      goto('/');
    }
  });

  // Redirect on successful authentication
  $effect(() => {
    if ($canAccessApp) {
      const redirectTo = authActions.getAndClearRedirectPath() || '/';
      goto(redirectTo);
    }
  });

  function validateFormData(): boolean {
    if (loginMethod === 'credentials') {
      // For credentials mode, validate username and password
      const rules = {
        username: loginValidationRules.username,
        password: loginValidationRules.password,
      };

      // Use username field for either username or email input
      const dataToValidate = {
        username: formData.username || formData.email,
        password: formData.password,
      };

      const result = validateForm(dataToValidate, rules);
      validationErrors = result.errors;
      
      // Map username error back to identity if needed
      if (result.errors.username) {
        validationErrors.identity = result.errors.username;
        delete validationErrors.username;
      }
      
      return result.isValid;
    } else {
      // For auth code mode, validate auth code
      const rules = {
        authCode: loginValidationRules.authCode,
      };

      const result = validateForm(formData, rules);
      validationErrors = result.errors;
      return result.isValid;
    }
  }

  // Debounced validation for real-time feedback
  const debouncedValidation = debounce(() => {
    if (touchedFields.size > 0) {
      validateFormData();
    }
  }, 300);

  function handleFieldBlur(fieldName: string) {
    touchedFields.add(fieldName);
    touchedFields = new Set(touchedFields); // Trigger reactivity
    validateFormData();
  }

  function handleFieldInput(fieldName: string, value: string) {
    // Sanitize input
    const sanitized = sanitizeInput(value);
    
    // Update form data
    if (fieldName === 'identity') {
      // Handle username/email field
      if (sanitized.includes('@')) {
        formData.email = sanitized;
        formData.username = '';
      } else {
        formData.username = sanitized;
        formData.email = '';
      }
    } else {
      (formData as any)[fieldName] = sanitized;
    }

    // Trigger debounced validation if field was touched
    if (touchedFields.has(fieldName)) {
      debouncedValidation();
    }
  }

  async function handleSubmit() {
    if (!validateFormData()) return;

    isLoading = true;
    formError = '';
    
    try {
      if (loginMethod === 'code') {
        // Use auth code login (legacy support)
        const success = await authActions.loginWithCode(formData.authCode.trim());
        if (!success) {
          formError = $authState.error || 'Invalid authorization code';
        } else {
          showSuccess = true;
          setTimeout(() => showSuccess = false, 2000);
        }
      } else {
        // Use JWT-based login with username/password
        const username = formData.username || formData.email;
        const success = await authActions.login(username, formData.password, false);
        
        if (!success) {
          formError = $authState.error || 'Invalid credentials. Please check your username/email and password.';
        } else {
          showSuccess = true;
          setTimeout(() => showSuccess = false, 2000);
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      formError = error instanceof Error ? error.message : 'Login failed. Please try again.';
    } finally {
      isLoading = false;
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }

  function switchLoginMethod() {
    loginMethod = loginMethod === 'credentials' ? 'code' : 'credentials';
    formError = '';
    validationErrors = {};
    touchedFields = new Set();
    authActions.clearError();
  }

  function switchToRegister() {
    currentView = 'register';
    formError = '';
    authActions.clearError();
  }

  function switchToLogin() {
    currentView = 'login';
    registrationSuccess = false;
    formError = '';
    authActions.clearError();
  }

  function handleRegistrationSuccess(event: CustomEvent) {
    console.log('Registration successful:', event.detail.user);
    registrationSuccess = true;
    currentView = 'login';
    formError = '';
    
    // Show success message
    showSuccess = true;
    setTimeout(() => {
      showSuccess = false;
    }, 5000);
  }

  function handleRegistrationError(event: CustomEvent) {
    console.error('Registration failed:', event.detail.message);
    // Error is handled by the registration form itself
  }

  function clearAccountLockout() {
    authActions.clearAccountLockout();
  }

  function togglePasswordVisibility() {
    showPassword = !showPassword;
  }
</script>

<svelte:head>
  <title>Login - Grantha AI Platform</title>
  <meta name="description" content="Sign in to access the Grantha AI Platform" />
</svelte:head>

<!-- Background with subtle pattern -->
<div class="login-page min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center p-4 relative overflow-hidden">
  <!-- Animated background elements -->
  <div class="absolute inset-0 overflow-hidden">
    <div class="absolute -inset-10 opacity-5">
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
      <div class="absolute top-3/4 right-1/4 w-96 h-96 bg-accent rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-1000"></div>
      <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-secondary rounded-full mix-blend-multiply filter blur-xl animate-float"></div>
    </div>
  </div>

  <!-- Theme toggle -->
  <div class="absolute top-6 right-6 z-10">
    <ThemeToggle />
  </div>

  <!-- Main login container -->
  <div class="relative z-10 w-full max-w-md">
    <!-- Header -->
    <div class="text-center mb-8">
      <div class="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
        <Shield class="w-8 h-8 text-primary" />
      </div>
      <h1 class="text-3xl font-bold text-foreground mb-2">
        {currentView === 'register' ? 'Join Grantha' : 'Welcome to Grantha'}
      </h1>
      <p class="text-muted-foreground">
        {#if currentView === 'register'}
          Create your account to get started with AI-powered tools
        {:else if loginMethod === 'credentials'}
          Sign in to your account to continue
        {:else}
          Enter your authorization code to access the platform
        {/if}
      </p>
    </div>

    <!-- Auth form card -->
    <div class="bg-card border border-border rounded-lg shadow-lg p-6 backdrop-blur-sm">
      {#if currentView === 'register'}
        <!-- Registration form -->
        <RegistrationForm
          on:success={handleRegistrationSuccess}
          on:error={handleRegistrationError}
          on:switchToLogin={switchToLogin}
        />
      {:else if currentView === 'login'}
        <!-- Account lockout warning -->
        {#if $isAccountLocked}
          <div class="rounded-md bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4 mb-6">
            <div class="flex items-start space-x-3">
              <AlertTriangle class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
              <div class="flex-1">
                <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                  Account Temporarily Locked
                </h4>
                <p class="text-sm text-yellow-700 dark:text-yellow-300 mb-3">
                  Your account has been temporarily locked due to multiple failed login attempts. 
                  Please wait a few minutes before trying again or contact support.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onclick={clearAccountLockout}
                  class="text-yellow-700 border-yellow-300 hover:bg-yellow-100"
                >
                  Try Again
                </Button>
              </div>
            </div>
          </div>
        {:else}
          <!-- Login attempts warning -->
          {#if $loginAttempts > 2}
            <div class="rounded-md bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 p-3 mb-6">
              <div class="flex items-start space-x-2">
                <AlertCircle class="w-4 h-4 text-orange-600 dark:text-orange-400 mt-0.5 flex-shrink-0" />
                <p class="text-sm text-orange-800 dark:text-orange-200">
                  Warning: {$loginAttempts} failed login attempts. Account will be temporarily locked after 5 attempts.
                </p>
              </div>
            </div>
          {/if}
          
          <!-- Registration success message -->
          {#if registrationSuccess}
            <div class="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 mb-6">
              <div class="flex items-start space-x-2">
                <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <p class="text-sm text-green-800 dark:text-green-200">
                  Account created successfully! You can now sign in with your credentials.
                </p>
              </div>
            </div>
          {/if}

          <!-- Method selector -->
          <div class="flex bg-muted rounded-md p-1 mb-6">
            <button
              class="flex-1 py-2 px-3 text-sm font-medium rounded transition-colors
                {loginMethod === 'credentials' 
                  ? 'bg-background text-foreground shadow-sm' 
                  : 'text-muted-foreground hover:text-foreground'}"
              onclick={() => { loginMethod = 'credentials'; }}
              disabled={$isAccountLocked}
            >
              <User class="w-4 h-4 inline mr-2" />
              Credentials
            </button>
            <button
              class="flex-1 py-2 px-3 text-sm font-medium rounded transition-colors
                {loginMethod === 'code' 
                  ? 'bg-background text-foreground shadow-sm' 
                  : 'text-muted-foreground hover:text-foreground'}"
              onclick={() => { loginMethod = 'code'; }}
              disabled={$isAccountLocked}
            >
              <Key class="w-4 h-4 inline mr-2" />
              Auth Code
            </button>
          </div>
        {/if}

      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
        {#if loginMethod === 'credentials'}
          <!-- Username/Email field -->
          <div>
            <label for="identity" class="block text-sm font-medium text-foreground mb-2">
              Username or Email
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <Mail class="w-4 h-4 text-muted-foreground" />
              </div>
              <Input
                id="identity"
                type="text"
                placeholder="Enter username or email"
                bind:value={formData.username}
                error={shouldShowError('identity', validationErrors, touchedFields) ? validationErrors.identity : undefined}
                class="pl-10"
                disabled={isLoading}
                autofocus
                autocomplete={getAutocomplete('username') as any}
                onblur={() => handleFieldBlur('identity')}
                oninput={(e) => handleFieldInput('identity', e.currentTarget.value)}
                onkeydown={handleKeyDown}
              />
            </div>
          </div>

          <!-- Password field -->
          <div>
            <label for="password" class="block text-sm font-medium text-foreground mb-2">
              Password
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <Lock class="w-4 h-4 text-muted-foreground" />
              </div>
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                bind:value={formData.password}
                error={shouldShowError('password', validationErrors, touchedFields) ? validationErrors.password : undefined}
                class="pl-10 pr-10"
                disabled={isLoading}
                autocomplete={getAutocomplete('password') as any}
                onblur={() => handleFieldBlur('password')}
                oninput={(e) => handleFieldInput('password', e.currentTarget.value)}
                onkeydown={handleKeyDown}
              />
              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
                onclick={togglePasswordVisibility}
              >
                {#if showPassword}
                  <EyeOff class="w-4 h-4" />
                {:else}
                  <Eye class="w-4 h-4" />
                {/if}
              </button>
            </div>
          </div>
        {:else}
          <!-- Auth code field -->
          <div>
            <label for="auth-code" class="block text-sm font-medium text-foreground mb-2">
              Authorization Code
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <Key class="w-4 h-4 text-muted-foreground" />
              </div>
              <Input
                id="auth-code"
                type="password"
                placeholder="Enter authorization code"
                bind:value={formData.authCode}
                error={shouldShowError('authCode', validationErrors, touchedFields) ? validationErrors.authCode : undefined}
                class="pl-10"
                disabled={isLoading}
                autofocus
                autocomplete="off"
                onblur={() => handleFieldBlur('authCode')}
                oninput={(e) => handleFieldInput('authCode', e.currentTarget.value)}
                onkeydown={handleKeyDown}
              />
            </div>
          </div>
        {/if}

        <!-- Submit button -->
        <Button
          type="submit"
          class="w-full h-11 text-base font-medium"
          loading={isLoading}
          disabled={isLoading || $isAccountLocked}
        >
          {#if !isLoading}
            <Lock class="w-4 h-4 mr-2" />
          {/if}
          {loginMethod === 'credentials' ? 'Sign In' : 'Authenticate'}
          <ArrowRight class="w-4 h-4 ml-2" />
        </Button>

        <!-- Success display -->
        {#if showSuccess}
          <div class="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 flex items-start space-x-2 animate-fade-in">
            <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <p class="text-sm text-green-800 dark:text-green-200">
              Authentication successful! Redirecting...
            </p>
          </div>
        {/if}

        <!-- Error display -->
        {#if (formError || $authState.error) && !showSuccess}
          <div class="rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2 animate-fade-in">
            <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
            <p class="text-sm text-destructive">
              {formError || $authState.error}
            </p>
          </div>
        {/if}
      </form>

        <!-- Additional options -->
        {#if !$isAccountLocked}
          <div class="mt-6 pt-4 border-t border-border">
            <div class="text-center space-y-3">
              <button
                type="button"
                class="text-sm text-muted-foreground hover:text-foreground transition-colors block w-full"
                onclick={switchLoginMethod}
              >
                {loginMethod === 'credentials' 
                  ? 'Have an authorization code instead?' 
                  : 'Use username and password instead?'}
              </button>
              
              <div class="flex items-center justify-center space-x-2 text-sm text-muted-foreground">
                <span>Don't have an account?</span>
                <button
                  type="button"
                  class="text-primary hover:text-primary/80 font-medium transition-colors"
                  onclick={switchToRegister}
                >
                  Sign up here
                </button>
              </div>
            </div>
          </div>
        {/if}
      {/if}

      <!-- Help text -->
      {#if currentView === 'login'}
        <div class="mt-4 text-center">
          <p class="text-xs text-muted-foreground">
            Need help? Contact your system administrator or check your configuration.
          </p>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="text-center mt-6">
      <p class="text-sm text-muted-foreground">
        Powered by 
        <span class="font-semibold text-foreground">Grantha AI Platform</span>
      </p>
    </div>
  </div>
</div>

<style>
  /* Custom animations */
  @keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
  }

  .animate-float {
    animation: float 3s ease-in-out infinite;
  }

  /* Smooth transitions for form elements */
  :global(.login-page input:focus) {
    transform: translateY(-1px);
  }

  :global(.login-page button:active) {
    transform: translateY(1px);
  }

  /* Custom scrollbar for mobile */
  :global(.login-page) {
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  :global(.login-page::-webkit-scrollbar) {
    display: none;
  }
</style>