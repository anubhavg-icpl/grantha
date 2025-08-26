<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import '../app.pcss';
	import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
	import AppLayout from '$lib/components/layout/AppLayout.svelte';
	import { httpInterceptor } from '$lib/utils/http-interceptor';

	interface Props {
		children: any;
	}

	let { children }: Props = $props();

	// Check if we're on a page that should skip the main app layout
	const isLoginPage = $derived($page.route.id?.includes('/login'));

	// Initialize HTTP interceptor and auth handlers
	onMount(() => {
		// HTTP interceptor is automatically initialized when imported
		
		// Set up auth failure event listener
		const handleAuthFailure = (event: CustomEvent) => {
			console.log('Authentication failure detected:', event.detail);
		};
		
		window.addEventListener('auth:failure', handleAuthFailure as EventListener);
		
		return () => {
			window.removeEventListener('auth:failure', handleAuthFailure as EventListener);
		};
	});
</script>

<svelte:head>
	<title>Grantha - AI Platform</title>
</svelte:head>

{#if isLoginPage}
	<!-- Login page has its own layout -->
	{@render children()}
{:else}
	<!-- Normal app pages with auth guard and app layout -->
	<AuthGuard>
		<AppLayout>
			{@render children()}
		</AppLayout>
	</AuthGuard>
{/if}