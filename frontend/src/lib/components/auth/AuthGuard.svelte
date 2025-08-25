<script lang="ts">
	import { authState, canAccessApp, authActions } from '$stores/auth';
	import AuthDialog from './AuthDialog.svelte';
	import LoadingSpinner from '../ui/LoadingSpinner.svelte';

	interface Props {
		children: any;
	}

	let { children }: Props = $props();
</script>

{#if $authState.isLoading}
	<div class="flex h-screen items-center justify-center">
		<LoadingSpinner size="lg" />
	</div>
{:else if $canAccessApp}
	{@render children()}
{:else}
	<AuthDialog />
{/if}