<script lang="ts">
	import ProcessedProjects from '$lib/components/projects/ProcessedProjects.svelte';
</script>

<svelte:head>
	<title>Projects - Grantha</title>
</svelte:head>

<div class="container mx-auto px-4 py-8">
	<ProcessedProjects showHeader={true} />
</div>