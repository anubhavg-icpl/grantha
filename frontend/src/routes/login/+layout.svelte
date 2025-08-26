<script lang="ts">
  // Login-specific layout that bypasses the main app layout
  // This prevents the header/sidebar from showing on the login page

  interface Props {
    children: any;
  }

  let { children }: Props = $props();
</script>

<svelte:head>
  <title>Login - Grantha AI Platform</title>
  <meta name="description" content="Sign in to access the Grantha AI Platform" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
</svelte:head>

<!-- Standalone login layout without app chrome -->
<div class="login-layout">
  {@render children()}
</div>

<style>
  .login-layout {
    min-height: 100vh;
    min-height: 100dvh; /* For mobile browsers */
  }
</style>