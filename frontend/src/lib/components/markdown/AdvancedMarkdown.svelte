<script lang="ts">
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  import Prism from 'prismjs';
  import 'prismjs/themes/prism-tomorrow.css';
  import 'prismjs/components/prism-javascript';
  import 'prismjs/components/prism-typescript';
  import 'prismjs/components/prism-python';
  import 'prismjs/components/prism-bash';
  import 'prismjs/components/prism-json';
  import 'prismjs/components/prism-markdown';
  import 'prismjs/components/prism-yaml';
  import 'prismjs/components/prism-css';
  import 'prismjs/components/prism-sql';

  export let content: string = '';
  export let enableMermaid: boolean = true;
  export let enableSyntaxHighlight: boolean = true;
  export let className: string = '';

  let container: HTMLElement;
  let processedContent = '';

  // Configure marked options
  marked.setOptions({
    gfm: true,
    breaks: true,
    pedantic: false,
    highlight: enableSyntaxHighlight ? (code: string, lang: string) => {
      if (lang && Prism.languages[lang]) {
        try {
          return Prism.highlight(code, Prism.languages[lang], lang);
        } catch (e) {
          console.error('Syntax highlighting error:', e);
        }
      }
      return code;
    } : undefined
  });

  // Process Mermaid diagrams
  async function processMermaidDiagrams() {
    if (!enableMermaid || !container) return;

    const mermaidBlocks = container.querySelectorAll('pre > code.language-mermaid');
    
    if (mermaidBlocks.length === 0) return;

    // Dynamically import mermaid only when needed
    const mermaid = (await import('mermaid')).default;
    
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      securityLevel: 'loose',
      fontFamily: 'monospace',
    });

    for (const block of Array.from(mermaidBlocks)) {
      const pre = block.parentElement;
      if (!pre) continue;

      const mermaidCode = block.textContent || '';
      const div = document.createElement('div');
      div.className = 'mermaid-diagram';
      
      try {
        const { svg } = await mermaid.render('mermaid-' + Math.random().toString(36).substr(2, 9), mermaidCode);
        div.innerHTML = svg;
        pre.replaceWith(div);
      } catch (error) {
        console.error('Mermaid rendering error:', error);
        div.innerHTML = `<pre class="error">Failed to render Mermaid diagram</pre>`;
        pre.replaceWith(div);
      }
    }
  }

  // Add copy button to code blocks
  function addCopyButtons() {
    if (!container) return;

    const codeBlocks = container.querySelectorAll('pre > code');
    
    codeBlocks.forEach((block) => {
      const pre = block.parentElement;
      if (!pre || pre.querySelector('.copy-button')) return;

      const button = document.createElement('button');
      button.className = 'copy-button';
      button.textContent = 'Copy';
      button.onclick = async () => {
        const text = block.textContent || '';
        try {
          await navigator.clipboard.writeText(text);
          button.textContent = 'Copied!';
          setTimeout(() => {
            button.textContent = 'Copy';
          }, 2000);
        } catch (err) {
          console.error('Failed to copy:', err);
          button.textContent = 'Failed';
          setTimeout(() => {
            button.textContent = 'Copy';
          }, 2000);
        }
      };
      
      pre.style.position = 'relative';
      pre.appendChild(button);
    });
  }

  // Process content when it changes
  $: if (content) {
    processedContent = marked.parse(content) as string;
  }

  // Apply post-processing after content is rendered
  $: if (processedContent && container) {
    // Use next tick to ensure DOM is updated
    setTimeout(() => {
      if (enableSyntaxHighlight) {
        Prism.highlightAllUnder(container);
      }
      processMermaidDiagrams();
      addCopyButtons();
    }, 0);
  }

  onMount(() => {
    return () => {
      // Cleanup if needed
    };
  });
</script>

<div 
  bind:this={container}
  class="markdown-content {className}"
>
  {@html processedContent}
</div>

