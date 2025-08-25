<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends HTMLInputAttributes {
		class?: string;
		error?: string;
		value?: string;
	}

	let { 
		class: className = '', 
		type = 'text',
		error,
		value = $bindable(''),
		...restProps 
	}: Props = $props();
</script>

<div class="w-full">
	<input
		{type}
		bind:value
		class={cn(
			'flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
			error && 'border-destructive focus-visible:ring-destructive',
			className
		)}
		{...restProps}
	/>
	{#if error}
		<p class="mt-1 text-xs text-destructive">{error}</p>
	{/if}
</div>