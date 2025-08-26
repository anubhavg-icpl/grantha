<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/button.svelte';
  import { 
    Monitor,
    Smartphone,
    Tablet,
    Globe,
    MapPin,
    Clock,
    LogOut,
    AlertTriangle,
    RefreshCw,
    CheckCircle,
    AlertCircle
  } from 'lucide-svelte';
  import { authActions, userSessions } from '$lib/stores/auth';
  import type { SessionInfo } from '$lib/types/api';

  // Component state
  let isLoading = $state(false);
  let isRefreshing = $state(false);
  let error = $state('');
  let successMessage = $state('');
  let revokingSessionId = $state<string | null>(null);

  onMount(async () => {
    await loadSessions();
  });

  async function loadSessions() {
    isLoading = true;
    error = '';

    try {
      await authActions.getUserSessions();
    } catch (err) {
      console.error('Failed to load sessions:', err);
      error = 'Failed to load session information';
    } finally {
      isLoading = false;
    }
  }

  async function refreshSessions() {
    isRefreshing = true;
    error = '';

    try {
      await authActions.getUserSessions();
      successMessage = 'Sessions refreshed successfully';
      setTimeout(() => {
        successMessage = '';
      }, 2000);
    } catch (err) {
      console.error('Failed to refresh sessions:', err);
      error = 'Failed to refresh session information';
    } finally {
      isRefreshing = false;
    }
  }

  async function revokeSession(sessionId: string) {
    if (revokingSessionId) return; // Prevent multiple simultaneous revokes

    revokingSessionId = sessionId;
    error = '';

    try {
      const result = await authActions.revokeSession(sessionId);
      
      if (result.success) {
        successMessage = 'Session revoked successfully';
        setTimeout(() => {
          successMessage = '';
        }, 2000);
      } else {
        error = result.error || 'Failed to revoke session';
      }
    } catch (err) {
      console.error('Failed to revoke session:', err);
      error = err instanceof Error ? err.message : 'Failed to revoke session';
    } finally {
      revokingSessionId = null;
    }
  }

  function getDeviceIcon(userAgent?: string) {
    if (!userAgent) return Globe;
    
    const ua = userAgent.toLowerCase();
    
    if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
      return Smartphone;
    } else if (ua.includes('tablet') || ua.includes('ipad')) {
      return Tablet;
    }
    
    return Monitor;
  }

  function getDeviceType(userAgent?: string): string {
    if (!userAgent) return 'Unknown Device';
    
    const ua = userAgent.toLowerCase();
    
    if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
      return 'Mobile Device';
    } else if (ua.includes('tablet') || ua.includes('ipad')) {
      return 'Tablet';
    }
    
    return 'Desktop Computer';
  }

  function getBrowserName(userAgent?: string): string {
    if (!userAgent) return 'Unknown Browser';
    
    const ua = userAgent.toLowerCase();
    
    if (ua.includes('chrome')) return 'Google Chrome';
    if (ua.includes('firefox')) return 'Mozilla Firefox';
    if (ua.includes('safari') && !ua.includes('chrome')) return 'Safari';
    if (ua.includes('edge')) return 'Microsoft Edge';
    if (ua.includes('opera')) return 'Opera';
    
    return 'Unknown Browser';
  }

  function formatLastActivity(activityTime: string): string {
    try {
      const date = new Date(activityTime);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
      if (diffDays < 30) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
      
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  }

  function getLocationFromIP(ipAddress?: string): string {
    if (!ipAddress) return 'Unknown Location';
    
    // This is a placeholder - in a real app you might use a geolocation service
    // For localhost/development
    if (ipAddress === '127.0.0.1' || ipAddress === '::1' || ipAddress.startsWith('192.168.')) {
      return 'Local Network';
    }
    
    return 'Unknown Location';
  }
</script>

<div class="max-w-4xl mx-auto">
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <div>
      <h2 class="text-2xl font-bold text-foreground flex items-center">
        <Monitor class="w-6 h-6 mr-2" />
        Active Sessions
      </h2>
      <p class="text-muted-foreground">
        Manage your active login sessions across devices
      </p>
    </div>
    
    <Button
      variant="outline"
      onclick={refreshSessions}
      loading={isRefreshing}
      disabled={isLoading || isRefreshing}
      class="flex items-center"
    >
      <RefreshCw class="w-4 h-4 mr-2" />
      Refresh
    </Button>
  </div>

  <!-- Messages -->
  {#if successMessage}
    <div class="mb-6 rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 flex items-start space-x-2">
      <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
      <p class="text-sm text-green-800 dark:text-green-200">
        {successMessage}
      </p>
    </div>
  {/if}

  {#if error}
    <div class="mb-6 rounded-md bg-destructive/10 border border-destructive/20 p-3 flex items-start space-x-2">
      <AlertCircle class="w-4 h-4 text-destructive mt-0.5 flex-shrink-0" />
      <p class="text-sm text-destructive">
        {error}
      </p>
    </div>
  {/if}

  <!-- Loading state -->
  {#if isLoading}
    <div class="space-y-4">
      {#each Array(3) as _}
        <div class="bg-card border border-border rounded-lg p-6">
          <div class="animate-pulse">
            <div class="flex items-start space-x-4">
              <div class="w-12 h-12 bg-muted rounded-lg"></div>
              <div class="flex-1 space-y-3">
                <div class="h-4 bg-muted rounded w-1/3"></div>
                <div class="h-3 bg-muted rounded w-1/2"></div>
                <div class="h-3 bg-muted rounded w-2/3"></div>
              </div>
              <div class="w-24 h-8 bg-muted rounded"></div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else if $userSessions.length === 0}
    <!-- No sessions -->
    <div class="text-center py-12">
      <Monitor class="w-16 h-16 text-muted-foreground mx-auto mb-4" />
      <h3 class="text-lg font-medium text-foreground mb-2">No Active Sessions</h3>
      <p class="text-muted-foreground">
        You don't have any active sessions at the moment.
      </p>
    </div>
  {:else}
    <!-- Sessions list -->
    <div class="space-y-4">
      {#each $userSessions as session (session.id)}
        {@const DeviceIcon = getDeviceIcon(session.user_agent)}
        <div class="bg-card border border-border rounded-lg p-6 transition-colors">
          <div class="flex items-start justify-between">
            <div class="flex items-start space-x-4">
              <!-- Device icon -->
              <div class="flex-shrink-0">
                <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                  <svelte:component this={DeviceIcon} class="w-6 h-6 text-primary" />
                </div>
              </div>
              
              <!-- Session details -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center space-x-2 mb-2">
                  <h3 class="text-lg font-medium text-foreground">
                    {getDeviceType(session.user_agent)}
                  </h3>
                  {#if session.is_current}
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      <div class="w-2 h-2 bg-green-400 rounded-full mr-1"></div>
                      Current Session
                    </span>
                  {/if}
                </div>
                
                <div class="space-y-1 text-sm text-muted-foreground">
                  <!-- Browser -->
                  <div class="flex items-center space-x-2">
                    <Globe class="w-4 h-4 flex-shrink-0" />
                    <span>{getBrowserName(session.user_agent)}</span>
                  </div>
                  
                  <!-- Location -->
                  {#if session.ip_address}
                    <div class="flex items-center space-x-2">
                      <MapPin class="w-4 h-4 flex-shrink-0" />
                      <span>{getLocationFromIP(session.ip_address)} ({session.ip_address})</span>
                    </div>
                  {/if}
                  
                  <!-- Last activity -->
                  <div class="flex items-center space-x-2">
                    <Clock class="w-4 h-4 flex-shrink-0" />
                    <span>Last active {formatLastActivity(session.last_activity)}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Actions -->
            <div class="flex items-start space-x-2">
              {#if !session.is_current}
                <Button
                  variant="outline"
                  size="sm"
                  onclick={() => revokeSession(session.id)}
                  loading={revokingSessionId === session.id}
                  disabled={revokingSessionId !== null}
                  class="flex items-center text-destructive border-destructive/20 hover:bg-destructive hover:text-destructive-foreground"
                >
                  {#if revokingSessionId === session.id}
                    <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  {:else}
                    <LogOut class="w-4 h-4 mr-2" />
                  {/if}
                  End Session
                </Button>
              {:else}
                <div class="text-xs text-muted-foreground bg-muted px-3 py-2 rounded-md">
                  Current Session
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
    
    <!-- Security notice -->
    <div class="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
      <div class="flex items-start space-x-3">
        <AlertTriangle class="w-5 h-5 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
        <div class="flex-1">
          <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">
            Security Tip
          </h4>
          <p class="text-xs text-yellow-700 dark:text-yellow-300">
            If you see any unfamiliar sessions, end them immediately and consider changing your password. 
            Always log out from public or shared devices.
          </p>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Pulse animation for loading */
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

  /* Spin animation */
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }
</style>