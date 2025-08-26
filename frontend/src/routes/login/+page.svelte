<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authState, authActions, canAccessApp } from '$stores/auth';
  import Button from '$lib/components/ui/button.svelte';
  import Input from '$lib/components/ui/input.svelte';
  import ThemeToggle from '$lib/components/ThemeToggle.svelte';
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
    AlertCircle
  } from 'lucide-svelte';

  // Form states
  let loginMethod: 'credentials' | 'code' = 'credentials';
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

  function validateForm(): boolean {
    const errors: Record<string, string> = {};
    
    if (loginMethod === 'credentials') {
      if (!formData.username.trim() && !formData.email.trim()) {
        errors.identity = 'Username or email is required';
      }
      if (!formData.password.trim()) {
        errors.password = 'Password is required';
      } else if (formData.password.length < 3) {
        errors.password = 'Password must be at least 3 characters';
      }
    } else {
      if (!formData.authCode.trim()) {
        errors.authCode = 'Authorization code is required';
      }
    }

    validationErrors = errors;
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;

    isLoading = true;
    formError = '';
    
    try {
      if (loginMethod === 'code') {
        // Use existing auth code validation
        const success = await authActions.validateCode(formData.authCode.trim());
        if (!success) {
          formError = $authState.error || 'Invalid authorization code';
        }
      } else {
        // For traditional login, we'll use the auth code field as a fallback
        // In a real implementation, you'd have a separate login endpoint
        // For now, we'll treat username/password as an auth code for demo purposes
        const loginCode = `${formData.username || formData.email}:${formData.password}`;
        const success = await authActions.validateCode(loginCode);
        
        if (!success) {
          // If that fails, try just the password as auth code
          const passSuccess = await authActions.validateCode(formData.password);
          if (!passSuccess) {
            formError = 'Invalid credentials. Please check your username/email and password.';
          }
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
    authActions.clearError();
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
<div class="min-h-screen bg-gradient-to-br from-background via-background to-accent/5 flex items-center justify-center p-4 relative overflow-hidden">
  <!-- Animated background elements -->
  <div class="absolute inset-0 overflow-hidden">
    <div class="absolute -inset-10 opacity-5">
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
      <div class="absolute top-3/4 right-1/4 w-96 h-96 bg-accent rounded-full mix-blend-multiply filter blur-xl animate-pulse delay-1000"></div>
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
      <h1 class="text-3xl font-bold text-foreground mb-2">Welcome to Grantha</h1>
      <p class="text-muted-foreground">
        {loginMethod === 'credentials' 
          ? 'Sign in to your account to continue' 
          : 'Enter your authorization code to access the platform'}
      </p>
    </div>

    <!-- Login form card -->
    <div class="bg-card border border-border rounded-lg shadow-lg p-6 backdrop-blur-sm">
      <!-- Method selector -->
      <div class="flex bg-muted rounded-md p-1 mb-6">
        <button
          class="flex-1 py-2 px-3 text-sm font-medium rounded transition-colors
            {loginMethod === 'credentials' 
              ? 'bg-background text-foreground shadow-sm' 
              : 'text-muted-foreground hover:text-foreground'}"
          onclick={() => { loginMethod = 'credentials'; }}
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
        >
          <Key class="w-4 h-4 inline mr-2" />
          Auth Code
        </button>
      </div>

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
                error={validationErrors.identity}
                class="pl-10"
                disabled={isLoading}
                autofocus
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
                error={validationErrors.password}
                class="pl-10 pr-10"
                disabled={isLoading}
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
                error={validationErrors.authCode}
                class="pl-10"
                disabled={isLoading}
                autofocus
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
          disabled={isLoading}
        >
          {#if !isLoading}
            <Lock class="w-4 h-4 mr-2" />
          {/if}
          {loginMethod === 'credentials' ? 'Sign In' : 'Authenticate'}
          <ArrowRight class="w-4 h-4 ml-2" />
        </Button>

        <!-- Error display -->
        {#if formError || $authState.error}
          <div class="rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2">
            <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
            <p class="text-sm text-destructive">
              {formError || $authState.error}
            </p>
          </div>
        {/if}
      </form>

      <!-- Additional options -->
      <div class="mt-6 pt-4 border-t border-border">
        <div class="text-center">
          <button
            type="button"
            class="text-sm text-muted-foreground hover:text-foreground transition-colors"
            onclick={switchLoginMethod}
          >
            {loginMethod === 'credentials' 
              ? 'Have an authorization code instead?' 
              : 'Use username and password instead?'}
          </button>
        </div>
      </div>

      <!-- Help text -->
      <div class="mt-4 text-center">
        <p class="text-xs text-muted-foreground">
          Need help? Contact your system administrator or check your configuration.
        </p>
      </div>
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