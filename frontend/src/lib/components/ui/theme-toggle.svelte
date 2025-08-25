<script lang="ts">
	import { toggleMode } from 'mode-watcher';
	import { Sun, Moon } from 'lucide-svelte';
	import { page } from '$app/stores';
	
	let isDark = $state(false);
	
	// Check initial theme from HTML class
	$effect(() => {
		if (typeof document !== 'undefined') {
			isDark = document.documentElement.classList.contains('dark');
		}
	});
	
	function handleToggle() {
		toggleMode();
		isDark = !isDark;
	}
</script>

<button
	type="button"
	class="theme-toggle-button cursor-pointer bg-transparent border border-japanese-border text-foreground hover:border-japanese-primary active:bg-japanese-secondary/10 rounded-md p-2 transition-all duration-300"
	title="Toggle theme"
	aria-label="Toggle theme"
	onclick={handleToggle}
>
	<!-- Japanese-inspired sun and moon icons -->
	<div class="relative w-5 h-5">
		<!-- Sun icon (light mode) -->
		<div class={`absolute inset-0 transition-opacity duration-300 ${isDark ? 'opacity-0' : 'opacity-100'}`}>
			<Sun class="w-5 h-5" aria-label="Light Mode" />
		</div>

		<!-- Moon icon (dark mode) -->
		<div class={`absolute inset-0 transition-opacity duration-300 ${isDark ? 'opacity-100' : 'opacity-0'}`}>
			<Moon class="w-5 h-5" aria-label="Dark Mode" />
		</div>
	</div>
</button>