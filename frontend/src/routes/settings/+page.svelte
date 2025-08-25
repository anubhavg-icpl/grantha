<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		Settings, 
		User, 
		Moon, 
		Sun, 
		Monitor, 
		Save, 
		RotateCcw,
		Bell,
		Shield,
		Database,
		Palette
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Select from '$lib/components/ui/select.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Card from '$lib/components/ui/card.svelte';

	interface UserSettings {
		theme: 'light' | 'dark' | 'system';
		language: string;
		notifications: boolean;
		autoSave: boolean;
		maxTokens: number;
		temperature: number;
		apiTimeout: number;
	}

	let settings = $state<UserSettings>({
		theme: 'system',
		language: 'en',
		notifications: true,
		autoSave: true,
		maxTokens: 4096,
		temperature: 0.7,
		apiTimeout: 30
	});

	const initialSettings: UserSettings = {
		theme: 'system',
		language: 'en',
		notifications: true,
		autoSave: true,
		maxTokens: 4096,
		temperature: 0.7,
		apiTimeout: 30
	};
	
	let originalSettings = $state<UserSettings>({ ...initialSettings });
	let hasChanges = $derived(JSON.stringify(settings) !== JSON.stringify(originalSettings));
	let isSaving = $state(false);

	const themeOptions = [
		{ value: 'light', label: 'Light' },
		{ value: 'dark', label: 'Dark' },
		{ value: 'system', label: 'System' }
	];

	const languageOptions = [
		{ value: 'en', label: 'English' },
		{ value: 'es', label: 'Spanish' },
		{ value: 'fr', label: 'French' },
		{ value: 'de', label: 'German' },
		{ value: 'zh', label: 'Chinese' },
		{ value: 'ja', label: 'Japanese' }
	];

	const saveSettings = async () => {
		isSaving = true;
		try {
			// Simulate API call
			await new Promise(resolve => setTimeout(resolve, 1000));
			
			// Apply theme immediately
			if (settings.theme === 'dark') {
				document.documentElement.classList.add('dark');
			} else if (settings.theme === 'light') {
				document.documentElement.classList.remove('dark');
			} else {
				// System theme
				const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
				document.documentElement.classList.toggle('dark', prefersDark);
			}
			
			localStorage.setItem('grantha-theme', settings.theme);
			localStorage.setItem('grantha-settings', JSON.stringify(settings));
			
			originalSettings = { ...settings };
		} catch (error) {
			console.error('Failed to save settings:', error);
		} finally {
			isSaving = false;
		}
	};

	const resetSettings = () => {
		settings = { ...originalSettings };
	};

	const resetToDefaults = () => {
		settings = {
			theme: 'system',
			language: 'en',
			notifications: true,
			autoSave: true,
			maxTokens: 4096,
			temperature: 0.7,
			apiTimeout: 30
		};
	};

	onMount(() => {
		// Load settings from localStorage
		const savedSettings = localStorage.getItem('grantha-settings');
		const savedTheme = localStorage.getItem('grantha-theme') as 'light' | 'dark' | 'system' || 'system';
		
		if (savedSettings) {
			try {
				const parsed = JSON.parse(savedSettings);
				settings = { ...settings, ...parsed, theme: savedTheme };
				originalSettings = { ...settings };
			} catch (e) {
				console.warn('Failed to load saved settings');
			}
		} else {
			settings.theme = savedTheme;
			originalSettings = { ...settings };
		}
	});
</script>

