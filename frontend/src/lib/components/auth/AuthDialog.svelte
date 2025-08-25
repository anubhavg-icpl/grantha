<script lang="ts">
	import { authState, authActions } from '$stores/auth';
	import Button from '../ui/button.svelte';
	import Input from '../ui/input.svelte';
	import { Lock, Shield, Key } from 'lucide-svelte';

	let authCode = $state('');
	let isValidating = $state(false);

	async function handleSubmit() {
		if (!authCode.trim()) return;
		
		isValidating = true;
		try {
			await authActions.validateCode(authCode.trim());
		} finally {
			isValidating = false;
		}
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			handleSubmit();
		}
	}
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
	<div class="w-full max-w-md space-y-8 rounded-lg border bg-card p-8 shadow-lg">
		<div class="text-center">
			<div class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
				<Shield class="h-8 w-8 text-primary" />
			</div>
			<h1 class="text-2xl font-bold text-foreground">Authentication Required</h1>
			<p class="mt-2 text-sm text-muted-foreground">
				Enter your authorization code to access Grantha
			</p>
		</div>

		<form class="space-y-6" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
			<div>
				<label for="auth-code" class="sr-only">Authorization Code</label>
				<div class="relative">
					<div class="absolute inset-y-0 left-0 flex items-center pl-3">
						<Key class="h-4 w-4 text-muted-foreground" />
					</div>
					<Input
						id="auth-code"
						type="password"
						placeholder="Enter authorization code"
						bind:value={authCode}
						onkeydown={handleKeyDown}
						error={$authState.error || undefined}
						class="pl-10"
						disabled={isValidating}
						autofocus
					/>
				</div>
			</div>

			<Button
				type="submit"
				class="w-full"
				loading={isValidating}
				disabled={!authCode.trim() || isValidating}
			>
				<Lock class="mr-2 h-4 w-4" />
				Authenticate
			</Button>

			{#if $authState.error}
				<div class="rounded-md bg-destructive/10 border border-destructive/20 p-3">
					<p class="text-sm text-destructive">{$authState.error}</p>
				</div>
			{/if}
		</form>

		<div class="text-center">
			<p class="text-xs text-muted-foreground">
				Need help? Check your configuration or contact your administrator.
			</p>
		</div>
	</div>
</div>