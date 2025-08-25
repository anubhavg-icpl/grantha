# Grantha Subagents Collection

A comprehensive set of specialized AI subagents for the Grantha project, designed to handle specific development, infrastructure, and operational tasks.

## 📚 Available Subagents

Each subagent is optimized with specific Claude models for cost-effective performance:

### Core Development
- **fullstack-developer** (Sonnet 4) - End-to-end feature development
- **api-designer** (Sonnet 4) - REST and GraphQL API architecture
- **websocket-engineer** (Sonnet 4) - Real-time communication specialist

### Language & Framework Specialists
- **typescript-pro** (Sonnet 4) - TypeScript type safety expert
- **nodejs-expert** (Sonnet 4) - Node.js and Express.js specialist

### Infrastructure & DevOps
- **docker-engineer** (Haiku 3.5) - Container orchestration
- **devops-engineer** (Sonnet 4) - CI/CD and automation
- **database-administrator** (Sonnet 4) - MongoDB and Redis management

### Quality & Security
- **code-reviewer** (Sonnet 4) - Code quality guardian
- **security-auditor** (Opus 4.1) - Vulnerability assessment
- **test-automator** (Haiku 3.5) - Test framework specialist

### AI & Data
- **ai-engineer** (Opus 4.1) - LLM integration and ML pipelines
- **llm-architect** (Opus 4.1) - Large language model systems
- **prompt-engineer** (Opus 4.1) - Prompt optimization

### Documentation & Communication
- **documentation-engineer** (Haiku 3.5) - Technical documentation
- **api-documenter** (Haiku 3.5) - OpenAPI specifications
- **technical-writer** (Haiku 3.5) - User guides and tutorials
- **product-manager** (Sonnet 4) - Product strategy and roadmap

### Code Optimization
- **refactoring-specialist** (Sonnet 4) - Code improvement expert

### Meta & Orchestration
- **agent-organizer** (Opus 4.1) - Multi-agent coordinator
- **workflow-orchestrator** (Opus 4.1) - Complex workflow automation
- **research-analyst** (Sonnet 4) - Market and technology research

## 💰 Model Optimization Strategy

Subagents are configured with cost-optimized model selection:

| Model | Cost (Input/Output per MTok) | Used For |
|-------|------------------------------|----------|
| **Haiku 3.5** | $0.80 / $4 | Simple, structured tasks (docs, tests, Docker) |
| **Sonnet 4** | $3 / $15 | Medium complexity (development, refactoring) |
| **Opus 4.1** | $15 / $75 | Complex tasks (security, AI/ML, orchestration) |

This strategy can reduce costs by up to 90% for routine tasks while ensuring critical operations use the most capable models.

## 🚀 Usage

Subagents are automatically loaded by Claude Code. You can invoke them in two ways:

### Automatic Invocation
Claude will automatically select appropriate subagents based on the task.

### Manual Invocation
```
Ask the [subagent-name] to [specific task]
```

Example:
```
Ask the api-designer to create a new endpoint for user authentication
```

## 🔧 Creating Custom Subagents

To create a new subagent:

1. Create a new `.md` file in `.claude/agents/`
2. Use this template:

```markdown
---
name: your-subagent-name
description: Brief description of capabilities
tools: List of tools (Read, Write, Edit, Bash, etc.)
---

You are a [role] specializing in [expertise] for the Grantha project.

## Core Expertise
- List key skills

## MCP Tool Integration
- Describe tool usage

## Implementation Workflow
1. Step-by-step process

## Best Practices
- Key guidelines
```

## 📊 Subagent Categories

| Category | Count | Primary Focus |
|----------|-------|--------------|
| Development | 3 | Core feature implementation |
| Infrastructure | 3 | DevOps and deployment |
| Quality | 3 | Testing and security |
| AI/ML | 3 | AI integration and optimization |
| Documentation | 4 | Technical writing and API docs |
| Orchestration | 3 | Workflow and multi-agent coordination |

## 🎯 Recommended Workflows

### New Feature Development
1. `product-manager` → Define requirements
2. `api-designer` → Design endpoints
3. `fullstack-developer` → Implement feature
4. `test-automator` → Create tests
5. `documentation-engineer` → Update docs

### Performance Optimization
1. `research-analyst` → Analyze bottlenecks
2. `refactoring-specialist` → Improve code
3. `database-administrator` → Optimize queries
4. `devops-engineer` → Infrastructure tuning

### Security Audit
1. `security-auditor` → Vulnerability scan
2. `code-reviewer` → Code analysis
3. `test-automator` → Security tests
4. `documentation-engineer` → Security documentation

## 📝 Notes

- Subagents operate with isolated contexts to prevent interference
- Each subagent has specialized prompts for optimal performance
- Subagents can be chained together for complex workflows
- Project-level subagents override global ones with the same name

## 🔗 Related Resources

- [Grantha API Documentation](../README.md)
- [VoltAgent Framework](https://github.com/VoltAgent/voltagent)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)