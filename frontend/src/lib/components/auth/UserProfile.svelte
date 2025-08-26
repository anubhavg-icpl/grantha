<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/button.svelte';
  import Input from '$lib/components/ui/input.svelte';
  import { 
    User, 
    Mail, 
    Calendar,
    Shield,
    CheckCircle,
    AlertCircle,
    Edit3,
    Save,
    X
  } from 'lucide-svelte';
  import { authActions, authState } from '$lib/stores/auth';
  import { sanitizeInput } from '$lib/utils/validation';

  // Component state
  let isEditing = $state(false);
  let isLoading = $state(false);
  let isUpdating = $state(false);
  let error = $state('');
  let successMessage = $state('');

  // Form data
  let formData = $state({
    username: '',
    email: '',
    full_name: '',
    bio: ''
  });

  // Original data for cancel functionality
  let originalData = $state({
    username: '',
    email: '',
    full_name: '',
    bio: ''
  });

  onMount(async () => {
    await loadUserProfile();
  });

  async function loadUserProfile() {
    isLoading = true;
    error = '';

    try {
      const userProfile = await authActions.getCurrentUser();
      if (userProfile) {
        const userData = {
          username: userProfile.username || '',
          email: userProfile.email || '',
          full_name: userProfile.full_name || '',
          bio: userProfile.bio || ''
        };
        
        formData = { ...userData };
        originalData = { ...userData };
      } else {
        // Fallback to auth state user data
        const user = $authState.user;
        if (user) {
          const userData = {
            username: user.username || '',
            email: user.email || '',
            full_name: user.full_name || '',
            bio: ''
          };
          
          formData = { ...userData };
          originalData = { ...userData };
        }
      }
    } catch (err) {
      console.error('Failed to load user profile:', err);
      error = 'Failed to load profile information';
    } finally {
      isLoading = false;
    }
  }

  function startEdit() {
    isEditing = true;
    error = '';
    successMessage = '';
  }

  function cancelEdit() {
    isEditing = false;
    formData = { ...originalData };
    error = '';
    successMessage = '';
  }

  async function saveChanges() {
    isUpdating = true;
    error = '';
    successMessage = '';

    try {
      // Prepare update data (only changed fields)
      const updates: Record<string, any> = {};
      
      if (formData.email !== originalData.email) {
        updates.email = formData.email.trim() || null;
      }
      
      if (formData.full_name !== originalData.full_name) {
        updates.full_name = formData.full_name.trim() || null;
      }
      
      if (formData.bio !== originalData.bio) {
        updates.bio = formData.bio.trim() || null;
      }

      if (Object.keys(updates).length === 0) {
        isEditing = false;
        return;
      }

      const result = await authActions.updateUserProfile(updates);
      
      if (result.success && result.user) {
        // Update original data
        originalData = { ...formData };
        isEditing = false;
        successMessage = 'Profile updated successfully';
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          successMessage = '';
        }, 3000);
      } else {
        error = result.error || 'Failed to update profile';
      }
    } catch (err) {
      console.error('Profile update error:', err);
      error = err instanceof Error ? err.message : 'Failed to update profile';
    } finally {
      isUpdating = false;
    }
  }

  function handleFieldInput(fieldName: string, value: string) {
    const sanitized = sanitizeInput(value);
    (formData as any)[fieldName] = sanitized;
  }

  // Format date for display
  function formatDate(dateString?: string): string {
    if (!dateString) return 'Not available';
    
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid date';
    }
  }
</script>

