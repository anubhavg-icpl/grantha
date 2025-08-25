"""
DeepResearch: Multi-turn research feature for comprehensive topic investigation.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
import json

from api.rag import RAG
from api.config import get_model_config
from api.prompts import DEEP_RESEARCH_PLAN_PROMPT, DEEP_RESEARCH_UPDATE_PROMPT, DEEP_RESEARCH_CONCLUSION_PROMPT

logger = logging.getLogger(__name__)


class DeepResearch:
    """
    Implements multi-turn research for thorough topic investigation.
    """
    
    MAX_ITERATIONS = 5
    
    def __init__(self, 
                 provider: str = "google",
                 model: Optional[str] = None,
                 rag_instance: Optional[RAG] = None):
        """
        Initialize DeepResearch.
        
        Args:
            provider: LLM provider to use
            model: Specific model to use
            rag_instance: Existing RAG instance to use for retrieval
        """
        self.provider = provider
        self.model = model
        self.rag = rag_instance or RAG(provider=provider, model=model)
        self.research_history = []
        self.iteration_count = 0
        
    async def conduct_research(self, 
                              query: str,
                              repo_url: str,
                              repo_type: str = "github",
                              token: Optional[str] = None,
                              language: str = "en") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Conduct deep research on a topic through multiple iterations.
        
        Args:
            query: The research question
            repo_url: Repository URL for context
            repo_type: Type of repository
            token: Access token for private repos
            language: Language for responses
            
        Yields:
            Research updates at each stage
        """
        logger.info(f"Starting deep research for query: {query}")
        
        # Prepare the RAG retriever if not already prepared
        if not hasattr(self.rag, 'retriever') or self.rag.retriever is None:
            self.rag.prepare_retriever(repo_url, repo_type, token)
        
        # Stage 1: Research Plan
        yield await self._create_research_plan(query, language)
        
        # Stage 2-4: Research Iterations
        while self.iteration_count < self.MAX_ITERATIONS - 1:
            research_update = await self._conduct_research_iteration(query, language)
            yield research_update
            
            # Check if research is complete
            if self._is_research_complete(research_update):
                break
                
        # Final Stage: Conclusion
        yield await self._create_conclusion(query, language)
        
    async def _create_research_plan(self, query: str, language: str) -> Dict[str, Any]:
        """
        Create initial research plan.
        
        Args:
            query: Research question
            language: Response language
            
        Returns:
            Research plan dictionary
        """
        logger.info("Creating research plan")
        
        # Get initial context from RAG
        initial_context = await self._get_relevant_context(query)
        
        # Generate research plan
        plan_prompt = DEEP_RESEARCH_PLAN_PROMPT.format(
            query=query,
            context=initial_context,
            language=language
        )
        
        plan_response = await self._generate_response(plan_prompt)
        
        research_plan = {
            "stage": "research_plan",
            "iteration": 0,
            "timestamp": datetime.now().isoformat(),
            "content": plan_response,
            "type": "plan",
            "query": query,
            "next_steps": self._extract_next_steps(plan_response)
        }
        
        self.research_history.append(research_plan)
        self.iteration_count = 1
        
        return research_plan
    
    async def _conduct_research_iteration(self, query: str, language: str) -> Dict[str, Any]:
        """
        Conduct a single research iteration.
        
        Args:
            query: Research question
            language: Response language
            
        Returns:
            Research update dictionary
        """
        logger.info(f"Conducting research iteration {self.iteration_count}")
        
        # Get previous research context
        previous_research = self._summarize_previous_research()
        
        # Identify areas needing more investigation
        focus_areas = self._identify_focus_areas(previous_research)
        
        # Get targeted context for focus areas
        targeted_context = await self._get_targeted_context(query, focus_areas)
        
        # Generate research update
        update_prompt = DEEP_RESEARCH_UPDATE_PROMPT.format(
            query=query,
            previous_research=previous_research,
            new_context=targeted_context,
            focus_areas=focus_areas,
            iteration=self.iteration_count,
            language=language
        )
        
        update_response = await self._generate_response(update_prompt)
        
        research_update = {
            "stage": "research_update",
            "iteration": self.iteration_count,
            "timestamp": datetime.now().isoformat(),
            "content": update_response,
            "type": "update",
            "focus_areas": focus_areas,
            "insights": self._extract_insights(update_response)
        }
        
        self.research_history.append(research_update)
        self.iteration_count += 1
        
        return research_update
    
    async def _create_conclusion(self, query: str, language: str) -> Dict[str, Any]:
        """
        Create final research conclusion.
        
        Args:
            query: Research question
            language: Response language
            
        Returns:
            Conclusion dictionary
        """
        logger.info("Creating research conclusion")
        
        # Compile all research findings
        all_findings = self._compile_all_findings()
        
        # Generate comprehensive conclusion
        conclusion_prompt = DEEP_RESEARCH_CONCLUSION_PROMPT.format(
            query=query,
            all_research=all_findings,
            total_iterations=self.iteration_count,
            language=language
        )
        
        conclusion_response = await self._generate_response(conclusion_prompt)
        
        conclusion = {
            "stage": "conclusion",
            "iteration": self.iteration_count,
            "timestamp": datetime.now().isoformat(),
            "content": conclusion_response,
            "type": "conclusion",
            "total_iterations": self.iteration_count,
            "key_findings": self._extract_key_findings(conclusion_response)
        }
        
        self.research_history.append(conclusion)
        
        return conclusion
    
    async def _get_relevant_context(self, query: str) -> str:
        """Get relevant context from the repository."""
        try:
            # Use RAG to retrieve relevant documents
            if hasattr(self.rag, 'retriever') and self.rag.retriever:
                documents = self.rag.retriever.retrieve(query, top_k=5)
                context = "\n\n".join([doc.text for doc in documents])
                return context[:4000]  # Limit context size
            return "No context available"
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return "Error retrieving context"
    
    async def _get_targeted_context(self, query: str, focus_areas: List[str]) -> str:
        """Get context targeted at specific focus areas."""
        contexts = []
        for area in focus_areas[:3]:  # Limit to top 3 areas
            area_query = f"{query} {area}"
            context = await self._get_relevant_context(area_query)
            contexts.append(f"### Context for {area}:\n{context}")
        return "\n\n".join(contexts)
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response using the configured model."""
        try:
            model_config = get_model_config(self.provider, self.model)
            model_client = model_config["model_client"]()
            
            # Generate response
            response = await model_client.acall(
                api_kwargs={"messages": [{"role": "user", "content": prompt}]},
                model_kwargs=model_config["model_kwargs"],
                model_type="LLM"
            )
            
            # Extract text from response
            if hasattr(response, 'data'):
                return response.data
            elif isinstance(response, str):
                return response
            else:
                # Handle async generator
                full_response = ""
                async for chunk in response:
                    full_response += chunk
                return full_response
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _summarize_previous_research(self) -> str:
        """Summarize previous research iterations."""
        summary = []
        for item in self.research_history:
            summary.append(f"**{item['stage'].replace('_', ' ').title()}** (Iteration {item['iteration']}):")
            if 'insights' in item:
                summary.append(f"Key Insights: {', '.join(item['insights'][:3])}")
            else:
                # Extract first few lines of content
                content_preview = item['content'][:500] + "..."
                summary.append(content_preview)
        return "\n\n".join(summary)
    
    def _identify_focus_areas(self, previous_research: str) -> List[str]:
        """Identify areas that need more investigation."""
        # Simple heuristic: extract questions and unknowns from previous research
        focus_areas = []
        
        # Look for question patterns
        if "unclear" in previous_research.lower():
            focus_areas.append("clarification of unclear aspects")
        if "?" in previous_research:
            focus_areas.append("answering open questions")
        if "further" in previous_research.lower():
            focus_areas.append("deeper investigation")
        if "implementation" in previous_research.lower():
            focus_areas.append("implementation details")
        if "example" in previous_research.lower():
            focus_areas.append("concrete examples")
            
        # Default focus areas if none found
        if not focus_areas:
            focus_areas = ["technical details", "practical applications", "best practices"]
            
        return focus_areas[:3]  # Limit to 3 focus areas
    
    def _extract_next_steps(self, plan_response: str) -> List[str]:
        """Extract next steps from research plan."""
        steps = []
        lines = plan_response.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['step', 'investigate', 'analyze', 'examine']):
                steps.append(line.strip())
        return steps[:5]  # Top 5 steps
    
    def _extract_insights(self, response: str) -> List[str]:
        """Extract key insights from research update."""
        insights = []
        lines = response.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['found', 'discovered', 'identified', 'shows', 'indicates']):
                insights.append(line.strip()[:100])  # Truncate long insights
        return insights[:5]
    
    def _extract_key_findings(self, conclusion: str) -> List[str]:
        """Extract key findings from conclusion."""
        findings = []
        lines = conclusion.split('\n')
        for line in lines:
            if any(marker in line for marker in ['•', '-', '*', '1.', '2.', '3.']):
                finding = line.strip().lstrip('•-*123456789. ')
                if finding:
                    findings.append(finding[:150])  # Truncate long findings
        return findings[:10]  # Top 10 findings
    
    def _compile_all_findings(self) -> str:
        """Compile all research findings."""
        findings = []
        for item in self.research_history:
            findings.append(f"### {item['stage'].replace('_', ' ').title()} (Iteration {item['iteration']})")
            findings.append(item['content'])
            if 'insights' in item and item['insights']:
                findings.append("\n**Key Insights:**")
                for insight in item['insights']:
                    findings.append(f"- {insight}")
        return "\n\n".join(findings)
    
    def _is_research_complete(self, research_update: Dict[str, Any]) -> bool:
        """
        Determine if research is complete.
        
        Args:
            research_update: Latest research update
            
        Returns:
            True if research should conclude
        """
        # Check for completion indicators
        content = research_update.get('content', '').lower()
        
        completion_indicators = [
            'comprehensive understanding achieved',
            'all aspects covered',
            'no further investigation needed',
            'research complete',
            'final answer'
        ]
        
        return any(indicator in content for indicator in completion_indicators)


# Add DeepResearch prompts
DEEP_RESEARCH_PLAN_PROMPT = """
You are conducting deep research on the following topic. Create a comprehensive research plan.

