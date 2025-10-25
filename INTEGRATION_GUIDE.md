# AgentGuard Integration Guide

## Quick Start for Testing with Your Agentic Platform

This guide explains how to integrate AgentGuard's hallucination detection into your existing agentic AI platform.

---

## Integration Options

### Option 1: Webhook Monitoring (Recommended for Testing)

Send agent responses to AgentGuard for real-time hallucination detection.

```python
import requests

# After your agent generates a response
agent_response = your_agent.generate(user_query)

# Monitor it with AgentGuard
monitoring_result = requests.post(
    "http://localhost:8000/test-agent",
    json={
        "agent_output": agent_response,
        "ground_truth": "Check this response for factual accuracy and hallucinations",
        "conversation_history": []
    }
)

result = monitoring_result.json()

# Check if hallucination risk is high
if result["hallucination_risk"] > 0.75:
    print(f" High hallucination risk: {result['hallucination_risk']:.1%}")
    print(f"Flagged segments: {result['details']['hallucinated_segments']}")
    # Take action: alert, log, block, etc.

# Continue with your workflow
return agent_response
```

---

### Option 2: Python SDK Wrapper

Wrap your agent calls with AgentGuard monitoring.

```python
# agentguard_wrapper.py
import requests
from functools import wraps

AGENTGUARD_API = "http://localhost:8000/test-agent"

def monitor_hallucinations(threshold=0.75, alert_on_risk=True):
    """Decorator to monitor agent outputs for hallucinations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute agent function
            output = func(*args, **kwargs)
            
            # Monitor with AgentGuard
            try:
                result = requests.post(AGENTGUARD_API, json={
                    "agent_output": output,
                    "ground_truth": "Validate this for accuracy and hallucinations",
                    "conversation_history": []
                }, timeout=15)
                
                data = result.json()
                risk = data["hallucination_risk"]
                
                if risk > threshold and alert_on_risk:
                    print(f" HALLUCINATION DETECTED: {risk:.1%} risk")
                    print(f"Agent: {func.__name__}")
                    print(f"Flagged: {data['details']['hallucinated_segments']}")
                    
                    # Optional: Log to monitoring system
                    # log_to_datadog(func.__name__, risk, output)
                
            except Exception as e:
                print(f"AgentGuard monitoring failed: {e}")
            
            return output
        return wrapper
    return decorator

# Usage in your agent code
@monitor_hallucinations(threshold=0.75)
def support_agent(user_query):
    response = your_llm.generate(
        prompt=f"Answer support question: {user_query}"
    )
    return response

# Now ehighly call is automatically monitored
response = support_agent("How do I reset my password?")
```

---

### Option 3: Async Batch Monitoring

Monitor agent conversations after the fact (audit/analysis).

```python
import asyncio
import aiohttp

async def batch_monitor_conversations(conversations: list):
    """
    Monitor a batch of agent conversations.
    
    Args:
        conversations: List of dicts with 'id', 'agent_output', 'context'
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for conv in conversations:
            task = session.post(
                "http://localhost:8000/test-agent",
                json={
                    "agent_output": conv["agent_output"],
                    "ground_truth": "Validate for accuracy",
                    "conversation_history": conv.get("history", [])
                }
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Process results
        flagged = []
        for i, response in enumerate(results):
            data = await response.json()
            if data["hallucination_risk"] > 0.75:
                flagged.append({
                    "conversation_id": conversations[i]["id"],
                    "risk": data["hallucination_risk"],
                    "segments": data["details"]["hallucinated_segments"]
                })
        
        return flagged

# Usage: Audit last 100 support tickets
conversations = fetch_last_100_tickets()
flagged_conversations = asyncio.run(batch_monitor_conversations(conversations))

print(f"Flagged {len(flagged_conversations)} high-risk conversations")
for conv in flagged_conversations:
    print(f"  Ticket {conv['conversation_id']}: {conv['risk']:.1%} risk")
```

---

## Testing Your Integration

### 1. Start AgentGuard Services

```bash
# Terminal 1: Start backend
cd /Users/seanmcdonnell/Desktop/HAL
source venv/bin/activate
export CLAUDE_API_KEY="your-key-here"
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend (optional)
cd /Users/seanmcdonnell/Desktop/HAL/agentguard-ui
npm run dev
```

