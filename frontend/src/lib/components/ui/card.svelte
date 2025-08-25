<script lang="ts">
	import { cn } from '$lib/utils';
	import type { HTMLAttributes } from 'svelte/elements';

	interface Props extends HTMLAttributes<HTMLDivElement> {
		class?: string;
		children?: any;
	}

	let { class: className = '', children, ...props }: Props = $props();
</script>

<div
	class={cn(
		"rounded-xl border bg-card text-card-foreground shadow",
		className
	)}
	{...props}
>
	{@render children()}
</div>