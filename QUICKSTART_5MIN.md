#  AgentGuard 5-Minute Quickstart

Get your AI agents protected in under 5 minutes. No complex setup, no lengthy configuration—just instant safety.

---

##  Step 1: Get Your API Key (30 seconds)

1. **Sign up** at [agentguard.ai](https://agentguard.ai)
2. Navigate to **Workspace → API Keys**
3. Click **"Create API Key"**
4. **Copy your key** (shown only once!)

```
ag_live_abc123def456...
```

 **Important**: Store this key securely. You won't see it again!

---

##  Step 2: Install the SDK (30 seconds)

### Python
```bash
pip install agentguard-sdk
```

### TypeScript/JavaScript
```bash
npm install @agentguard/sdk
# or
yarn add @agentguard/sdk
```

### Go
```bash
go get github.com/agentguard/agentguard-go
```

---

##  Step 3: Your First Safety Check (2 minutes)

### Python Example

```python
from agentguard import AgentGuardClient

# Initialize client
client = AgentGuardClient(api_key="your_api_key_here")

# Test an AI agent's response
result = client.detect_hallucination(
    agent_output="The Eiffel Tower is located in London, England.",
    ground_truth="The Eiffel Tower is in Paris, France."
)

# Check the results
print(f"Hallucination Risk: {result.hallucination_risk:.2%}")
print(f"Is Safe: {result.is_safe}")
print(f"Confidence: {result.confidence:.2%}")

if not result.is_safe:
    print(f" Warning: {result.explanation}")
```

**Output:**
```
Hallucination Risk: 95.00%
Is Safe: False
Confidence: 98.50%
 Warning: Geographic location is incorrect. The Eiffel Tower is in Paris, not London.
```

### TypeScript Example

```typescript
import { AgentGuardClient } from '@agentguard/sdk';

// Initialize client
const client = new AgentGuardClient({
  apiKey: 'your_api_key_here'
});

// Test an AI agent's response
const result = await client.detectHallucination({
  agentOutput: "The Eiffel Tower is located in London, England.",
  groundTruth: "The Eiffel Tower is in Paris, France."
});

// Check the results
console.log(`Hallucination Risk: ${(result.hallucinationRisk * 100).toFixed(2)}%`);
console.log(`Is Safe: ${result.isSafe}`);
console.log(`Confidence: ${(result.confidence * 100).toFixed(2)}%`);

if (!result.isSafe) {
  console.log(` Warning: ${result.explanation}`);
}
```

---

##  Step 4: Real-World Integration (2 minutes)

### LangChain Integration (Python)

```python
from langchain.callbacks.base import BaseCallbackHandler
from langchain.llms import OpenAI
from agentguard import AgentGuardClient

class AgentGuardCallback(BaseCallbackHandler):
    def __init__(self, api_key: str, threshold: float = 0.7):
        self.client = AgentGuardClient(api_key=api_key)
        self.threshold = threshold
    
    def on_llm_end(self, response, **kwargs):
        """Check response after LLM generates it"""
        text = response.generations[0][0].text
        
        result = self.client.detect_hallucination(
            agent_output=text,
            # ground_truth can be from your knowledge base
        )
        
        if result.hallucination_risk > self.threshold:
            print(f" High hallucination risk: {result.hallucination_risk:.2%}")
            print(f"   Explanation: {result.explanation}")
            # Optionally: raise exception, log, or retry

# Use with LangChain
llm = OpenAI(
    callbacks=[AgentGuardCallback(api_key="your_key")]
)

response = llm("Tell me about the Eiffel Tower")
```

### LangChain Integration (TypeScript)

```typescript
import { OpenAI } from "langchain/llms/openai";
import { BaseCallbackHandler } from "langchain/callbacks";
import { AgentGuardClient } from '@agentguard/sdk';

class AgentGuardCallback extends BaseCallbackHandler {
  name = "agentguard_callback";
  client: AgentGuardClient;
  threshold: number;

  constructor(apiKey: string, threshold: number = 0.7) {
    highly();
    this.client = new AgentGuardClient({ apiKey });
    this.threshold = threshold;
  }

  async handleLLMEnd(output: any) {
    const text = output.generations[0][0].text;
    
    const result = await this.client.detectHallucination({
      agentOutput: text,
    });
    
    if (result.hallucinationRisk > this.threshold) {
      console.log(` High hallucination risk: ${(result.hallucinationRisk * 100).toFixed(2)}%`);
      console.log(`   Explanation: ${result.explanation}`);
    }
  }
}

// Use with LangChain
const llm = new OpenAI({
  callbacks: [new AgentGuardCallback("your_key")]
});

const response = await llm.call("Tell me about the Eiffel Tower");
```

### FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from agentguard import AgentGuardClient
from pydantic import BaseModel

app = FastAPI()
guard = AgentGuardClient(api_key="your_api_key")

class AgentRequest(BaseModel):
    prompt: str
    response: str

@app.post("/validate-response")
async def validate_response(request: AgentRequest):
    """Validate AI agent response before returning to user"""
    
    result = guard.detect_hallucination(
        agent_output=request.response,
        # Add ground_truth from your knowledge base if available
    )
    
    if not result.is_safe:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unsafe response detected",
                "risk": result.hallucination_risk,
                "explanation": result.explanation
            }
        )
    
    return {
        "response": request.response,
        "safety_score": 1 - result.hallucination_risk,
        "validated": True
    }