### 2. Test Endpoint

```bash
curl -X POST http://localhost:8000/test-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "To fix your server, reboot the quantum router",
    "ground_truth": "Check for technical accuracy",
    "conversation_history": []
  }'
```

Expected response:
```json
{
  "hallucination_risk": 0.89,
  "details": {
    "claude_score": 0.05,
    "claude_explanation": "The statement contains fabricated technology...",
    "hallucinated_segments": ["quantum router"],
    "statistical_score": 0.23,
    "needs_review": false
  },
  "confidence_interval": [0.18, 0.28],
  "uncertainty": 0.05
}
```

---

## Integration Patterns by Use Case

### IT Support Agent

```python
def handle_support_ticket(ticket):
    # Agent generates response
    response = it_support_agent.answer(ticket.question)
    
    # Check for hallucinations before sending
    check = monitor_response(response)
    
    if check["hallucination_risk"] > 0.7:
        # High risk - escalate to human
        ticket.escalate_to_human(
            reason=f"AI hallucination detected: {check['details']['hallucinated_segments']}"
        )
        return None
    
    # Safe to send
    ticket.respond(response)
    return response
```

### Retail Chatbot

```python
def retail_assistant(customer_query):
    response = chatbot.generate(customer_query)
    
    # Monitor for inventory/pricing hallucinations
    check = agentguard_check(response)
    
    if check["hallucination_risk"] > 0.6:
        # Don't give false info about products/prices
        return "Let me check with a specialist about that."
    
    return response
```

### HR/Policy Agent

```python
def hr_policy_assistant(employee_question, policy_docs):
    response = hr_agent.answer(employee_question, context=policy_docs)
    
    # Verify against actual policies
    check = agentguard_check(
        agent_output=response,
        ground_truth=policy_docs  # Use actual docs as ground truth
    )
    
    if check["hallucination_risk"] > 0.5:
        # Policy info must be accurate
        log_compliance_alert(employee_question, response, check)
        return "Please consult with HR directly for accurate policy information."
    
    return response
```

---

## API Reference

### POST /test-agent

**Request:**
```json
{
  "agent_output": "string (required) - The agent's response to check",
  "ground_truth": "string (optional) - Reference material or validation context",
  "conversation_history": ["string"] (optional) - Previous conversation turns
}
```

**Response:**
```json
{
  "hallucination_risk": 0.0-1.0,  // 0=accurate, 1=complete hallucination
  "details": {
    "claude_score": 0.0-1.0,  // LLM judge score
    "claude_explanation": "string",  // Why it's flagged
    "hallucinated_segments": ["string"],  // Specific false claims
    "statistical_score": 0.0-1.0,  // Token-level analysis
    "needs_review": boolean  // High uncertainty flag
  },
  "confidence_interval": [lower, upper],  // Statistical confidence
  "uncertainty": 0.0-1.0  // How certain is the detection
}
```

---

## Performance & Cost Considerations

**Latency:**
- Average: 2-5 seconds per check
- Claude API: 1-3s (varies by output length)
- Statistical analysis: <0.5s

**Cost (using Claude API):**
- ~$0.001-0.005 per check (depending on output length)
- 1000 checks/day ≈ $1-5/day
- Recommend monitoring high-risk queries only at scale

**Optimization:**
- Monitor 10-20% of responses (sample high-risk scenarios)
- Cache results for identical responses
- Use local statistical model for pre-filtering (fast), then Claude for flagged cases

---

## Next Steps

1. **Test with sample data** from your agentic platform
2. **Tune threshold** - what hallucination_risk level triggers action? (0.5? 0.75?)
3. **Add alerting** - Slack webhook when high risk detected
4. **Log for analysis** - Store results for trend analysis
5. **Integrate into CI/CD** - Test agents before deployment

---

## Questions?

- **Backend API:** http://localhost:8000/docs (OpenAPI interactive docs)
- **Frontend UI:** http://localhost:3001 (test interface)
- **Repository:** https://github.com/seanebones-lang/mars

Ready to test with your platform! Start with Option 1 (simple webhook) to validate it works with your agents.

