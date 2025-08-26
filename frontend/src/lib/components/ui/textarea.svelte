<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	interface Props extends HTMLTextareaAttributes {
		class?: string;
		value?: string;
		label?: string;
		hideLabel?: boolean;
		error?: string;
	}

	let { 
		class: className = '', 
		value = '', 
		label,
		hideLabel = false,
		error,
		...props 
	}: Props = $props();

	// Generate unique ID for accessibility
	const textareaId = props.id || `textarea-${crypto.randomUUID()}`;
</script>

<div class="w-full">
	{#if label && !hideLabel}
		<label for={textareaId} class="block text-sm font-medium text-foreground mb-1">
			{label}
		</label>
	{/if}
	<textarea
		id={textareaId}
		class={cn(
			'flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
			error && 'border-destructive focus-visible:ring-destructive',
			className
		)}
		aria-describedby={error ? `${textareaId}-error` : undefined}
		aria-invalid={error ? 'true' : 'false'}
		bind:value
		{...props}
	></textarea>
	{#if error}
		<p id="{textareaId}-error" class="mt-1 text-xs text-destructive" role="alert">{error}</p>
	{/if}
</div>