**Research Question:** {query}

**Initial Context:**
{context}

**Language:** {language}

Create a structured research plan that includes:
1. Key areas to investigate
2. Questions to answer
3. Information gaps to fill
4. Methodology for investigation
5. Expected outcomes

Format your response as a clear, structured research plan.
"""

DEEP_RESEARCH_UPDATE_PROMPT = """
Continue the deep research investigation.

**Original Question:** {query}
**Research Iteration:** {iteration}

**Previous Research:**
{previous_research}

**Focus Areas for This Iteration:**
{focus_areas}

**New Context Retrieved:**
{new_context}

**Language:** {language}

Provide a research update that:
1. Builds on previous findings
2. Investigates the focus areas
3. Identifies new insights
4. Highlights remaining questions
5. Suggests next steps if needed

Be thorough and analytical in your investigation.
"""

DEEP_RESEARCH_CONCLUSION_PROMPT = """
Provide a comprehensive conclusion to the research investigation.

**Original Question:** {query}
**Total Research Iterations:** {total_iterations}

**All Research Findings:**
{all_research}

**Language:** {language}

Create a final conclusion that:
1. Synthesizes all findings
2. Provides a complete answer to the original question
3. Highlights key discoveries
4. Notes any limitations or caveats
5. Offers actionable recommendations

Structure your conclusion clearly with:
- Executive Summary
- Detailed Findings
- Key Takeaways
- Recommendations
"""