<div class="max-w-2xl mx-auto">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-2xl font-bold text-foreground flex items-center">
        <User class="w-6 h-6 mr-2" />
        User Profile
      </h2>
      <p class="text-muted-foreground">
        Manage your personal information and preferences
      </p>
    </div>
    
    {#if !isEditing && !isLoading}
      <Button
        variant="outline"
        onclick={startEdit}
        class="flex items-center"
      >
        <Edit3 class="w-4 h-4 mr-2" />
        Edit Profile
      </Button>
    {/if}
  </div>

  <!-- Loading state -->
  {#if isLoading}
    <div class="bg-card border border-border rounded-lg p-6">
      <div class="animate-pulse space-y-4">
        <div class="h-4 bg-muted rounded w-1/4"></div>
        <div class="h-10 bg-muted rounded"></div>
        <div class="h-4 bg-muted rounded w-1/4"></div>
        <div class="h-10 bg-muted rounded"></div>
        <div class="h-4 bg-muted rounded w-1/4"></div>
        <div class="h-20 bg-muted rounded"></div>
      </div>
    </div>
  {:else}
    <!-- Profile form -->
    <div class="bg-card border border-border rounded-lg p-6 space-y-6">
      <!-- Success message -->
      {#if successMessage}
        <div class="rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 flex items-start space-x-2">
          <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
          <p class="text-sm text-green-800 dark:text-green-200">
            {successMessage}
          </p>
        </div>
      {/if}

      <!-- Error message -->
      {#if error}
        <div class="rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2">
          <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
          <p class="text-sm text-destructive">
            {error}
          </p>
        </div>
      {/if}

      <form class="space-y-4">
        <!-- Username (read-only) -->
        <div>
          <label class="block text-sm font-medium text-foreground mb-2">
            Username
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <User class="w-4 h-4 text-muted-foreground" />
            </div>
            <Input
              type="text"
              value={formData.username}
              class="pl-10 bg-muted"
              disabled
              readonly
            />
          </div>
          <p class="text-xs text-muted-foreground mt-1">
            Username cannot be changed
          </p>
        </div>

        <!-- Email -->
        <div>
          <label class="block text-sm font-medium text-foreground mb-2">
            Email Address
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <Mail class="w-4 h-4 text-muted-foreground" />
            </div>
            <Input
              type="email"
              placeholder="Enter your email address"
              bind:value={formData.email}
              class="pl-10"
              disabled={!isEditing}
              readonly={!isEditing}
              oninput={(e) => handleFieldInput('email', e.currentTarget.value)}
            />
          </div>
        </div>

        <!-- Full Name -->
        <div>
          <label class="block text-sm font-medium text-foreground mb-2">
            Full Name
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <User class="w-4 h-4 text-muted-foreground" />
            </div>
            <Input
              type="text"
              placeholder="Enter your full name"
              bind:value={formData.full_name}
              class="pl-10"
              disabled={!isEditing}
              readonly={!isEditing}
              oninput={(e) => handleFieldInput('full_name', e.currentTarget.value)}
            />
          </div>
        </div>

        <!-- Bio -->
        <div>
          <label class="block text-sm font-medium text-foreground mb-2">
            Bio
          </label>
          <textarea
            placeholder="Tell us about yourself"
            bind:value={formData.bio}
            class="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-colors resize-none"
            class:bg-muted={!isEditing}
            class:cursor-not-allowed={!isEditing}
            rows="4"
            disabled={!isEditing}
            readonly={!isEditing}
            oninput={(e) => handleFieldInput('bio', e.currentTarget.value)}
          ></textarea>
        </div>

        <!-- Action buttons (when editing) -->
        {#if isEditing}
          <div class="flex space-x-3 pt-4">
            <Button
              type="button"
              onclick={saveChanges}
              loading={isUpdating}
              disabled={isUpdating}
              class="flex items-center"
            >
              <Save class="w-4 h-4 mr-2" />
              Save Changes
            </Button>
            
            <Button
              type="button"
              variant="outline"
              onclick={cancelEdit}
              disabled={isUpdating}
              class="flex items-center"
            >
              <X class="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        {/if}
      </form>

      <!-- Account information -->
      <div class="pt-6 border-t border-border">
        <h3 class="text-lg font-medium text-foreground mb-4 flex items-center">
          <Shield class="w-5 h-5 mr-2" />
          Account Information
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <!-- User ID -->
          <div>
            <span class="text-muted-foreground">User ID:</span>
            <span class="ml-2 font-mono text-foreground">
              {$authState.user?.id || 'N/A'}
            </span>
          </div>
          
          <!-- Account Status -->
          <div>
            <span class="text-muted-foreground">Status:</span>
            <span class="ml-2 text-green-600 dark:text-green-400">
              Active
            </span>
          </div>
          
          <!-- Verification Status -->
          {#if $authState.user?.is_verified !== undefined}
            <div>
              <span class="text-muted-foreground">Verified:</span>
              <span class="ml-2" class:text-green-600={$authState.user.is_verified} class:text-yellow-600={!$authState.user.is_verified}>
                {$authState.user.is_verified ? 'Yes' : 'Pending'}
              </span>
            </div>
          {/if}
          
          <!-- Admin Status -->
          {#if $authState.user?.is_superuser}
            <div>
              <span class="text-muted-foreground">Admin:</span>
              <span class="ml-2 text-primary font-medium">
                Yes
              </span>
            </div>
          {/if}
          
          <!-- Created At -->
          {#if $authState.user?.created_at}
            <div class="md:col-span-2">
              <span class="text-muted-foreground">Member since:</span>
              <span class="ml-2 text-foreground flex items-center">
                <Calendar class="w-4 h-4 mr-1" />
                {formatDate($authState.user.created_at)}
              </span>
            </div>
          {/if}
          
          <!-- Last Login -->
          {#if $authState.user?.last_login}
            <div class="md:col-span-2">
              <span class="text-muted-foreground">Last login:</span>
              <span class="ml-2 text-foreground">
                {formatDate($authState.user.last_login)}
              </span>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Loading animation */
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>