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
	}

	let { 
		options = [], 
		value = $bindable(''), 
		placeholder = 'Select an option...',
		class: className = '',
		...props 
	}: Props = $props();
</script>

<div class="relative">
	<select
		class={cn(
			'flex h-9 w-full appearance-none rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
			className
		)}
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