<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/ui/button.svelte';
  import Input from '$lib/components/ui/input.svelte';
  import { 
    validateForm, 
    validationRules, 
    sanitizeInput,
    shouldShowError,
    debounce
  } from '$lib/utils/validation';
  import { 
    Lock, 
    Eye, 
    EyeOff,
    Shield,
    AlertCircle,
    CheckCircle,
    LogOut
  } from 'lucide-svelte';
  import { authActions } from '$lib/stores/auth';

  const dispatch = createEventDispatcher<{
    success: void;
    error: { message: string };
    cancel: void;
  }>();

  // Form state
  let formData = $state({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });
  
  let showCurrentPassword = $state(false);
  let showNewPassword = $state(false);
  let showConfirmPassword = $state(false);
  let isLoading = $state(false);
  let formError = $state('');
  let successMessage = $state('');
  let validationErrors = $state<Record<string, string>>({});
  let touchedFields = $state(new Set<string>());
  let countdown = $state(0);

  // Custom validation rules for password change
  const passwordChangeRules = {
    currentPassword: [
      validationRules.required('Current password is required')
    ],
    newPassword: [
      validationRules.required('New password is required'),
      validationRules.minLength(8, 'New password must be at least 8 characters'),
      validationRules.strongPassword()
    ],
    confirmNewPassword: [
      validationRules.required('Please confirm your new password'),
      {
        test: (value: string) => value === formData.newPassword,
        message: 'Passwords do not match'
      }
    ]
  };

  function validateFormData(): boolean {
    // Add additional validation to ensure new password is different from current
    const rules = {
      ...passwordChangeRules,
      newPassword: [
        ...passwordChangeRules.newPassword,
        {
          test: (value: string) => value !== formData.currentPassword,
          message: 'New password must be different from current password'
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
    // Update form data (don't sanitize passwords)
    (formData as any)[fieldName] = value;

    // Trigger debounced validation if field was touched
    if (touchedFields.has(fieldName)) {
      debouncedValidation();
    }
  }

  async function handleSubmit() {
    if (!validateFormData()) return;

    isLoading = true;
    formError = '';
    successMessage = '';
    
    try {
      const result = await authActions.changePassword(
        formData.currentPassword,
        formData.newPassword
      );

      if (result.success) {
        successMessage = 'Password changed successfully! You will be logged out in a few seconds for security.';
        
        // Start countdown
        countdown = 5;
        const countdownInterval = setInterval(() => {
          countdown--;
          if (countdown <= 0) {
            clearInterval(countdownInterval);
          }
        }, 1000);
        
        dispatch('success');
      } else {
        formError = result.error || 'Failed to change password';
        dispatch('error', { message: formError });
      }
    } catch (error) {
      console.error('Password change error:', error);
      formError = error instanceof Error ? error.message : 'Failed to change password. Please try again.';
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

  function togglePasswordVisibility(field: 'current' | 'new' | 'confirm') {
    switch (field) {
      case 'current':
        showCurrentPassword = !showCurrentPassword;
        break;
      case 'new':
        showNewPassword = !showNewPassword;
        break;
      case 'confirm':
        showConfirmPassword = !showConfirmPassword;
        break;
    }
  }

  function handleCancel() {
    // Reset form
    formData = {
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: ''
    };
    validationErrors = {};
    touchedFields = new Set();
    formError = '';
    successMessage = '';
    
    dispatch('cancel');
  }

  // Password strength indicator
  $: passwordStrength = getPasswordStrength(formData.newPassword);

  function getPasswordStrength(password: string): {
    score: number;
    label: string;
    color: string;
    suggestions: string[];
  } {
    if (!password) return { score: 0, label: '', color: '', suggestions: [] };
    
    let score = 0;
    const suggestions: string[] = [];
    
    if (password.length >= 8) score += 1;
    else suggestions.push('At least 8 characters');
    
    if (/[a-z]/.test(password)) score += 1;
    else suggestions.push('Include lowercase letters');
    
    if (/[A-Z]/.test(password)) score += 1;
    else suggestions.push('Include uppercase letters');
    
    if (/\d/.test(password)) score += 1;
    else suggestions.push('Include numbers');
    
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
</script>

<div class="max-w-md mx-auto">
  <div class="text-center mb-6">
    <div class="inline-flex items-center justify-center w-12 h-12 bg-primary/10 rounded-full mb-3">
      <Shield class="w-6 h-6 text-primary" />
    </div>
    <h2 class="text-2xl font-bold text-foreground mb-1">Change Password</h2>
    <p class="text-sm text-muted-foreground">
      Update your password to keep your account secure
    </p>
  </div>

  <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
    <!-- Current Password -->
    <div>
      <label for="currentPassword" class="block text-sm font-medium text-foreground mb-2">
        Current Password *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Lock class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="currentPassword"
          type={showCurrentPassword ? 'text' : 'password'}
          placeholder="Enter your current password"
          bind:value={formData.currentPassword}
          error={shouldShowError('currentPassword', validationErrors, touchedFields) ? validationErrors.currentPassword : undefined}
          class="pl-10 pr-10"
          disabled={isLoading || successMessage !== ''}
          autocomplete="current-password"
          onblur={() => handleFieldBlur('currentPassword')}
          oninput={(e) => handleFieldInput('currentPassword', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
          onclick={() => togglePasswordVisibility('current')}
          disabled={isLoading || successMessage !== ''}
        >
          {#if showCurrentPassword}
            <EyeOff class="w-4 h-4" />
          {:else}
            <Eye class="w-4 h-4" />
          {/if}
        </button>
      </div>
    </div>

    <!-- New Password -->
    <div>
      <label for="newPassword" class="block text-sm font-medium text-foreground mb-2">
        New Password *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Lock class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="newPassword"
          type={showNewPassword ? 'text' : 'password'}
          placeholder="Enter your new password"
          bind:value={formData.newPassword}
          error={shouldShowError('newPassword', validationErrors, touchedFields) ? validationErrors.newPassword : undefined}
          class="pl-10 pr-10"
          disabled={isLoading || successMessage !== ''}
          autocomplete="new-password"
          onblur={() => handleFieldBlur('newPassword')}
          oninput={(e) => handleFieldInput('newPassword', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
          onclick={() => togglePasswordVisibility('new')}
          disabled={isLoading || successMessage !== ''}
        >
          {#if showNewPassword}
            <EyeOff class="w-4 h-4" />
          {:else}
            <Eye class="w-4 h-4" />
          {/if}
        </button>
      </div>
      
      <!-- Password strength indicator -->
      {#if formData.newPassword && touchedFields.has('newPassword')}
        <div class="mt-2">
          <div class="flex items-center space-x-2">
            <div class="flex-1 bg-muted rounded-full h-2">
              <div 
                class="h-2 rounded-full transition-all duration-300"
                class:bg-red-500={passwordStrength.score <= 1}
                class:bg-orange-500={passwordStrength.score === 2}
                class:bg-yellow-500={passwordStrength.score === 3}
                class:bg-blue-500={passwordStrength.score === 4}
                class:bg-green-500={passwordStrength.score === 5}
                style="width: {(passwordStrength.score / 5) * 100}%"
              ></div>
            </div>
            {#if passwordStrength.label}
              <span class="text-xs font-medium {passwordStrength.color}">
                {passwordStrength.label}
              </span>
            {/if}
          </div>
          
          {#if passwordStrength.suggestions.length > 0}
            <div class="mt-2 text-xs text-muted-foreground">
              <p class="mb-1">To improve strength:</p>
              <ul class="list-disc list-inside space-y-0.5">
                {#each passwordStrength.suggestions as suggestion}
                  <li>{suggestion}</li>
                {/each}
              </ul>
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Confirm New Password -->
    <div>
      <label for="confirmNewPassword" class="block text-sm font-medium text-foreground mb-2">
        Confirm New Password *
      </label>
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <Lock class="w-4 h-4 text-muted-foreground" />
        </div>
        <Input
          id="confirmNewPassword"
          type={showConfirmPassword ? 'text' : 'password'}
          placeholder="Confirm your new password"
          bind:value={formData.confirmNewPassword}
          error={shouldShowError('confirmNewPassword', validationErrors, touchedFields) ? validationErrors.confirmNewPassword : undefined}
          class="pl-10 pr-10"
          disabled={isLoading || successMessage !== ''}
          autocomplete="new-password"
          onblur={() => handleFieldBlur('confirmNewPassword')}
          oninput={(e) => handleFieldInput('confirmNewPassword', e.currentTarget.value)}
          onkeydown={handleKeyDown}
        />
        <button
          type="button"
          class="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
          onclick={() => togglePasswordVisibility('confirm')}
          disabled={isLoading || successMessage !== ''}
        >
          {#if showConfirmPassword}
            <EyeOff class="w-4 h-4" />
          {:else}
            <Eye class="w-4 h-4" />
          {/if}
        </button>
      </div>
    </div>

    <!-- Action buttons -->
    {#if !successMessage}
      <div class="flex space-x-3 pt-2">
        <Button
          type="submit"
          class="flex-1 h-11 text-base font-medium"
          loading={isLoading}
          disabled={isLoading}
        >
          {#if !isLoading}
            <Shield class="w-4 h-4 mr-2" />
          {/if}
          Change Password
        </Button>
        
        <Button
          type="button"
          variant="outline"
          onclick={handleCancel}
          disabled={isLoading}
          class="px-6"
        >
          Cancel
        </Button>
      </div>
    {/if}

    <!-- Success display with countdown -->
    {#if successMessage}
      <div class="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-4 flex items-start space-x-3">
        <CheckCircle class="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
        <div class="flex-1">
          <p class="text-sm text-green-800 dark:text-green-200 mb-2">
            {successMessage}
          </p>
          {#if countdown > 0}
            <div class="flex items-center space-x-2 text-green-700 dark:text-green-300">
              <LogOut class="w-4 h-4" />
              <span class="text-sm font-medium">
                Redirecting in {countdown} seconds...
              </span>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Error display -->
    {#if formError && !successMessage}
      <div class="rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2">
        <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
        <p class="text-sm text-destructive">
          {formError}
        </p>
      </div>
    {/if}
  </form>

  <!-- Security note -->
  {#if !successMessage}
    <div class="mt-6 p-4 bg-muted/50 border border-border rounded-lg">
      <h4 class="text-sm font-medium text-foreground mb-2 flex items-center">
        <Shield class="w-4 h-4 mr-2" />
        Security Notice
      </h4>
      <p class="text-xs text-muted-foreground">
        After changing your password, you will be logged out of all devices for security. 
        You'll need to sign in again with your new password.
      </p>
    </div>
  {/if}
</div>