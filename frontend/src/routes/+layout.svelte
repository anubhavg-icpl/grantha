<script lang="ts">
	import '../app.pcss';
	import AuthGuard from '$lib/components/auth/AuthGuard.svelte';
	import AppLayout from '$lib/components/layout/AppLayout.svelte';

	interface Props {
		children: any;
	}

	let { children }: Props = $props();
</script>

<svelte:head>
	<title>Grantha - AI Platform</title>
</svelte:head>

<AuthGuard>
	<AppLayout>
		{@render children()}
	</AppLayout>
</AuthGuard>