<svelte:head>
	<title>Settings - Grantha</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<h1 class="text-3xl font-bold text-foreground mb-2">Settings</h1>
		<p class="text-muted-foreground">
			Configure your preferences and application settings.
		</p>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
		<!-- Settings Forms -->
		<div class="lg:col-span-2 space-y-6">
			<!-- Appearance Settings -->
			<Card class="p-6">
				<div class="flex items-center mb-4">
					<Palette class="mr-2 h-5 w-5 text-primary" />
					<h2 class="text-lg font-semibold">Appearance</h2>
				</div>
				
				<div class="space-y-4">
					<div>
						<label for="theme" class="block text-sm font-medium mb-2">
							Theme
						</label>
						<Select
							id="theme"
							bind:value={settings.theme}
							options={themeOptions}
							placeholder="Select theme..."
						/>
					</div>

					<div>
						<label for="language" class="block text-sm font-medium mb-2">
							Language
						</label>
						<Select
							id="language"
							bind:value={settings.language}
							options={languageOptions}
							placeholder="Select language..."
						/>
					</div>
				</div>
			</Card>

			<!-- Behavior Settings -->
			<Card class="p-6">
				<div class="flex items-center mb-4">
					<Settings class="mr-2 h-5 w-5 text-primary" />
					<h2 class="text-lg font-semibold">Behavior</h2>
				</div>
				
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<div>
							<label for="notifications" class="text-sm font-medium">
								Enable Notifications
							</label>
							<p class="text-xs text-muted-foreground">
								Get notified about important updates and completions
							</p>
						</div>
						<input
							id="notifications"
							type="checkbox"
							bind:checked={settings.notifications}
							class="rounded border-input"
						/>
					</div>

					<div class="flex items-center justify-between">
						<div>
							<label for="autoSave" class="text-sm font-medium">
								Auto-save Conversations
							</label>
							<p class="text-xs text-muted-foreground">
								Automatically save chat conversations and progress
							</p>
						</div>
						<input
							id="autoSave"
							type="checkbox"
							bind:checked={settings.autoSave}
							class="rounded border-input"
						/>
					</div>
				</div>
			</Card>

			<!-- AI Model Settings -->
			<Card class="p-6">
				<div class="flex items-center mb-4">
					<Shield class="mr-2 h-5 w-5 text-primary" />
					<h2 class="text-lg font-semibold">AI Model Defaults</h2>
				</div>
				
				<div class="space-y-4">
					<div>
						<label for="maxTokens" class="block text-sm font-medium mb-2">
							Max Tokens: {settings.maxTokens}
						</label>
						<input
							id="maxTokens"
							type="range"
							min="1024"
							max="8192"
							step="256"
							bind:value={settings.maxTokens}
							class="w-full"
						/>
						<div class="flex justify-between text-xs text-muted-foreground mt-1">
							<span>1K</span>
							<span>8K</span>
						</div>
					</div>

					<div>
						<label for="temperature" class="block text-sm font-medium mb-2">
							Temperature: {settings.temperature}
						</label>
						<input
							id="temperature"
							type="range"
							min="0"
							max="2"
							step="0.1"
							bind:value={settings.temperature}
							class="w-full"
						/>
						<div class="flex justify-between text-xs text-muted-foreground mt-1">
							<span>Focused</span>
							<span>Creative</span>
						</div>
					</div>

					<div>
						<label for="apiTimeout" class="block text-sm font-medium mb-2">
							API Timeout (seconds)
						</label>
						<Input
							id="apiTimeout"
							type="number"
							min="10"
							max="300"
							value={settings.apiTimeout.toString()}
							oninput={(e) => settings.apiTimeout = Number((e.target as HTMLInputElement).value)}
							class="w-32"
						/>
					</div>
				</div>
			</Card>
		</div>

		<!-- Settings Summary & Actions -->
		<div class="space-y-6">
			<!-- Current Settings Summary -->
			<Card class="p-6">
				<div class="flex items-center mb-4">
					<User class="mr-2 h-5 w-5 text-primary" />
					<h2 class="text-lg font-semibold">Current Settings</h2>
				</div>
				
				<div class="space-y-3">
					<div class="flex items-center justify-between">
						<span class="text-sm text-muted-foreground">Theme</span>
						<Badge variant="outline">
							<div class="flex items-center gap-1">
								{#if settings.theme === 'light'}
									<Sun class="w-3 h-3" />
								{:else if settings.theme === 'dark'}
									<Moon class="w-3 h-3" />
								{:else}
									<Monitor class="w-3 h-3" />
								{/if}
								{settings.theme}
							</div>
						</Badge>
					</div>
					
					<div class="flex items-center justify-between">
						<span class="text-sm text-muted-foreground">Language</span>
						<Badge variant="secondary">
							{languageOptions.find(l => l.value === settings.language)?.label}
						</Badge>
					</div>
					
					<div class="flex items-center justify-between">
						<span class="text-sm text-muted-foreground">Notifications</span>
						<Badge variant={settings.notifications ? "success" : "secondary"}>
							{#if settings.notifications}
								<Bell class="w-3 h-3 mr-1" />
								Enabled
							{:else}
								Disabled
							{/if}
						</Badge>
					</div>
					
					<div class="flex items-center justify-between">
						<span class="text-sm text-muted-foreground">Auto-save</span>
						<Badge variant={settings.autoSave ? "success" : "secondary"}>
							{#if settings.autoSave}
								<Database class="w-3 h-3 mr-1" />
								Enabled
							{:else}
								Disabled
							{/if}
						</Badge>
					</div>
				</div>
			</Card>

			<!-- Actions -->
			<Card class="p-6">
				<h3 class="text-lg font-semibold mb-4">Actions</h3>
				
				<div class="space-y-3">
					<Button
						variant="default"
						class="w-full"
						disabled={!hasChanges || isSaving}
						loading={isSaving}
						onclick={saveSettings}
					>
						<Save class="mr-2 h-4 w-4" />
						Save Changes
					</Button>
					
					<Button
						variant="outline"
						class="w-full"
						disabled={!hasChanges}
						onclick={resetSettings}
					>
						<RotateCcw class="mr-2 h-4 w-4" />
						Reset Changes
					</Button>
					
					<Button
						variant="destructive"
						class="w-full"
						onclick={resetToDefaults}
					>
						Reset to Defaults
					</Button>
				</div>
			</Card>
		</div>
	</div>

	<!-- Status Messages -->
	{#if hasChanges}
		<div class="fixed bottom-4 right-4 bg-accent border border-accent-foreground/20 text-accent-foreground rounded-lg p-4 shadow-lg">
			<p class="text-sm font-medium">Unsaved changes detected</p>
			<p class="text-xs opacity-75">Remember to save your settings</p>
		</div>
	{/if}
</div>