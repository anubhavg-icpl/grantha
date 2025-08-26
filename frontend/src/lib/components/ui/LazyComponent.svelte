<script lang="ts">
	import { onMount } from 'svelte';
	import { createIntersectionLazyLoader, LazyLoadPerformanceMonitor } from '$utils/lazy-loader';
	import LoadingSpinner from './LoadingSpinner.svelte';
	import type { ComponentType } from 'svelte';

	interface Props {
		importFn: () => Promise<{ default: ComponentType<any> }>;
		props?: Record<string, any>;
		loadOnMount?: boolean;
		threshold?: number;
		rootMargin?: string;
		delay?: number;
		componentName?: string;
	}

	let {
		importFn,
		props = {},
		loadOnMount = false,
		threshold = 0.1,
		rootMargin = '50px',
		delay = 0,
		componentName = 'UnknownComponent'
	}: Props = $props();

	// State
	let isLoading = $state(false);
	let error: string | null = $state(null);
	let component: ComponentType<any> | null = $state(null);
	let containerElement: HTMLElement;

	// Performance monitoring
	const perfMonitor = LazyLoadPerformanceMonitor.getInstance();

	// Create intersection lazy loader
	const lazyLoader = createIntersectionLazyLoader(importFn, {
		threshold,
		rootMargin,
		delay
	});

	async function loadComponent() {
		if (component || isLoading) return;

		isLoading = true;
		error = null;
		perfMonitor.startLoad(componentName);

		try {
			if (loadOnMount) {
				// Load immediately
				const module = await importFn();
				component = module.default;
			} else {
				// Load when visible
				component = await lazyLoader.loadWhenVisible(containerElement);
			}
			perfMonitor.endLoad(componentName);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load component';
			console.error(`Failed to load ${componentName}:`, err);
		} finally {
			isLoading = false;
		}
	}

	onMount(() => {
		if (loadOnMount) {
			loadComponent();
		} else {
			// Set up intersection observer
			loadComponent();
		}
	});
</script>

<div bind:this={containerElement} class="lazy-component-wrapper">
	{#if error}
		<div class="error-container p-4 border border-red-200 rounded-lg bg-red-50">
			<p class="text-red-800 text-sm">
				⚠️ Failed to load {componentName}
			</p>
			<p class="text-red-600 text-xs mt-1">{error}</p>
			<button 
				class="mt-2 px-3 py-1 text-xs bg-red-100 hover:bg-red-200 rounded"
				onclick={loadComponent}
			>
				Retry
			</button>
		</div>
	{:else if isLoading}
		<div class="loading-container p-4 flex items-center justify-center">
			<LoadingSpinner size="sm" />
			<span class="ml-2 text-sm text-gray-600">Loading {componentName}...</span>
		</div>
	{:else if component}
		<component {...props}></component>
	{:else}
		<div class="placeholder-container p-4 bg-gray-50 rounded-lg">
			<div class="animate-pulse">
				<div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
				<div class="h-4 bg-gray-200 rounded w-1/2"></div>
			</div>
		</div>
	{/if}
</div>

<style>
	.lazy-component-wrapper {
		min-height: 2rem; /* Prevent layout shift */
	}

	.loading-container {
		min-height: 100px;
	}

	.error-container {
		min-height: 80px;
	}

	.placeholder-container {
		min-height: 60px;
	}
</style>