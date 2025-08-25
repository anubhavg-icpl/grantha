<script lang="ts">
	import { page } from '$app/stores';
	import { authActions } from '$lib/stores/auth.js';
	import Sidebar from './Sidebar.svelte';
	import Header from './Header.svelte';
	import { writable } from 'svelte/store';

	interface Props {
		children: any;
	}

	let { children }: Props = $props();

	const sidebarOpen = writable(true);

	// Close sidebar on mobile when route changes
	$effect(() => {
		if ($page.route) {
			if (typeof window !== 'undefined' && window.innerWidth < 1024) {
				$sidebarOpen = false;
			}
		}
	});
</script>

<div class="flex h-screen bg-background">
	<!-- Sidebar -->
	<Sidebar bind:open={$sidebarOpen} />
	
	<!-- Main content area -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Header -->
		<Header 
			onToggleSidebar={() => sidebarOpen.update(open => !open)}
			{sidebarOpen}
		/>
		
		<!-- Page content -->
		<main class="flex-1 overflow-auto">
			<div class="container mx-auto px-4 py-6">
				{@render children()}
			</div>
		</main>
	</div>
</div>

<!-- Mobile sidebar overlay -->
{#if $sidebarOpen}
	<div 
		class="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
		role="button"
		tabindex="0"
		onclick={() => sidebarOpen.set(false)}
		onkeydown={(e) => e.key === 'Escape' && sidebarOpen.set(false)}
	></div>
{/if}