<style>
  :global(.markdown-content) {
    max-width: none;
    color: #e5e7eb;
  }

  :global(.markdown-content h1) {
    @apply text-3xl font-bold mb-4 mt-6;
  }

  :global(.markdown-content h2) {
    @apply text-2xl font-semibold mb-3 mt-5;
  }

  :global(.markdown-content h3) {
    @apply text-xl font-semibold mb-2 mt-4;
  }

  :global(.markdown-content h4) {
    @apply text-lg font-medium mb-2 mt-3;
  }

  :global(.markdown-content p) {
    @apply mb-4 leading-relaxed;
  }

  :global(.markdown-content ul) {
    @apply list-disc list-inside mb-4 space-y-1;
  }

  :global(.markdown-content ol) {
    @apply list-decimal list-inside mb-4 space-y-1;
  }

  :global(.markdown-content li) {
    @apply ml-4;
  }

  :global(.markdown-content pre) {
    @apply bg-gray-900 rounded-lg p-4 overflow-x-auto mb-4 relative;
  }

  :global(.markdown-content code) {
    @apply text-sm font-mono;
  }

  :global(.markdown-content p code) {
    @apply bg-gray-800 px-2 py-1 rounded text-blue-300;
  }

  :global(.markdown-content blockquote) {
    @apply border-l-4 border-gray-600 pl-4 italic my-4 text-gray-300;
  }

  :global(.markdown-content table) {
    @apply w-full mb-4 border-collapse;
  }

  :global(.markdown-content table th) {
    @apply bg-gray-800 border border-gray-700 px-4 py-2 text-left font-semibold;
  }

  :global(.markdown-content table td) {
    @apply border border-gray-700 px-4 py-2;
  }

  :global(.markdown-content table tr:nth-child(even)) {
    @apply bg-gray-900;
  }

  :global(.markdown-content a) {
    @apply text-blue-400 hover:text-blue-300 underline;
  }

  :global(.markdown-content img) {
    @apply max-w-full h-auto rounded-lg my-4;
  }

  :global(.markdown-content hr) {
    @apply my-6 border-gray-700;
  }

  /* Copy button styles */
  :global(.markdown-content .copy-button) {
    @apply absolute top-2 right-2 px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors cursor-pointer text-white;
  }

  /* Mermaid diagram styles */
  :global(.markdown-content .mermaid-diagram) {
    @apply my-4 p-4 bg-white rounded-lg overflow-x-auto;
  }

  :global(.markdown-content .mermaid-diagram svg) {
    @apply max-w-full h-auto;
  }

  /* Error styles */
  :global(.markdown-content pre.error) {
    @apply bg-red-900 text-red-200 p-4 rounded-lg;
  }

  /* Syntax highlighting adjustments */
  :global(.markdown-content .token.comment),
  :global(.markdown-content .token.prolog),
  :global(.markdown-content .token.doctype),
  :global(.markdown-content .token.cdata) {
    @apply text-gray-500;
  }

  :global(.markdown-content .token.punctuation) {
    @apply text-gray-400;
  }

  :global(.markdown-content .token.property),
  :global(.markdown-content .token.tag),
  :global(.markdown-content .token.boolean),
  :global(.markdown-content .token.number),
  :global(.markdown-content .token.constant),
  :global(.markdown-content .token.symbol),
  :global(.markdown-content .token.deleted) {
    @apply text-pink-400;
  }

  :global(.markdown-content .token.selector),
  :global(.markdown-content .token.attr-name),
  :global(.markdown-content .token.string),
  :global(.markdown-content .token.char),
  :global(.markdown-content .token.builtin),
  :global(.markdown-content .token.inserted) {
    @apply text-green-400;
  }

  :global(.markdown-content .token.operator),
  :global(.markdown-content .token.entity),
  :global(.markdown-content .token.url),
  :global(.markdown-content .language-css .token.string),
  :global(.markdown-content .style .token.string) {
    @apply text-cyan-400;
  }

  :global(.markdown-content .token.atrule),
  :global(.markdown-content .token.attr-value),
  :global(.markdown-content .token.keyword) {
    @apply text-purple-400;
  }

  :global(.markdown-content .token.function),
  :global(.markdown-content .token.class-name) {
    @apply text-yellow-400;
  }

  :global(.markdown-content .token.regex),
  :global(.markdown-content .token.important),
  :global(.markdown-content .token.variable) {
    @apply text-orange-400;
  }
</style>