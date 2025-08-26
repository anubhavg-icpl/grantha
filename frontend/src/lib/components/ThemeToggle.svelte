<script lang="ts">
  import { onMount } from 'svelte';
  import { Sun, Moon } from 'lucide-svelte';
  
  let theme: 'light' | 'dark' | 'system' = 'system';
  let actualTheme: 'light' | 'dark' = 'light';
  
  function applyTheme(newTheme: 'light' | 'dark' | 'system') {
    theme = newTheme;
    
    if (newTheme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      actualTheme = prefersDark ? 'dark' : 'light';
      document.documentElement.removeAttribute('data-theme');
    } else {
      actualTheme = newTheme;
      document.documentElement.setAttribute('data-theme', newTheme);
    }
    
    // Apply or remove dark class for Tailwind
    if (actualTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Save preference
    localStorage.setItem('theme-preference', theme);
  }
  
  function toggleTheme() {
    if (theme === 'light') {
      applyTheme('dark');
    } else if (theme === 'dark') {
      applyTheme('system');
    } else {
      applyTheme('light');
    }
  }
  
  onMount(() => {
    // Load saved preference or default to system
    const saved = localStorage.getItem('theme-preference') as 'light' | 'dark' | 'system' | null;
    applyTheme(saved || 'system');
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        actualTheme = mediaQuery.matches ? 'dark' : 'light';
        if (actualTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  });
</script>

<button
  on:click={toggleTheme}
  class="theme-toggle"
  aria-label="Toggle theme"
  title="{theme === 'system' ? 'System' : theme === 'light' ? 'Light' : 'Dark'} theme"
>
  {#if actualTheme === 'light'}
    <Sun class="w-5 h-5" />
  {:else}
    <Moon class="w-5 h-5" />
  {/if}
  {#if theme === 'system'}
    <span class="theme-indicator"></span>
  {/if}
</button>

<style>
  .theme-toggle {
    @apply relative flex items-center justify-center;
    @apply w-10 h-10 rounded-lg;
    @apply bg-accent hover:bg-accent/80;
    @apply text-accent-foreground;
    @apply transition-all duration-200;
    @apply border border-border;
  }
  
  .theme-toggle:hover {
    @apply shadow-md;
  }
  
  .theme-toggle:active {
    @apply scale-95;
  }
  
  .theme-indicator {
    @apply absolute -top-1 -right-1;
    @apply w-2 h-2 rounded-full;
    @apply bg-primary;
    @apply animate-pulse;
  }
  
  :global(.dark) .theme-toggle {
    @apply bg-accent hover:bg-accent/80;
    @apply text-accent-foreground;
  }
</style>