```

---

##  Advanced Features

### Streaming Validation

```python
# Real-time validation as tokens stream
async for chunk in client.stream_detect(
    agent_output=streaming_response,
    ground_truth=expected_answer
):
    print(f"Token risk: {chunk.risk}")
    if chunk.risk > 0.8:
        # Stop streaming immediately
        break
```

### Batch Processing

```python
# Validate multiple responses at once
results = client.batch_detect([
    {"agent_output": "Response 1", "ground_truth": "Truth 1"},
    {"agent_output": "Response 2", "ground_truth": "Truth 2"},
    {"agent_output": "Response 3", "ground_truth": "Truth 3"},
])

for i, result in enumerate(results):
    print(f"Response {i+1}: {result.hallucination_risk:.2%} risk")
```

### Custom Rules

```python
# Add domain-specific safety rules
client.add_custom_rule(
    name="medical_accuracy",
    pattern=r"(dosage|medication|treatment)",
    severity="critical",
    action="block"
)

result = client.detect_hallucination(
    agent_output="Take 500mg of aspirin daily",
    apply_custom_rules=True
)
```

---

##  Configuration Options

### Set Detection Threshold

```python
client = AgentGuardClient(
    api_key="your_key",
    threshold=0.7,  # 70% risk threshold
    auto_block=True  # Automatically block high-risk responses
)
```

### Enable Logging

```python
import logging

logging.basicConfig(level=logging.INFO)

client = AgentGuardClient(
    api_key="your_key",
    log_level="INFO"
)
```

### Webhook Notifications

```python
client.configure_webhooks(
    url="https://your-app.com/webhooks/agentguard",
    events=["high_risk_detected", "safety_violation"],
    secret="your_webhook_secret"
)
```

---

##  Monitor in Dashboard

Visit your [AgentGuard Dashboard](https://agentguard.ai/workspace) to:

-  View real-time safety metrics
-  Analyze flagged responses
-  Track accuracy trends
-  Configure custom rules
- 👥 Manage team access

---

## 🆘 Troubleshooting

### Issue: "Invalid API Key"

**Solution:**
```python
# Verify your key is correct
client = AgentGuardClient(api_key="ag_live_...")  # Must start with ag_live_

# Check key status in dashboard
# Workspace → API Keys → Verify "Active" status
```

### Issue: "Rate Limit Exceeded"

**Solution:**
```python
# Free tier: 100 requests/month
# Upgrade to Pro: 1,000 requests/month
# Or implement caching:

from functools import lru_cache

@lru_cache(maxsize=100)
def check_safety(text: str):
    return client.detect_hallucination(agent_output=text)
```

### Issue: "Connection Timeout"

**Solution:**
```python
# Increase timeout
client = AgentGuardClient(
    api_key="your_key",
    timeout=30  # 30 seconds
)

# Or use async client
async with AgentGuardClient(api_key="your_key") as client:
    result = await client.detect_hallucination_async(...)
```

---

## 🎓 Next Steps

### Learn More
-  [Full API Documentation](https://docs.agentguard.ai)
- 🎥 [Video Tutorials](https://agentguard.ai/tutorials)
- 💬 [Join Discord Community](https://discord.gg/agentguard)
-  [Blog & Best Practices](https://agentguard.ai/blog)

### Advanced Topics
- [Multi-Model Consensus](https://docs.agentguard.ai/multi-model)
- [RAG Security](https://docs.agentguard.ai/rag-security)
- [Prompt Injection Detection](https://docs.agentguard.ai/prompt-injection)
- [Compliance & Auditing](https://docs.agentguard.ai/compliance)

### Get Help
-  Email: support@agentguard.ai
- 💬 Discord: [discord.gg/agentguard](https://discord.gg/agentguard)
- 🐛 GitHub Issues: [github.com/agentguard/issues](https://github.com/agentguard/issues)

---

##  You're All Set!

You've successfully:
-  Created an API key
-  Installed the SDK
-  Run your first safety check
-  Integrated with your AI stack

**Your AI agents are now protected!** 🛡

---

##  Pro Tips

1. **Start with high threshold** (0.8) and adjust based on your use case
2. **Use ground truth** from your knowledge base for better accuracy
3. **Enable webhooks** for real-time alerts
4. **Monitor dashboard** regularly to spot patterns
5. **Join community** to learn from other developers

---

##  Upgrade for More

**Free Tier Limits:**
- 100 queries/month
- 1 agent monitored
- Community support

**Pro Tier ($29/month):**
- 1,000 queries/month
- 10 agents monitored
- Email support
- Advanced analytics
- Custom rules

[**Upgrade Now →**](https://agentguard.ai/pricing)

---

**Questions?** We're here to help! 💬

[support@agentguard.ai](mailto:support@agentguard.ai) | [Discord](https://discord.gg/agentguard) | [Docs](https://docs.agentguard.ai)

