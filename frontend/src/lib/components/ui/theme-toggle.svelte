<script lang="ts">
	import { mode, setMode } from 'mode-watcher';
	import { Sun, Moon } from 'lucide-svelte';
	import { get } from 'svelte/store';

	function toggleTheme() {
		const currentMode = get(mode);
		setMode(currentMode === 'dark' ? 'light' : 'dark');
	}
	
	$: currentMode = $mode;
</script>

<button
	type="button"
	class="theme-toggle-button cursor-pointer bg-transparent border border-japanese-border text-foreground hover:border-japanese-primary active:bg-japanese-secondary/10 rounded-md p-2 transition-all duration-300"
	title="Toggle theme"
	aria-label="Toggle theme"
	onclick={toggleTheme}
>
	<!-- Japanese-inspired sun and moon icons -->
	<div class="relative w-5 h-5">
		<!-- Sun icon (light mode) -->
		<div class={`absolute inset-0 transition-opacity duration-300 ${currentMode === 'dark' ? 'opacity-0' : 'opacity-100'}`}>
			<Sun class="w-5 h-5" aria-label="Light Mode" />
		</div>

		<!-- Moon icon (dark mode) -->
		<div class={`absolute inset-0 transition-opacity duration-300 ${currentMode === 'dark' ? 'opacity-100' : 'opacity-0'}`}>
			<Moon class="w-5 h-5" aria-label="Dark Mode" />
		</div>
	</div>
</button>