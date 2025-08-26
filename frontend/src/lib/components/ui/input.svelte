<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends HTMLInputAttributes {
		class?: string;
		error?: string;
		value?: string;
		label?: string;
		hideLabel?: boolean;
	}

	let { 
		class: className = '', 
		type = 'text',
		error,
		value = $bindable(''),
		label,
		hideLabel = false,
		...restProps 
	}: Props = $props();

	// Generate unique ID for accessibility
	const inputId = restProps.id || `input-${crypto.randomUUID()}`;
</script>

<div class="w-full">
	{#if label && !hideLabel}
		<label for={inputId} class="block text-sm font-medium text-foreground mb-1">
			{label}
		</label>
	{/if}
	<input
		id={inputId}
		{type}
		bind:value
		aria-describedby={error ? `${inputId}-error` : undefined}
		aria-invalid={error ? 'true' : 'false'}
		class={cn(
			'flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
			error && 'border-destructive focus-visible:ring-destructive',
			className
		)}
		{...restProps}
	/>
	{#if error}
		<p id="{inputId}-error" class="mt-1 text-xs text-destructive" role="alert">{error}</p>
	{/if}
</div>