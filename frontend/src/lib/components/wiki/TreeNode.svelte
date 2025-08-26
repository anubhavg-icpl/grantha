<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { ChevronRight, ChevronDown, File, Folder, BookOpen } from 'lucide-svelte';
  
  export let node: any;
  export let selectedPageId: string | null = null;
  export let depth: number = 0;
  
  const dispatch = createEventDispatcher();
  
  function getNodeIcon() {
    if (node.type === 'section') {
      return Folder;
    }
    if (node.page?.isSection) {
      return BookOpen;
    }
    return File;
  }
  
  function getImportanceClass(): string {
    if (node.type !== 'page' || !node.page) return '';
    switch (node.page.importance) {
      case 'high':
        return 'text-red-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return '';
    }
  }
  
  function handleClick() {
    if (node.children?.length > 0) {
      dispatch('toggle');
    }
    dispatch('select');
  }
  
  const Icon = getNodeIcon();
  const hasChildren = node.children?.length > 0;
  const isSelected = selectedPageId === node.id;
</script>

<li class="tree-node" style="margin-left: {depth * 1}rem">
  <div 
    class="tree-node-content {isSelected ? 'selected' : ''}"
    on:click={handleClick}
    on:keydown={(e) => e.key === 'Enter' && handleClick()}
    role="button"
    tabindex="0"
  >
    {#if hasChildren}
      <span class="tree-node-chevron {node.expanded ? 'expanded' : ''}">
        {#if node.expanded}
          <ChevronDown class="w-3 h-3" />
        {:else}
          <ChevronRight class="w-3 h-3" />
        {/if}
      </span>
    {:else}
      <span class="w-3"></span>
    {/if}
    
    <Icon class="tree-node-icon {getImportanceClass()}" />
    
    <span class="tree-node-title">
      {node.title}
    </span>
  </div>
  
  {#if hasChildren && node.expanded}
    <ul class="tree-node-children">
      {#each node.children as childNode}
        <svelte:self
          node={childNode}
          {selectedPageId}
          depth={depth + 1}
          on:select
          on:toggle
        />
      {/each}
    </ul>
  {/if}
</li>