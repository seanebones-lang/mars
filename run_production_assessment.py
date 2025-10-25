#!/usr/bin/env python3
"""
Production Readiness Assessment for AgentGuard
Uses Claude to perform comprehensive production readiness evaluation
"""

import os
import anthropic
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_input_document():
    """Load the production readiness input document."""
    with open('PRODUCTION_READINESS_INPUT.md', 'r') as f:
        content = f.read()
    
    # Split into SYSTEM_DESCRIPTION and CURRENT_STATE
    parts = content.split('## CURRENT_STATE')
    system_desc = parts[0].replace('# AgentGuard Production Readiness Assessment - Input Document\n\n## SYSTEM_DESCRIPTION\n\n', '')
    current_state = parts[1].strip()
    
    return system_desc, current_state

def run_assessment():
    """Run the production readiness assessment using Claude."""
    
    # Load API key from environment
    api_key = os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("ERROR: CLAUDE_API_KEY environment variable not set")
        print("Please set it with: export CLAUDE_API_KEY='your-key-here'")
        return
    
    print("Loading input document...")
    system_desc, current_state = load_input_document()
    
    print(f"System Description: {len(system_desc)} characters")
    print(f"Current State: {len(current_state)} characters")
    print("\nInitializing Claude client...")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a senior DevOps and production engineering consultant who specializes in AI systems deployment. Your task is to evaluate AgentGuard, a complex AI hallucination detection system, and prepare it for full production deployment.

Here is the system description:

<system_description>
{system_desc}
</system_description>

Here is the current state of the system:

<current_state>
{current_state}
</current_state>

This is a mission-critical, expensive system that must achieve 100% production readiness. Every component, feature, and line of code must be bulletproof and ready for live clients. The system is fully hosted on Render and must perform flawlessly under production conditions.

Your goal is to conduct a comprehensive production readiness assessment and create a detailed preparation plan. You must evaluate every aspect of the system with extreme thoroughness and caution.

First, conduct a systematic analysis in <systematic_assessment> tags. In this assessment:

1. **Extract Key System Components**: List out all the major features, endpoints, SDKs, and architectural components mentioned in the system description to ensure you evaluate each one thoroughly. It's OK for this section to be quite long.

2. **Systematic Evaluation**: For each of these 10 production dimensions, note specific findings, gaps, and concerns based on the actual system details provided:
   - Code quality and testing coverage
   - Security vulnerabilities and hardening  
   - Performance optimization and scalability
   - Monitoring, logging, and observability
   - Error handling and fault tolerance
   - Infrastructure and deployment configuration
   - Data integrity and backup strategies
   - Compliance and documentation
   - Client-facing interfaces and user experience
   - Operational procedures and incident response

3. **Priority Assessment**: Categorize your findings into P0-Critical (blocking), P1-High (urgent), and P2-Medium (important) based on production impact.

Pay particular attention to the scale and complexity of this system - with 12 major features, 97 REST endpoints, multiple SDKs, and full frontend/backend architecture, you need to assess each component thoroughly rather than providing generic recommendations.

After your assessment, provide a comprehensive production readiness plan that addresses every identified gap and requirement. Structure your response with these sections:

**CRITICAL ISSUES** - Any blocking problems that must be resolved before production (P0-Critical priority)
**SECURITY HARDENING** - All security measures and vulnerability mitigations (specify P0-P2 priorities)
**PERFORMANCE OPTIMIZATION** - Scalability, speed, and resource efficiency improvements (specify priorities)
**MONITORING & OBSERVABILITY** - Complete visibility into system health and performance (specify priorities)
**TESTING STRATEGY** - Comprehensive testing approach including load, security, and integration tests (specify priorities)
**DEPLOYMENT PIPELINE** - Production-grade CI/CD with proper safeguards (specify priorities)
**OPERATIONAL PROCEDURES** - Incident response, maintenance, and support processes (specify priorities)
**COMPLIANCE & DOCUMENTATION** - All required documentation and regulatory compliance (specify priorities)
**CLIENT READINESS** - User-facing features, interfaces, and support systems (specify priorities)

For each section, provide specific, actionable items with clear priorities using this scale:
- P0-Critical: Must be completed before production launch
- P1-High: Should be completed within first month of production
- P2-Medium: Should be completed within first quarter of production

Your final response should be a complete, implementable roadmap that transforms this system into a production-ready platform capable of serving live clients with zero tolerance for failure. Focus on concrete actions, specific technologies, and measurable outcomes rather than general recommendations."""

    print("\nSending request to Claude (this may take 1-2 minutes)...")
    print("=" * 80)
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20000,
            temperature=1,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "<systematic_assessment>"}]
                }
            ]
        )
        
        # Extract response
        response_text = "<systematic_assessment>\n"
        for block in message.content:
            if hasattr(block, 'text'):
                response_text += block.text
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"PRODUCTION_READINESS_ASSESSMENT_{timestamp}.md"
        
        with open(output_file, 'w') as f:
            f.write("# AgentGuard Production Readiness Assessment\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Model:** claude-sonnet-4-20250514\n")
            f.write(f"**Company:** Mothership AI\n")
            f.write(f"**Product:** watcher.mothership-ai.com\n\n")
            f.write("---\n\n")
            f.write(response_text)
        
        print("\n" + "=" * 80)
        print(f"\n✅ Assessment complete!")
        print(f"📄 Results saved to: {output_file}")
        print(f"📊 Response length: {len(response_text)} characters")
        print(f"💰 Tokens used: ~{message.usage.input_tokens} input, ~{message.usage.output_tokens} output")
        print("\n" + "=" * 80)
        print("\nPreview of assessment:\n")
        print(response_text[:1000] + "...\n")
        print(f"\nRead full assessment: cat {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error during assessment: {e}")
        raise

if __name__ == "__main__":
    print("=" * 80)
    print("AgentGuard Production Readiness Assessment")
    print("Mothership AI - watcher.mothership-ai.com")
    print("=" * 80)
    print()
    
    run_assessment()

