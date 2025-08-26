<script lang="ts">
  import { onMount } from 'svelte';
  import { Bot, Plus, Settings, Play, Pause, Trash2, Edit2, Save, X, Code, FileText, Search, Shield, Zap, Brain, CheckCircle, XCircle, AlertCircle, BookOpen, Terminal, Database, Globe, GitBranch } from 'lucide-svelte';
  import { apiClient } from '$lib/api/client.js';

  interface AgentCapability {
    id: string;
    name: string;
    description: string;
    icon: any;
  }

  interface Agent {
    id: string;
    name: string;
    description: string;
    type: 'wiki' | 'docs' | 'research' | 'code' | 'fullstack' | 'security' | 'custom';
    capabilities: string[];
    status: 'idle' | 'running' | 'completed' | 'error';
    createdAt: number;
    lastRun?: number;
    config: {
      provider?: string;
      model?: string;
      temperature?: number;
      repoUrl?: string;
      language?: string;
      outputFormat?: string;
      autoRun?: boolean;
    };
    tasks: string[];
    output?: any;
    error?: string;
  }

  interface Task {
    id: string;
    agentId: string;
    title: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    startedAt?: number;
    completedAt?: number;
    result?: any;
    error?: string;
  }

  // Available capabilities
  const capabilities: AgentCapability[] = [
    { id: 'wiki-gen', name: 'Wiki Generation', description: 'Generate comprehensive wiki documentation', icon: BookOpen },
    { id: 'api-docs', name: 'API Documentation', description: 'Create API documentation', icon: FileText },
    { id: 'code-analysis', name: 'Code Analysis', description: 'Analyze and understand codebases', icon: Code },
    { id: 'research', name: 'Deep Research', description: 'Conduct thorough research', icon: Search },
    { id: 'security-audit', name: 'Security Audit', description: 'Security vulnerability checks', icon: Shield },
    { id: 'fullstack-dev', name: 'Full-Stack Dev', description: 'End-to-end development', icon: Terminal },
    { id: 'database-design', name: 'Database Design', description: 'Design database schemas', icon: Database },
    { id: 'deployment', name: 'Deployment', description: 'Deploy and configure apps', icon: Globe },
    { id: 'version-control', name: 'Version Control', description: 'Git operations', icon: GitBranch }
  ];

  // Pre-configured agent templates
  const agentTemplates = [
    {
      name: 'Wiki Master',
      description: 'Generates comprehensive wiki documentation for any repository',
      type: 'wiki',
      capabilities: ['wiki-gen', 'api-docs', 'code-analysis'],
      icon: BookOpen,
      config: {
        outputFormat: 'markdown',
        temperature: 0.7
      }
    },
    {
      name: 'Documentation Pro',
      description: 'Creates beautiful, searchable documentation with examples',
      type: 'docs',
      capabilities: ['api-docs', 'code-analysis'],
      icon: FileText,
      config: {
        outputFormat: 'html',
        temperature: 0.5
      }
    },
    {
      name: 'Research Assistant',
      description: 'Deep research on any technical topic with sources',
      type: 'research',
      capabilities: ['research', 'code-analysis'],
      icon: Search,
      config: {
        temperature: 0.8
      }
    },
    {
      name: 'Full-Stack Developer',
      description: 'Complete feature implementation from backend to frontend',
      type: 'fullstack',
      capabilities: ['fullstack-dev', 'database-design', 'api-docs'],
      icon: Terminal,
      config: {
        temperature: 0.6
      }
    },
    {
      name: 'Security Guardian',
      description: 'Comprehensive security audits and vulnerability fixes',
      type: 'security',
      capabilities: ['security-audit', 'code-analysis'],
      icon: Shield,
      config: {
        temperature: 0.3
      }
    }
  ];

  // State
  let agents: Agent[] = $state([]);
  let tasks: Task[] = $state([]);
  let showCreateModal = $state(false);
  let editingAgent: Agent | null = $state(null);
  let selectedAgent: Agent | null = $state(null);
  let selectedTemplate: typeof agentTemplates[0] | null = $state(null);
  
  // New agent form
  let newAgent = $state({
    name: '',
    description: '',
    type: 'wiki' as Agent['type'],
    capabilities: [] as string[],
    config: {
      provider: 'openai',
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      repoUrl: '',
      language: 'en',
      outputFormat: 'markdown',
      autoRun: false
    }
  });

  // Task execution form
  let taskInput = $state({
    title: '',
    description: '',
    repoUrl: '',
    query: ''
  });

  // Load agents from localStorage
  function loadAgents() {
    const saved = localStorage.getItem('grantha_agents');
    if (saved) {
      try {
        agents = JSON.parse(saved);
      } catch (e) {
        agents = [];
      }
    }
  }

  // Save agents to localStorage
  function saveAgents() {
    localStorage.setItem('grantha_agents', JSON.stringify(agents));
  }

  // Load tasks
  function loadTasks() {
    const saved = localStorage.getItem('grantha_agent_tasks');
    if (saved) {
      try {
        tasks = JSON.parse(saved);
      } catch (e) {
        tasks = [];
      }
    }
  }

  // Save tasks
  function saveTasks() {
    localStorage.setItem('grantha_agent_tasks', JSON.stringify(tasks));
  }

  // Use template
  function useTemplate(template: typeof agentTemplates[0]) {
    selectedTemplate = template;
    newAgent = {
      name: template.name,
      description: template.description,
      type: template.type as Agent['type'],
      capabilities: template.capabilities,
      config: {
        ...newAgent.config,
        ...template.config
      }
    };
    showCreateModal = true;
  }

  // Create new agent
  function createAgent() {
    if (!newAgent.name || !newAgent.description) {
      alert('Please provide agent name and description');
      return;
    }

    const agent: Agent = {
      id: `agent_${Date.now()}`,
      name: newAgent.name,
      description: newAgent.description,
      type: newAgent.type,
      capabilities: newAgent.capabilities,
      status: 'idle',
      createdAt: Date.now(),
      config: { ...newAgent.config },
      tasks: []
    };

    agents = [...agents, agent];
    saveAgents();
    
    // Reset form
    newAgent = {
      name: '',
      description: '',
      type: 'wiki',
      capabilities: [],
      config: {
        provider: 'openai',
        model: 'gpt-3.5-turbo',
        temperature: 0.7,
        repoUrl: '',
        language: 'en',
        outputFormat: 'markdown',
        autoRun: false
      }
    };
    
    selectedTemplate = null;
    showCreateModal = false;
    
    // Auto-select the new agent
    selectedAgent = agent;
  }

  // Update agent
  function updateAgent() {
    if (!editingAgent) return;
    
    const index = agents.findIndex(a => a.id === editingAgent.id);
    if (index !== -1) {
      agents[index] = { ...editingAgent };
      agents = agents;
      saveAgents();
    }
    
    editingAgent = null;
  }

  // Delete agent
  function deleteAgent(agentId: string) {
    if (!confirm('Delete this agent and all its tasks?')) return;
    
    agents = agents.filter(a => a.id !== agentId);
    tasks = tasks.filter(t => t.agentId !== agentId);
    saveAgents();
    saveTasks();
    
    if (selectedAgent?.id === agentId) {
      selectedAgent = null;
    }
  }

  // Run agent
  async function runAgent(agent: Agent) {
    if (agent.status === 'running') return;
    
    // Update agent status
    agent.status = 'running';
    agent.lastRun = Date.now();
    agents = agents;
    saveAgents();

    // Create task
    const task: Task = {
      id: `task_${Date.now()}`,
      agentId: agent.id,
      title: taskInput.title || `${agent.name} - ${new Date().toLocaleString()}`,
      status: 'running',
      progress: 0,
      startedAt: Date.now()
    };
    
    agent.tasks = [...agent.tasks, task.id];
    tasks = [...tasks, task];
    saveTasks();

    try {
      // Simulate progress
      for (let i = 0; i <= 100; i += 20) {
        task.progress = i;
        tasks = tasks;
        await new Promise(resolve => setTimeout(resolve, 300));
      }

      // Execute based on agent type
      let result: any;
      const repoUrl = taskInput.repoUrl || agent.config.repoUrl || 'https://github.com/anubhavg-icpl/grantha';
      
      if (agent.type === 'wiki' || agent.type === 'docs') {
        // Generate wiki/docs
        result = await apiClient.generateWiki({
          repo_url: repoUrl,
          language: agent.config.language || 'en',
          provider: agent.config.provider,
          model: agent.config.model
        });
      } else if (agent.type === 'research') {
        // Deep research
        result = await apiClient.deepResearch({
          query: taskInput.query || taskInput.description || 'Research topic',
          type: 'comprehensive'
        });
      } else {
        // Simulate other types
        result = {
          success: true,
          type: agent.type,
          data: `${agent.name} completed the task: ${taskInput.title || 'Automated task'}`,
          capabilities: agent.capabilities,
          timestamp: Date.now(),
          output: generateMockOutput(agent.type)
        };
      }

      // Update task and agent
      task.status = 'completed';
      task.completedAt = Date.now();
      task.result = result;
      agent.status = 'completed';
      agent.output = result;
      
    } catch (error) {
      task.status = 'failed';
      task.error = error instanceof Error ? error.message : 'Unknown error';
      agent.status = 'error';
      agent.error = task.error;
    }

    tasks = tasks;
    agents = agents;
    saveTasks();
    saveAgents();
  }

  // Generate mock output for demo
  function generateMockOutput(type: string) {
    switch(type) {
      case 'code':
        return `// Generated code analysis
function optimizedFunction() {
  // Improved performance by 40%
  return processData();
}`;
      case 'fullstack':
        return {
          backend: 'API endpoints created',
          frontend: 'UI components built',
          database: 'Schema optimized'
        };
      case 'security':
        return {
          vulnerabilities: 0,
          fixes: 3,
          recommendations: ['Enable 2FA', 'Update dependencies']
        };
      default:
        return 'Task completed successfully';
    }
  }

  // Stop agent
  function stopAgent(agent: Agent) {
    if (agent.status !== 'running') return;
    
    agent.status = 'idle';
    agents = agents;
    saveAgents();
    
    // Mark running tasks as failed
    const agentTasks = tasks.filter(t => t.agentId === agent.id && t.status === 'running');
    agentTasks.forEach(task => {
      task.status = 'failed';
      task.error = 'Stopped by user';
    });
    tasks = tasks;
    saveTasks();
  }

  // Toggle capability
  function toggleCapability(capId: string) {
    const index = newAgent.capabilities.indexOf(capId);
    if (index === -1) {
      newAgent.capabilities = [...newAgent.capabilities, capId];
    } else {
      newAgent.capabilities = newAgent.capabilities.filter(c => c !== capId);
    }
  }

  // Get agent type icon
  function getAgentIcon(type: Agent['type']) {
    switch (type) {
      case 'wiki': return BookOpen;
      case 'docs': return FileText;
      case 'research': return Search;
      case 'code': return Code;
      case 'fullstack': return Terminal;
      case 'security': return Shield;
      default: return Bot;
    }
  }

  // Get status color
  function getStatusColor(status: Agent['status']) {
    switch (status) {
      case 'running': return 'text-blue-500';
      case 'completed': return 'text-green-500';
      case 'error': return 'text-red-500';
      default: return 'text-muted-foreground';
    }
  }

  // Get status icon
  function getStatusIcon(status: Agent['status']) {
    switch (status) {
      case 'running': return Play;
      case 'completed': return CheckCircle;
      case 'error': return XCircle;
      default: return AlertCircle;
    }
  }

  // Clear task input
  function clearTaskInput() {
    taskInput = {
      title: '',
      description: '',
      repoUrl: '',
      query: ''
    };
  }

  onMount(() => {
    loadAgents();
    loadTasks();
  });
