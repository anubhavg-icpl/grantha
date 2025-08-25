<script lang="ts">
	import { cn } from '$lib/utils';
	import { tv, type VariantProps } from 'tailwind-variants';
	import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	const toastVariants = tv({
		base: 'group pointer-events-auto relative flex w-full items-center justify-between space-x-2 overflow-hidden rounded-md border p-4 pr-6 shadow-lg transition-all',
		variants: {
			variant: {
				default: 'border bg-background text-foreground',
				destructive: 'destructive border-destructive bg-destructive text-destructive-foreground',
				success: 'border-green-500 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-50',
				warning: 'border-yellow-500 bg-yellow-50 text-yellow-900 dark:bg-yellow-950 dark:text-yellow-50',
				info: 'border-blue-500 bg-blue-50 text-blue-900 dark:bg-blue-950 dark:text-blue-50'
			}
		},
		defaultVariants: {
			variant: 'default'
		}
	});

	type Variant = VariantProps<typeof toastVariants>['variant'];

	interface Props {
		variant?: Variant;
		title?: string;
		description?: string;
		class?: string;
		duration?: number;
		dismissible?: boolean;
	}

	let {
		variant = 'default',
		title,
		description,
		class: className = '',
		duration = 5000,
		dismissible = true
	}: Props = $props();

	const dispatch = createEventDispatcher();

	let visible = $state(true);
	let timeoutId: ReturnType<typeof setTimeout> | null = null;

	function dismiss() {
		visible = false;
		dispatch('dismiss');
	}

	function getIcon(variant: Variant) {
		switch (variant) {
			case 'destructive':
				return AlertCircle;
			case 'success':
				return CheckCircle;
			case 'warning':
				return AlertTriangle;
			case 'info':
				return Info;
			default:
				return Info;
		}
	}

	// Auto dismiss
	if (duration > 0) {
		timeoutId = setTimeout(() => {
			dismiss();
		}, duration);
	}

	// Clear timeout on manual dismiss
	function handleDismiss() {
		if (timeoutId) {
			clearTimeout(timeoutId);
			timeoutId = null;
		}
		dismiss();
	}
</script>

{#if visible}
	<div class={toastVariants({ variant, className })}>
		<div class="flex items-center space-x-2">
			{#if variant}
				{@const IconComponent = getIcon(variant)}
				<IconComponent class="h-4 w-4 flex-shrink-0" />
			{/if}
			<div class="grid gap-1">
				{#if title}
					<div class="text-sm font-semibold">{title}</div>
				{/if}
				{#if description}
					<div class="text-sm opacity-90">{description}</div>
				{/if}
			</div>
		</div>
		{#if dismissible}
			<button
				type="button"
				class="absolute right-1 top-1 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-1 group-hover:opacity-100"
				onclick={handleDismiss}
			>
				<X class="h-4 w-4" />
			</button>
		{/if}
	</div>
{/if}