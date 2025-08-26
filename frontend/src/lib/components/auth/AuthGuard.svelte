<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authState, canAccessApp, authActions, isAccountLocked } from '$stores/auth';
	import LoadingSpinner from '../ui/LoadingSpinner.svelte';
	import { Shield, AlertTriangle, RefreshCw } from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';

	interface Props {
		children: any;
		requireAuth?: boolean;
		requireVerification?: boolean;
		fallbackPath?: string;
	}

	let { 
		children, 
		requireAuth = true, 
		requireVerification = false, 
		fallbackPath = '/login' 
	}: Props = $props();

	let authCheckComplete = $state(false);
	let retryCount = $state(0);
	const MAX_RETRIES = 3;

	// Handle authentication and routing
	$effect(() => {
		if ($authState.isLoading) return;
		
		authCheckComplete = true;
		
		// If authentication is not required, allow access
		if (!requireAuth || !$authState.authRequired) {
			return;
		}
		
		// Check if user can access the app
		if (!$canAccessApp && !isOnPublicPage()) {
			// Save current path for post-login redirect
			if ($page.url.pathname !== '/' && !$page.url.pathname.startsWith('/login')) {
				authActions.setRedirectPath($page.url.pathname + $page.url.search);
			}
			goto(fallbackPath);
			return;
		}
		
		// Check email verification if required
		if (requireVerification && $authState.user && !$authState.user.is_verified) {
			// Could redirect to verification page here
			console.warn('User email verification required');
		}
	});

	function isOnPublicPage(): boolean {
		const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password'];
		return publicPaths.some(path => $page.route.id?.includes(path));
	}

	async function retryAuthCheck() {
		if (retryCount >= MAX_RETRIES) return;
		
		retryCount++;
		try {
			await authActions.checkAuthStatus();
		} catch (error) {
			console.error('Auth retry failed:', error);
		}
	}

	function clearAuthError() {
		authActions.clearError();
	}
</script>

{#if $authState.isLoading && !authCheckComplete}
	<!-- Initial loading state -->
	<div class="flex h-screen items-center justify-center bg-background">
		<div class="text-center">
			<div class="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
				<Shield class="w-8 h-8 text-primary animate-pulse" />
			</div>
			<LoadingSpinner size="lg" class="mb-4" />
			<p class="text-muted-foreground">Checking authentication...</p>
		</div>
	</div>
{:else if $authState.error && !$canAccessApp && !isOnPublicPage()}
	<!-- Auth error state -->
	<div class="flex h-screen items-center justify-center bg-background p-4">
		<div class="max-w-md w-full text-center space-y-6">
			<div class="inline-flex items-center justify-center w-16 h-16 bg-destructive/10 rounded-full mb-4">
				<AlertTriangle class="w-8 h-8 text-destructive" />
			</div>
			
			<div>
				<h2 class="text-2xl font-bold text-foreground mb-2">Authentication Error</h2>
				<p class="text-muted-foreground mb-4">
					{$authState.error}
				</p>
			</div>
			
			<div class="space-y-3">
				{#if retryCount < MAX_RETRIES}
					<Button
						onclick={retryAuthCheck}
						class="w-full"
						loading={$authState.isLoading}
					>
						<RefreshCw class="w-4 h-4 mr-2" />
						Try Again ({MAX_RETRIES - retryCount} attempts left)
					</Button>
				{/if}
				
				<Button
					variant="outline"
					onclick={() => goto(fallbackPath)}
					class="w-full"
				>
					Go to Login
				</Button>
				
				<Button
					variant="ghost"
					onclick={clearAuthError}
					class="w-full text-sm"
				>
					Dismiss Error
				</Button>
			</div>
		</div>
	</div>
{:else if $isAccountLocked && !isOnPublicPage()}
	<!-- Account locked state -->
	<div class="flex h-screen items-center justify-center bg-background p-4">
		<div class="max-w-md w-full text-center space-y-6">
			<div class="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full mb-4">
				<Shield class="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
			</div>
			
			<div>
				<h2 class="text-2xl font-bold text-foreground mb-2">Account Temporarily Locked</h2>
				<p class="text-muted-foreground mb-4">
					Your account has been temporarily locked due to multiple failed login attempts. 
					Please wait a few minutes before trying again.
				</p>
			</div>
			
			<Button
				variant="outline"
				onclick={() => goto(fallbackPath)}
				class="w-full"
			>
				Go to Login
			</Button>
		</div>
	</div>
{:else if requireVerification && $authState.user && !$authState.user.is_verified && $canAccessApp}
	<!-- Email verification required -->
	<div class="flex h-screen items-center justify-center bg-background p-4">
		<div class="max-w-md w-full text-center space-y-6">
			<div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
				<Shield class="w-8 h-8 text-blue-600 dark:text-blue-400" />
			</div>
			
			<div>
				<h2 class="text-2xl font-bold text-foreground mb-2">Email Verification Required</h2>
				<p class="text-muted-foreground mb-4">
					Please verify your email address to access this feature.
					Check your inbox for a verification email.
				</p>
			</div>
			
			<div class="space-y-3">
				<Button
					class="w-full"
					onclick={() => {
						// TODO: Implement resend verification email
						console.log('Resend verification email');
					}}
				>
					Resend Verification Email
				</Button>
				
				<Button
					variant="outline"
					onclick={() => {
						// Allow access but with limited functionality
						// This is optional based on your requirements
					}}
					class="w-full"
				>
					Continue with Limited Access
				</Button>
			</div>
		</div>
	</div>
{:else if !requireAuth || $canAccessApp || isOnPublicPage()}
	<!-- Render children if auth not required, user can access, or on public page -->
	{@render children()}
{:else}
	<!-- Fallback loading state while redirecting -->
	<div class="flex h-screen items-center justify-center bg-background">
		<div class="text-center">
			<LoadingSpinner size="lg" class="mb-4" />
			<p class="text-muted-foreground">Redirecting...</p>
		</div>
	</div>
{/if}