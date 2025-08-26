<script lang="ts">
	import { cn } from '$lib/utils';
	import { ChevronDown } from 'lucide-svelte';
	import type { HTMLSelectAttributes } from 'svelte/elements';

	interface SelectOption {
		value: string;
		label: string;
		disabled?: boolean;
	}

	interface Props extends HTMLSelectAttributes {
		options: SelectOption[];
		value?: string;
		placeholder?: string;
		class?: string;
		label?: string;
		hideLabel?: boolean;
		error?: string;
	}

	let { 
		options = [], 
		value = $bindable(''), 
		placeholder = 'Select an option...',
		class: className = '',
		label,
		hideLabel = false,
		error,
		...props 
	}: Props = $props();

	// Generate unique ID for accessibility
	const selectId = props.id || `select-${crypto.randomUUID()}`;
</script>

<div class="w-full">
	{#if label && !hideLabel}
		<label for={selectId} class="block text-sm font-medium text-foreground mb-1">
			{label}
		</label>
	{/if}
	<div class="relative">
		<select
			id={selectId}
			class={cn(
				'flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
				error && 'border-destructive focus-visible:ring-destructive',
				className
			)}
			aria-describedby={error ? `${selectId}-error` : undefined}
			aria-invalid={error ? 'true' : 'false'}
			bind:value
			{...props}
		>
			{#if placeholder}
				<option value="" disabled>{placeholder}</option>
			{/if}
			{#each options as option}
				<option value={option.value} disabled={option.disabled}>
					{option.label}
				</option>
			{/each}
		</select>
		<ChevronDown class="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 opacity-50 pointer-events-none" />
	</div>
	{#if error}
		<p id="{selectId}-error" class="mt-1 text-xs text-destructive" role="alert">{error}</p>
	{/if}
</div>