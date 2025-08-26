<script lang="ts">
  import { ChevronRight, ChevronDown, File, Folder, BookOpen } from 'lucide-svelte';
  import type { WikiPageExtended, WikiSection } from '$lib/types/shared.js';
  
  export let pages: WikiPageExtended[] = [];
  export let sections: WikiSection[] = [];
  export let selectedPageId: string | null = null;
  export let onSelectPage: (page: WikiPageExtended) => void = () => {};
  
  interface TreeNode {
    id: string;
    title: string;
    type: 'page' | 'section';
    children: TreeNode[];
    page?: WikiPageExtended;
    section?: WikiSection;
    expanded?: boolean;
  }
  
  let treeNodes: TreeNode[] = [];
  let expandedNodes = new Set<string>();
  
  // Build tree structure from pages and sections
  function buildTree(): TreeNode[] {
    const nodeMap = new Map<string, TreeNode>();
    const rootNodes: TreeNode[] = [];
    
    // Create nodes for all pages
    pages.forEach(page => {
      const node: TreeNode = {
        id: page.id,
        title: page.title,
        type: 'page',
        children: [],
        page,
        expanded: false
      };
      nodeMap.set(page.id, node);
    });
    
    // Create nodes for sections
    sections.forEach(section => {
      const node: TreeNode = {
        id: section.id,
        title: section.title,
        type: 'section',
        children: [],
        section,
        expanded: expandedNodes.has(section.id)
      };
      nodeMap.set(section.id, node);
      
      // Add pages to sections
      section.pages?.forEach((pageId: string) => {
        const pageNode = nodeMap.get(pageId);
        if (pageNode) {
          node.children.push(pageNode);
        }
      });
      
      // Add subsections
      section.subsections?.forEach((subsectionId: string) => {
        const subsectionNode = nodeMap.get(subsectionId);
        if (subsectionNode) {
          node.children.push(subsectionNode);
        }
      });
    });
    
    // Build hierarchy
    pages.forEach(page => {
      const node = nodeMap.get(page.id);
      if (!node) return;
      
      if (page.parentId) {
        const parent = nodeMap.get(page.parentId);
        if (parent && !parent.children.includes(node)) {
          parent.children.push(node);
        }
      } else if (!page.isSection) {
        rootNodes.push(node);
      }
      
      // Add children
      page.children?.forEach(childId => {
        const child = nodeMap.get(childId);
        if (child && !node.children.includes(child)) {
          node.children.push(child);
        }
      });
    });
    
    // Add root sections
    sections.forEach(section => {
      const node = nodeMap.get(section.id);
      if (node && !section.subsections?.length) {
        const hasParent = sections.some(s => 
          s.subsections?.includes(section.id)
        );
        if (!hasParent) {
          rootNodes.push(node);
        }
      }
    });
    
    // Sort nodes by importance and title
    const sortNodes = (nodes: TreeNode[]) => {
      nodes.sort((a, b) => {
        // Sections first
        if (a.type !== b.type) {
          return a.type === 'section' ? -1 : 1;
        }
        
        // By importance
        if (a.page && b.page) {
          const importanceOrder = { high: 0, medium: 1, low: 2 };
          const aImportance = importanceOrder[a.page.importance];
          const bImportance = importanceOrder[b.page.importance];
          if (aImportance !== bImportance) {
            return aImportance - bImportance;
          }
        }
        
        // By title
        return a.title.localeCompare(b.title);
      });
      
      // Recursively sort children
      nodes.forEach(node => {
        if (node.children.length > 0) {
          sortNodes(node.children);
        }
      });
    };
    
    sortNodes(rootNodes);
    return rootNodes;
  }
  
  // Toggle node expansion
  function toggleNode(nodeId: string) {
    if (expandedNodes.has(nodeId)) {
      expandedNodes.delete(nodeId);
    } else {
      expandedNodes.add(nodeId);
    }
    expandedNodes = expandedNodes; // Trigger reactivity
    treeNodes = buildTree();
  }
  
  // Handle node selection
  function selectNode(node: TreeNode) {
    if (node.type === 'page' && node.page) {
      selectedPageId = node.id;
      onSelectPage(node.page);
    } else if (node.type === 'section') {
      toggleNode(node.id);
    }
  }
  
  // Get icon for node
  function getNodeIcon(node: TreeNode) {
    if (node.type === 'section') {
      return Folder;
    }
    if (node.page?.isSection) {
      return BookOpen;
    }
    return File;
  }
  
  // Get importance class
  function getImportanceClass(importance?: string): string {
    switch (importance) {
      case 'high':
        return 'text-red-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-green-500';
      default:
        return '';
    }
  }
  
  // Rebuild tree when data changes
  $: if (pages || sections) {
    treeNodes = buildTree();
  }
</script>

<div class="wiki-tree-view">
  <div class="tree-header">
    <h3 class="text-lg font-semibold mb-2">Documentation Structure</h3>
  </div>
  
  <div class="tree-content">
    {#if treeNodes.length === 0}
      <div class="empty-state text-gray-500 text-center py-8">
        <BookOpen class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No documentation available</p>
      </div>
    {:else}
      <ul class="tree-list">
        {#each treeNodes as node}
          <TreeNode 
            {node} 
            {selectedPageId}
            depth={0}
            on:select={() => selectNode(node)}
            on:toggle={() => toggleNode(node.id)}
          />
        {/each}
      </ul>
    {/if}
  </div>
</div>

<!-- Recursive Tree Node Component -->
<script lang="ts" context="module">
  import TreeNode from './TreeNode.svelte';
</script>

<style>
  .wiki-tree-view {
    @apply h-full overflow-y-auto bg-gray-900 rounded-lg p-4;
  }
  
  .tree-header {
    @apply border-b border-gray-700 pb-2 mb-4;
  }
  
  .tree-content {
    @apply overflow-x-hidden;
  }
  
  .tree-list {
    @apply space-y-1;
  }
  
  :global(.tree-node) {
    @apply select-none;
  }
  
  :global(.tree-node-content) {
    @apply flex items-center gap-2 px-2 py-1 rounded cursor-pointer hover:bg-gray-800 transition-colors;
  }
  
  :global(.tree-node-content.selected) {
    @apply bg-blue-900 bg-opacity-50;
  }
  
  :global(.tree-node-icon) {
    @apply w-4 h-4 flex-shrink-0;
  }
  
  :global(.tree-node-chevron) {
    @apply w-3 h-3 transition-transform;
  }
  
  :global(.tree-node-chevron.expanded) {
    @apply rotate-90;
  }
  
  :global(.tree-node-title) {
    @apply flex-1 text-sm truncate;
  }
  
  :global(.tree-node-children) {
    @apply ml-4 mt-1 space-y-1;
  }
</style>