</script>

<svelte:head>
  <title>AI Agents - Grantha</title>
</svelte:head>

<div class="min-h-screen bg-background">
  <!-- Header -->
  <div class="border-b border-border bg-card">
    <div class="container mx-auto px-4 py-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold">AI Agent Hub</h1>
          <p class="text-muted-foreground mt-1">Create autonomous agents for wiki generation, documentation, and more</p>
        </div>
        <div class="flex items-center gap-4">
          <button
            onclick={() => { selectedTemplate = null; showCreateModal = true; }}
            class="flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            <Plus class="w-5 h-5" />
            Create Agent
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Templates Section -->
  {#if agents.length === 0}
    <div class="container mx-auto px-4 py-8">
      <h2 class="text-xl font-semibold mb-6">Quick Start Templates</h2>
      <div class="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {#each agentTemplates as template}
          <button
            onclick={() => useTemplate(template)}
            class="group bg-card border border-border rounded-xl p-6 hover:shadow-lg hover:border-primary transition-all text-left"
          >
            <div class="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
              {@const IconComponent = template.icon}
              <IconComponent class="w-7 h-7 text-primary" />
            </div>
            <h3 class="font-semibold mb-2">{template.name}</h3>
            <p class="text-sm text-muted-foreground line-clamp-2">{template.description}</p>
          </button>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Main Content -->
  <div class="container mx-auto px-4 py-8">
    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Agents Grid -->
      <div class="lg:col-span-2">
        {#if agents.length > 0}
          <h2 class="text-xl font-semibold mb-6">Your Agents</h2>
          <div class="grid gap-4">
            {#each agents as agent}
              <div class="bg-card border border-border rounded-lg p-6 hover:shadow-lg transition-all {selectedAgent?.id === agent.id ? 'ring-2 ring-primary' : ''}">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex items-start gap-3">
                    <div class="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                      {@const IconComponent = getAgentIcon(agent.type)}
                      <IconComponent class="w-6 h-6 text-primary" />
                    </div>
                    <div class="flex-1">
                      <h3 class="font-semibold text-lg">{agent.name}</h3>
                      <p class="text-sm text-muted-foreground">{agent.description}</p>
                      <div class="flex items-center gap-3 mt-2">
                        <div class="flex items-center gap-1">
                          {@const StatusIcon = getStatusIcon(agent.status)}
                          <StatusIcon class="w-4 h-4 {getStatusColor(agent.status)}" />
                          <span class="text-xs {getStatusColor(agent.status)} capitalize">{agent.status}</span>
                        </div>
                        {#if agent.lastRun}
                          <span class="text-xs text-muted-foreground">
                            Last: {new Date(agent.lastRun).toLocaleString()}
                          </span>
                        {/if}
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex items-center gap-1">
                    {#if agent.status === 'running'}
                      <button
                        onclick={() => stopAgent(agent)}
                        class="p-2 hover:bg-accent rounded-lg transition-colors"
                        title="Stop"
                      >
                        <Pause class="w-4 h-4" />
                      </button>
                    {:else}
                      <button
                        onclick={() => { selectedAgent = agent; clearTaskInput(); }}
                        class="p-2 hover:bg-accent rounded-lg transition-colors"
                        title="Configure & Run"
                      >
                        <Play class="w-4 h-4" />
                      </button>
                    {/if}
                    <button
                      onclick={() => editingAgent = { ...agent }}
                      class="p-2 hover:bg-accent rounded-lg transition-colors"
                      title="Edit"
                    >
                      <Settings class="w-4 h-4" />
                    </button>
                    <button
                      onclick={() => deleteAgent(agent.id)}
                      class="p-2 hover:bg-accent rounded-lg transition-colors text-destructive"
                      title="Delete"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <!-- Capabilities -->
                <div class="flex flex-wrap gap-2">
                  {#each agent.capabilities.slice(0, 4) as capId}
                    {#each capabilities.filter(c => c.id === capId) as capability}
                      <span class="flex items-center gap-1 px-2 py-1 text-xs bg-secondary/50 text-secondary-foreground rounded-full">
                        {@const CapIcon = capability.icon}
                        <CapIcon class="w-3 h-3" />
                        {capability.name}
                      </span>
                    {/each}
                  {/each}
                  {#if agent.capabilities.length > 4}
                    <span class="px-2 py-1 text-xs bg-muted text-muted-foreground rounded-full">
                      +{agent.capabilities.length - 4} more
                    </span>
                  {/if}
                </div>
                
                <!-- Running progress -->
                {#if agent.status === 'running'}
                  {#each tasks.filter(t => t.agentId === agent.id && t.status === 'running') as runningTask}
                    <div class="mt-4">
                      <div class="flex justify-between text-xs text-muted-foreground mb-1">
                        <span>{runningTask.title}</span>
                        <span>{runningTask.progress}%</span>
                      </div>
                      <div class="w-full bg-secondary/30 rounded-full h-2">
                        <div 
                          class="bg-primary h-2 rounded-full transition-all duration-300"
                          style="width: {runningTask.progress}%"
                        ></div>
                      </div>
                    </div>
                  {/each}
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <div class="bg-card border border-border rounded-lg p-12 text-center">
            <Bot class="w-20 h-20 mx-auto mb-4 text-muted-foreground/30" />
            <h3 class="text-xl font-semibold mb-2">No agents yet</h3>
            <p class="text-muted-foreground mb-6">Create your first AI agent or use a template to get started</p>
            <button
              onclick={() => showCreateModal = true}
              class="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
            >
              Create Your First Agent
            </button>
          </div>
        {/if}
      </div>

      <!-- Task Panel -->
      <div>
        <h2 class="text-xl font-semibold mb-6">Run Task</h2>
        
        {#if selectedAgent}
          <div class="bg-card border border-border rounded-lg p-6">
            <div class="mb-6">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  {@const AgentIcon = getAgentIcon(selectedAgent.type)}
                  <AgentIcon class="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 class="font-semibold">{selectedAgent.name}</h3>
                  <p class="text-xs text-muted-foreground">{selectedAgent.type} agent</p>
                </div>
              </div>
            </div>
            
            <div class="space-y-4">
              <div>
                <label class="text-sm font-medium mb-2 block">Task Name</label>
                <input
                  type="text"
                  bind:value={taskInput.title}
                  placeholder="e.g., Generate project documentation"
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              
              {#if selectedAgent.type === 'wiki' || selectedAgent.type === 'docs' || selectedAgent.type === 'code' || selectedAgent.type === 'fullstack'}
                <div>
                  <label class="text-sm font-medium mb-2 block">Repository URL</label>
                  <input
                    type="text"
                    bind:value={taskInput.repoUrl}
                    placeholder="https://github.com/user/repo"
                    class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              {/if}
              
              {#if selectedAgent.type === 'research'}
                <div>
                  <label for="research-query-textarea" class="text-sm font-medium mb-2 block">Research Query</label>
                  <textarea
                    id="research-query-textarea"
                    bind:value={taskInput.query}
                    placeholder="What would you like to research?"
                    class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                    rows="3"
                  ></textarea>
                </div>
              {/if}
              
              <div>
                <label for="task-instructions-textarea" class="text-sm font-medium mb-2 block">Instructions (Optional)</label>
                <textarea
                  id="task-instructions-textarea"
                  bind:value={taskInput.description}
                  placeholder="Additional instructions for the agent..."
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows="3"
                ></textarea>
              </div>
              
              <button
                onclick={() => runAgent(selectedAgent)}
                disabled={selectedAgent.status === 'running'}
                class="w-full px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {selectedAgent.status === 'running' ? 'Running...' : 'Run Task'}
              </button>
            </div>
          </div>
        {:else}
          <div class="bg-card border border-border rounded-lg p-8 text-center">
            <Play class="w-12 h-12 mx-auto mb-3 text-muted-foreground/30" />
            <p class="text-sm text-muted-foreground">Select an agent to run tasks</p>
          </div>
        {/if}

        <!-- Recent Tasks -->
        <div class="mt-8">
          <h3 class="text-lg font-semibold mb-4">Task History</h3>
          
          {#if tasks.length === 0}
            <p class="text-sm text-muted-foreground">No tasks yet</p>
          {:else}
            <div class="space-y-2 max-h-96 overflow-y-auto">
              {#each tasks.slice(-10).reverse() as task}
                <div class="bg-card border border-border rounded-lg p-3">
                  <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium truncate">{task.title}</p>
                      <p class="text-xs text-muted-foreground">
                        {new Date(task.startedAt || 0).toLocaleString()}
                      </p>
                    </div>
                    <div class="flex items-center gap-1">
                      {#if task.status === 'completed'}
                        <CheckCircle class="w-4 h-4 text-green-500" />
                      {:else if task.status === 'failed'}
                        <XCircle class="w-4 h-4 text-red-500" />
                      {:else if task.status === 'running'}
                        <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      {:else}
                        <AlertCircle class="w-4 h-4 text-yellow-500" />
                      {/if}
                    </div>
                  </div>
                  {#if task.error}
                    <p class="text-xs text-red-500 mt-1">{task.error}</p>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Create/Edit Agent Modal -->
  {#if showCreateModal || editingAgent}
    {#if editingAgent}
      <!-- Edit Mode -->
      <div 
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" 
        onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
        onkeydown={(e) => { if (e.key === 'Escape') { showCreateModal = false; editingAgent = null; selectedTemplate = null; } }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-modal-title"
      >
        <div 
          class="bg-card rounded-xl shadow-2xl border border-border p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto" 
          onclick={(e) => e.stopPropagation()}
          role="document"
        >
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 id="edit-modal-title" class="text-xl font-semibold">Edit Agent</h2>
              <p class="text-sm text-muted-foreground mt-1">Configure your AI agent's capabilities and settings</p>
            </div>
            <button
              onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
              class="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Basic Info -->
            <div class="space-y-4">
              <div>
                <label for="edit-agent-name" class="text-sm font-medium mb-2 block">Agent Name</label>
                <input
                  id="edit-agent-name"
                  type="text"
                  bind:value={editingAgent.name}
                  placeholder="e.g., Documentation Generator"
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              
              <div>
                <label for="edit-agent-description" class="text-sm font-medium mb-2 block">Description</label>
                <textarea
                  id="edit-agent-description"
                  bind:value={editingAgent.description}
                  placeholder="What does this agent do?"
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows="3"
                ></textarea>
              </div>
              
              <div>
                <label for="edit-agent-type" class="text-sm font-medium mb-2 block">Agent Type</label>
                <select
                  id="edit-agent-type"
                  bind:value={editingAgent.type}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="wiki">Wiki Generator</option>
                  <option value="docs">Documentation</option>
                  <option value="research">Research</option>
                  <option value="code">Code Analysis</option>
                  <option value="fullstack">Full-Stack Dev</option>
                  <option value="security">Security</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>
            
            <!-- Configuration -->
            <div class="space-y-4">
              <div>
                <label for="edit-agent-provider" class="text-sm font-medium mb-2 block">AI Provider</label>
                <select
                  id="edit-agent-provider"
                  bind:value={editingAgent.config.provider}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="openai">OpenAI</option>
                  <option value="google">Google</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="groq">Groq</option>
                  <option value="deepseek">DeepSeek</option>
                </select>
              </div>
              
              <div>
                <label for="edit-agent-model" class="text-sm font-medium mb-2 block">Model</label>
                <select
                  id="edit-agent-model"
                  bind:value={editingAgent.config.model}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                  <option value="gemini-pro">Gemini Pro</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="deepseek-coder">DeepSeek Coder</option>
                </select>
              </div>
              
              <div>
                <label for="edit-agent-temperature" class="text-sm font-medium mb-2 flex justify-between">
                  <span>Temperature</span>
                  <span class="text-primary font-mono">{editingAgent.config.temperature?.toFixed(1)}</span>
                </label>
                <input
                  id="edit-agent-temperature"
                  type="range"
                  bind:value={editingAgent.config.temperature}
                  min="0"
                  max="2"
                  step="0.1"
                  class="w-full accent-primary"
                />
                <div class="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>
              
              <div>
                <label for="edit-agent-output-format" class="text-sm font-medium mb-2 block">Output Format</label>
                <select
                  id="edit-agent-output-format"
                  bind:value={editingAgent.config.outputFormat}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="markdown">Markdown</option>
                  <option value="json">JSON</option>
                  <option value="html">HTML</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Capabilities -->
          <div class="mt-6">
            <label class="text-sm font-medium mb-3 block">Capabilities</label>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
              {#each capabilities as capability}
                <button
                  onclick={() => {
                    const index = editingAgent.capabilities.indexOf(capability.id);
                    if (index === -1) {
                      editingAgent.capabilities = [...editingAgent.capabilities, capability.id];
                    } else {
                      editingAgent.capabilities = editingAgent.capabilities.filter(c => c !== capability.id);
                    }
                  }}
                  class="flex items-center gap-2 p-3 border rounded-lg transition-all {editingAgent.capabilities.includes(capability.id) 
                    ? 'bg-primary/10 border-primary text-primary' 
                    : 'border-border hover:bg-accent'}"
                >
                  <svelte:component this={capability.icon} class="w-4 h-4" />
                  <div class="text-left flex-1">
                    <div class="text-sm font-medium">{capability.name}</div>
                  </div>
                </button>
              {/each}
            </div>
          </div>
          
          <div class="mt-6 flex justify-end gap-2">
            <button
              onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
              class="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              onclick={updateAgent}
              class="px-6 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
            >
              Update Agent
            </button>
          </div>
        </div>
      </div>
    {:else}
      <!-- Create Mode -->
      <div 
        class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" 
        onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
        onkeydown={(e) => { if (e.key === 'Escape') { showCreateModal = false; editingAgent = null; selectedTemplate = null; } }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-modal-title"
      >
        <div 
          class="bg-card rounded-xl shadow-2xl border border-border p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto" 
          onclick={(e) => e.stopPropagation()}
          role="document"
        >
          <div class="flex items-center justify-between mb-6">
            <div>
              <h2 id="create-modal-title" class="text-xl font-semibold">{selectedTemplate ? `Create from Template: ${selectedTemplate.name}` : 'Create Custom Agent'}</h2>
              <p class="text-sm text-muted-foreground mt-1">Configure your AI agent's capabilities and settings</p>
            </div>
            <button
              onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
              class="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
          
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Basic Info -->
            <div class="space-y-4">
              <div>
                <label for="new-agent-name" class="text-sm font-medium mb-2 block">Agent Name</label>
                <input
                  id="new-agent-name"
                  type="text"
                  bind:value={newAgent.name}
                  placeholder="e.g., Documentation Generator"
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              
              <div>
                <label for="new-agent-description" class="text-sm font-medium mb-2 block">Description</label>
                <textarea
                  id="new-agent-description"
                  bind:value={newAgent.description}
                  placeholder="What does this agent do?"
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows="3"
                ></textarea>
              </div>
              
              <div>
                <label for="new-agent-type" class="text-sm font-medium mb-2 block">Agent Type</label>
                <select
                  id="new-agent-type"
                  bind:value={newAgent.type}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="wiki">Wiki Generator</option>
                  <option value="docs">Documentation</option>
                  <option value="research">Research</option>
                  <option value="code">Code Analysis</option>
                  <option value="fullstack">Full-Stack Dev</option>
                  <option value="security">Security</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>
            
            <!-- Configuration -->
            <div class="space-y-4">
              <div>
                <label for="new-agent-provider" class="text-sm font-medium mb-2 block">AI Provider</label>
                <select
                  id="new-agent-provider"
                  bind:value={newAgent.config.provider}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="openai">OpenAI</option>
                  <option value="google">Google</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="groq">Groq</option>
                  <option value="deepseek">DeepSeek</option>
                </select>
              </div>
              
              <div>
                <label for="new-agent-model" class="text-sm font-medium mb-2 block">Model</label>
                <select
                  id="new-agent-model"
                  bind:value={newAgent.config.model}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4">GPT-4</option>
                  <option value="gemini-pro">Gemini Pro</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="deepseek-coder">DeepSeek Coder</option>
                </select>
              </div>
              
              <div>
                <label for="new-agent-temperature" class="text-sm font-medium mb-2 flex justify-between">
                  <span>Temperature</span>
                  <span class="text-primary font-mono">{newAgent.config.temperature?.toFixed(1)}</span>
                </label>
                <input
                  id="new-agent-temperature"
                  type="range"
                  bind:value={newAgent.config.temperature}
                  min="0"
                  max="2"
                  step="0.1"
                  class="w-full accent-primary"
                />
                <div class="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>
              
              <div>
                <label for="new-agent-output-format" class="text-sm font-medium mb-2 block">Output Format</label>
                <select
                  id="new-agent-output-format"
                  bind:value={newAgent.config.outputFormat}
                  class="w-full px-3 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="markdown">Markdown</option>
                  <option value="json">JSON</option>
                  <option value="html">HTML</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Capabilities -->
          <div class="mt-6">
            <label class="text-sm font-medium mb-3 block">Capabilities</label>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
              {#each capabilities as capability}
                <button
                  onclick={() => toggleCapability(capability.id)}
                  class="flex items-center gap-2 p-3 border rounded-lg transition-all {newAgent.capabilities.includes(capability.id) 
                    ? 'bg-primary/10 border-primary text-primary' 
                    : 'border-border hover:bg-accent'}"
                >
                  <svelte:component this={capability.icon} class="w-4 h-4" />
                  <div class="text-left flex-1">
                    <div class="text-sm font-medium">{capability.name}</div>
                  </div>
                </button>
              {/each}
            </div>
          </div>
          
          <div class="mt-6 flex justify-end gap-2">
            <button
              onclick={() => { showCreateModal = false; editingAgent = null; selectedTemplate = null; }}
              class="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              onclick={createAgent}
              class="px-6 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
            >
              Create Agent
            </button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>