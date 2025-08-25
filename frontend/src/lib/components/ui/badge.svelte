<script lang="ts">
	import { tv, type VariantProps } from 'tailwind-variants';
	import type { HTMLAttributes } from 'svelte/elements';

	const badgeVariants = tv({
		base: 'inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
		variants: {
			variant: {
				default: 'border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/80',
				secondary: 'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
				destructive: 'border-transparent bg-destructive text-destructive-foreground shadow hover:bg-destructive/80',
				outline: 'text-foreground',
				success: 'border-transparent bg-green-500 text-white shadow hover:bg-green-500/80',
				warning: 'border-transparent bg-yellow-500 text-white shadow hover:bg-yellow-500/80'
			}
		},
		defaultVariants: {
			variant: 'default'
		}
	});

	type Variant = VariantProps<typeof badgeVariants>['variant'];

	interface Props extends HTMLAttributes<HTMLDivElement> {
		variant?: Variant;
		class?: string;
		children?: any;
	}

	let { 
		variant = 'default', 
		class: className = '',
		children,
		...props 
	}: Props = $props();
</script>

<div
	class={badgeVariants({ variant, className })}
	{...props}
>
	{@render children()}
</div>