<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authState, canAccessApp, authActions } from '$stores/auth';
	import LoadingSpinner from '../ui/LoadingSpinner.svelte';

	interface Props {
		children: any;
	}

	let { children }: Props = $props();

	// Redirect to login if not authenticated and not already on login page
	$effect(() => {
		if (!$authState.isLoading && !$canAccessApp && !$page.route.id?.includes('/login')) {
			goto('/login');
		}
	});
</script>

{#if $authState.isLoading}
	<div class="flex h-screen items-center justify-center bg-background">
		<LoadingSpinner size="lg" />
	</div>
{:else if $canAccessApp || $page.route.id?.includes('/login')}
	{@render children()}
{:else}
	<!-- Fallback loading state while redirecting -->
	<div class="flex h-screen items-center justify-center bg-background">
		<LoadingSpinner size="lg" />
	</div>
{/if}