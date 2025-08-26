<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/ui/button.svelte';
  import Input from '$lib/components/ui/input.svelte';
  import { 
    validateForm, 
    registrationValidationRules, 
    sanitizeInput,
    shouldShowError,
    debounce,
    getAutocomplete
  } from '$lib/utils/validation';
  import { 
    User, 
    Mail, 
    Lock, 
    Eye, 
    EyeOff,
    UserCheck,
    AlertCircle,
    CheckCircle
  } from 'lucide-svelte';
  import { authActions } from '$lib/stores/auth';

  const dispatch = createEventDispatcher<{
    success: { user: any };
    error: { message: string };
    switchToLogin: void;
  }>();

  // Form state
  let formData = $state({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    bio: ''
  });
  
  let showPassword = $state(false);
  let showConfirmPassword = $state(false);
  let isLoading = $state(false);
  let formError = $state('');
  let validationErrors = $state<Record<string, string>>({});
  let touchedFields = $state(new Set<string>());

  function validateFormData(): boolean {
    // Create validation rules with confirm password check
    const rules = {
      ...registrationValidationRules,
      confirmPassword: [
        ...registrationValidationRules.confirmPassword,
        {
          test: (value: string) => value === formData.password,
          message: 'Passwords do not match'
        }
      ]
    };

    const result = validateForm(formData, rules);
    validationErrors = result.errors;
    return result.isValid;
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
    (formData as any)[fieldName] = sanitized;

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
      const result = await authActions.register({
        username: formData.username.trim(),
        password: formData.password,
        email: formData.email.trim() || undefined,
        full_name: formData.fullName.trim() || undefined,
        bio: formData.bio.trim() || undefined
      });

      if (result.success && result.user) {
        dispatch('success', { user: result.user });
      } else {
        formError = result.error || 'Registration failed';
        dispatch('error', { message: formError });
      }
    } catch (error) {
      console.error('Registration error:', error);
      formError = error instanceof Error ? error.message : 'Registration failed. Please try again.';
      dispatch('error', { message: formError });
    } finally {
      isLoading = false;
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }

  function togglePasswordVisibility(field: 'password' | 'confirmPassword') {
    if (field === 'password') {
      showPassword = !showPassword;
    } else {
      showConfirmPassword = !showConfirmPassword;
    }
  }
</script>

<div class="space-y-4">
  <div class="text-center mb-6">
    <div class="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-full mb-3">
      <UserCheck class="w-6 h-6 text-primary" />
    </div>
    <h2 class="text-2xl font-bold text-foreground mb-1">Create Account</h2>
    <p class="text-sm text-muted-foreground">
      Join Grantha to access powerful AI tools
    </p>
  </div>

  <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
    <!-- Username field -->
    <div>
      <label for="username" class="block text-sm font-medium text-foreground mb-2">
        Username *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <User class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="username"
          type="text"
          placeholder="Enter username"
          bind:value={formData.username}
          error={shouldShowError('username', validationErrors, touchedFields) ? validationErrors.username : undefined}
          class="pl-10"
          disabled={isLoading}
          autocomplete={getAutocomplete('username') as any}
          onblur={() => handleFieldBlur('username')}
          oninput={(e) => handleFieldInput('username', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
      </div>
    </div>

    <!-- Email field -->
    <div>
      <label for="email" class="block text-sm font-medium text-foreground mb-2">
        Email Address
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Mail class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="email"
          type="email"
          placeholder="Enter email address (optional)"
          bind:value={formData.email}
          error={shouldShowError('email', validationErrors, touchedFields) ? validationErrors.email : undefined}
          class="pl-10"
          disabled={isLoading}
          autocomplete={getAutocomplete('email') as any}
          onblur={() => handleFieldBlur('email')}
          oninput={(e) => handleFieldInput('email', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
      </div>
    </div>

    <!-- Full Name field -->
    <div>
      <label for="fullName" class="block text-sm font-medium text-foreground mb-2">
        Full Name
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <User class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="fullName"
          type="text"
          placeholder="Enter your full name (optional)"
          bind:value={formData.fullName}
          class="pl-10"
          disabled={isLoading}
          autocomplete={getAutocomplete('fullName') as any}
          onblur={() => handleFieldBlur('fullName')}
          oninput={(e) => handleFieldInput('fullName', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
      </div>
    </div>

    <!-- Password field -->
    <div>
      <label for="password" class="block text-sm font-medium text-foreground mb-2">
        Password *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Lock class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="password"
          type={showPassword ? 'text' : 'password'}
          placeholder="Create a strong password"
          bind:value={formData.password}
          error={shouldShowError('password', validationErrors, touchedFields) ? validationErrors.password : undefined}
          class="pl-10 pr-10"
          disabled={isLoading}
          autocomplete={getAutocomplete('newPassword') as any}
          onblur={() => handleFieldBlur('password')}
          oninput={(e) => handleFieldInput('password', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
          onclick={() => togglePasswordVisibility('password')}
        >
          {#if showPassword}
            <EyeOff class="w-4 h-4" />
          {:else}
            <Eye class="w-4 h-4" />
          {/if}
        </button>
      </div>
    </div>

    <!-- Confirm Password field -->
    <div>
      <label for="confirmPassword" class="block text-sm font-medium text-foreground mb-2">
        Confirm Password *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Lock class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="confirmPassword"
          type={showConfirmPassword ? 'text' : 'password'}
          placeholder="Confirm your password"
          bind:value={formData.confirmPassword}
          error={shouldShowError('confirmPassword', validationErrors, touchedFields) ? validationErrors.confirmPassword : undefined}
          class="pl-10 pr-10"
          disabled={isLoading}
          autocomplete={getAutocomplete('newPassword') as any}
          onblur={() => handleFieldBlur('confirmPassword')}
          oninput={(e) => handleFieldInput('confirmPassword', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
          onclick={() => togglePasswordVisibility('confirmPassword')}
        >
          {#if showConfirmPassword}
            <EyeOff class="w-4 h-4" />
          {:else}
            <Eye class="w-4 h-4" />
          {/if}
        </button>
      </div>
    </div>

    <!-- Bio field -->
    <div>
      <label for="bio" class="block text-sm font-medium text-foreground mb-2">
        Bio
      </label>
      <textarea
        id="bio"
        placeholder="Tell us about yourself (optional)"
        bind:value={formData.bio}
        class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors resize-none"
        rows="3"
        disabled={isLoading}
        onblur={() => handleFieldBlur('bio')}
        oninput={(e) => handleFieldInput('bio', e.currentTarget.value)}
      ></textarea>
    </div>

    <!-- Submit button -->
    <Button
      type="submit"
      class="w-full h-11 text-base font-medium"
      loading={isLoading}
      disabled={isLoading}
    >
      {#if !isLoading}
        <UserCheck class="w-4 h-4 mr-2" />
      {/if}
      Create Account
    </Button>

    <!-- Error display -->
    {#if formError}
      <div class="rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2 animate-fade-in">
        <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
        <p class="text-sm text-destructive">
          {formError}
        </p>
      </div>
    {/if}
  </form>

  <!-- Switch to login -->
  <div class="mt-6 pt-4 border-t border-border text-center">
    <p class="text-sm text-muted-foreground">
      Already have an account?
      <button
        type="button"
        class="text-primary hover:text-primary/80 font-medium transition-colors"
        onclick={() => dispatch('switchToLogin')}
      >
        Sign in here
      </button>
    </p>
  </div>
</div>

<style>
  /* Custom animations for form elements */
  :global(.animate-fade-in) {
    animation: fadeIn 0.3s ease-in-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>