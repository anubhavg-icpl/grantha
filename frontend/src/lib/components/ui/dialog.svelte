<script lang="ts">
	import { cn } from '$lib/utils';
	import { X } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		open?: boolean;
		class?: string;
		children?: any;
		title?: string;
		description?: string;
	}

	let { 
		open = false, 
		class: className = '', 
		children, 
		title,
		description 
	}: Props = $props();

	const dispatch = createEventDispatcher();

	function closeDialog() {
		open = false;
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			closeDialog();
		}
	}

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			closeDialog();
		}
	}
</script>

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
		onclick={handleBackdropClick}
		onkeydown={handleKeydown}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<!-- Dialog Content -->
		<div class="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 p-6">
			<div
				class={cn(
					'relative rounded-lg border bg-background p-6 shadow-lg',
					className
				)}
			>
				<!-- Close Button -->
				<button
					type="button"
					class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
					onclick={closeDialog}
				>
					<X class="h-4 w-4" />
					<span class="sr-only">Close</span>
				</button>

				<!-- Header -->
				{#if title || description}
					<div class="mb-4">
						{#if title}
							<h2 class="text-lg font-semibold text-foreground">{title}</h2>
						{/if}
						{#if description}
							<p class="text-sm text-muted-foreground mt-1">{description}</p>
						{/if}
					</div>
				{/if}

				<!-- Content -->
				<div>
					{@render children()}
				</div>
			</div>
		</div>
	</div>
{/if}