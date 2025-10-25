# ❓ AgentGuard Frequently Asked Questions (FAQ)

**Last Updated**: November 6, 2025

---

##  Getting Started

### What is AgentGuard?
AgentGuard is a production-grade AI safety platform that helps developers detect hallucinations, block prompt injections, and optimize AI costs. Think of it as a security layer for your AI agents.

### How does it work?
AgentGuard analyzes your AI's inputs and outputs in real-time using multiple detection methods:
1. **Multi-model consensus** - Multiple AI models vote on safety
2. **Semantic analysis** - Understanding context and meaning
3. **Pattern matching** - Detecting known attack patterns
4. **Uncertainty quantification** - Measuring AI confidence

### Do I need to change my existing code?
Minimal changes! For LangChain/LlamaIndex, just add our callback handler. For other frameworks, wrap your AI calls with our SDK. Most integrations take < 10 minutes.

### What languages/frameworks do you support?
- **SDKs**: Python, TypeScript/JavaScript, Go
- **Frameworks**: LangChain, LlamaIndex, CrewAI
- **APIs**: REST API for any language
- **Models**: OpenAI, Anthropic, Cohere, Hugging Face, custom models

---

##  Pricing & Billing

### How much does AgentGuard cost?
- **Free**: 100 queries/month, perfect for testing
- **Pro**: $49/month for 10,000 queries
- **Business**: $299/month for 100,000 queries
- **Enterprise**: Custom pricing for unlimited scale

See full pricing at [agentguard.ai/pricing](https://agentguard.ai/pricing)

### What counts as a "query"?
One query = one safety check. If you check both user input and agent output, that's 2 queries. Streaming validation counts tokens, not messages.

### Can I save money with AgentGuard?
Yes! Semantic caching reduces redundant AI calls by 40-60%, often saving more than AgentGuard costs. Plus, catching hallucinations early prevents costly mistakes.

### What happens if I exceed my tier limit?
We'll send you a notification. On the free tier, requests are rate-limited. On paid tiers, we'll continue service and bill overage at $0.005/query.

### Can I upgrade/downgrade anytime?
Yes! Upgrade instantly. Downgrades take effect at the next billing cycle. No long-term contracts required.

---

##  Security & Privacy

### Is my data secure?
Absolutely. We use:
- **TLS 1.3** encryption for all data in transit
- **AES-256** encryption for data at rest
- **SOC 2 Type II** compliance (in progress)
- **GDPR** compliant
- **Regular security audits** (95/100 security score)

### Do you store my AI prompts/responses?
We store metadata (timestamps, safety scores) for 30 days. Full prompt/response text is optional and encrypted. You control retention policies.

### Can I self-host AgentGuard?
Enterprise plans include on-premise deployment options. Contact sales@agentguard.ai for details.

### What about compliance (HIPAA, SOC 2, etc.)?
- **GDPR**: Fully compliant
- **SOC 2**: Certification in progress (Q1 2026)
- **HIPAA**: Available for Enterprise plans
- **ISO 27001**: Planned for Q2 2026

---

##  Features & Capabilities

### What is hallucination detection?
Hallucination detection identifies when AI models generate false or fabricated information. AgentGuard uses multi-model consensus to achieve 95%+ accuracy.

### What is prompt injection protection?
Prompt injection is when users try to manipulate your AI with malicious prompts. AgentGuard blocks these attacks before they reach your model.

### What is semantic caching?
Instead of exact-match caching, semantic caching finds similar prompts using embeddings. This catches 40-60% more cache hits, dramatically reducing API costs.

### What is streaming validation?
For streaming responses (like ChatGPT), AgentGuard validates each token in real-time, flagging issues as they happen instead of waiting for the full response.

### Can I customize detection thresholds?
Yes! Adjust sensitivity for your use case:
- **High sensitivity**: Catch more issues, more false positives
- **Balanced**: Default setting (recommended)
- **Low sensitivity**: Fewer false positives, might miss edge cases

### Do you support webhooks?
Yes! Get real-time alerts in Slack, Teams, email, or custom endpoints when safety issues are detected.

---

##  Technical Questions

### What's the API latency?
AgentGuard adds <100ms latency. With caching enabled, responses are often faster than direct API calls.

### What's your uptime SLA?
- **Free**: Best effort (typically 99.5%+)
- **Pro**: 99.9% uptime SLA
- **Business**: 99.95% uptime SLA
- **Enterprise**: 99.99% uptime SLA with dedicated infrastructure

### How do I handle rate limits?
Each tier has rate limits:
- **Free**: 10 requests/minute
- **Pro**: 100 requests/minute
- **Business**: 1000 requests/minute
- **Enterprise**: Custom limits

Use our SDK's built-in retry logic or implement exponential backoff.

### Can I use AgentGuard with multiple AI models?
Yes! AgentGuard works with any LLM:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Cohere
- Hugging Face models
- Custom/local models

### What about batch processing?
Yes! Use our batch API to process multiple prompts efficiently. Great for testing, evaluation, and offline analysis.

### Can I test AgentGuard locally?
Yes! Use our test mode with mock responses, or run against our staging environment. No credit card required for testing.

---

##  Analytics & Monitoring

### What metrics can I track?
- **Safety metrics**: Hallucinations detected, attacks blocked
- **Performance**: Response time, cache hit rate
- **Usage**: API calls, cost savings
- **Business**: User engagement, conversion rates

### Can I export my data?
Yes! Export to CSV, JSON, or connect via API. Enterprise plans include data warehouse integration.

### Do you have a status page?
Yes! Check real-time status at [status.agentguard.ai](https://status.agentguard.ai)

### Can I set up custom alerts?
Yes! Configure alerts for:
- High error rates
- Unusual patterns
- Cost thresholds
- Security incidents

---

## 🤝 Support & Community

### How do I get help?
- **Free tier**: Documentation, FAQ, community Slack
- **Pro tier**: Email support (<24h response)
- **Business tier**: Priority support (<4h response)
- **Enterprise tier**: Dedicated account manager (<1h response)

### Where is your documentation?
Complete docs at [docs.agentguard.ai](https://docs.agentguard.ai)

### Do you have a community?
Yes! Join our Slack community with 500+ developers:
[Join AgentGuard Slack](https://agentguard.ai/slack)

### Can I request features?
Absolutely! Submit feature requests via:
- GitHub Discussions
- Community Slack
- Email: features@agentguard.ai

### Do you offer training?
- **Self-service**: Video tutorials, documentation
- **Pro**: Monthly office hours
- **Business**: Quarterly training sessions
- **Enterprise**: Custom training programs

---

##  Advanced Use Cases

### Can I use AgentGuard for evaluation?
Yes! Many teams use AgentGuard to evaluate AI models before deployment. Batch API is perfect for this.

### Does it work with RAG systems?
Absolutely! AgentGuard is excellent for RAG (Retrieval-Augmented Generation):
- Validate retrieved documents
- Check generated responses
- Detect hallucinations in citations

### Can I use it for fine-tuning?
Yes! Use AgentGuard to:
- Filter training data
- Validate fine-tuned outputs
- Compare model versions

### What about multi-agent systems?
Perfect for multi-agent systems! Monitor each agent independently and track inter-agent communication safety.

### Can I build custom detection rules?
Enterprise plans support custom detection rules and models. Contact sales@agentguard.ai

---

## 🌍 Enterprise Questions

### Do you offer volume discounts?
Yes! Contact sales@agentguard.ai for custom pricing at scale.

### Can we get a dedicated instance?
Yes! Enterprise plans include dedicated infrastructure with custom SLAs.

### Do you support SSO?
Yes! SAML, OAuth2, and LDAP integration available for Business and Enterprise plans.

### What about RBAC (role-based access control)?
Full RBAC available for Business and Enterprise plans. Define custom roles and permissions.

### Can we get a custom contract?
Yes! We work with your legal team on custom MSAs, DPAs, and BAAs.

---

## 🔄 Migration & Integration

### How long does integration take?
- **Simple integration**: 10 minutes
- **Full integration**: 1-2 hours
- **Enterprise deployment**: 1-2 weeks

### Can you help with migration?
Yes! Business and Enterprise plans include migration assistance.

### Do you have a staging environment?
Yes! Test against staging before production deployment.

### Can I run A/B tests?
Yes! Use our A/B testing framework to compare detection strategies.

---

## 📞 Contact & Sales

### How do I contact sales?
- **Email**: sales@agentguard.ai
- **Schedule call**: [Book a demo](https://agentguard.ai/demo)
- **Phone**: +1 (555) 123-4567

### How do I contact support?
- **Email**: support@agentguard.ai
- **Slack**: [Community Slack](https://agentguard.ai/slack)
- **Emergency**: enterprise@agentguard.ai (Enterprise only)

### Where are you located?
Headquarters: San Francisco, CA  
Remote team across US, Europe, and Asia

### Are you hiring?
Yes! Check [agentguard.ai/careers](https://agentguard.ai/careers)

---

## 🎓 Learning Resources

### Where can I learn more?
- **Documentation**: [docs.agentguard.ai](https://docs.agentguard.ai)
- **Blog**: [agentguard.ai/blog](https://agentguard.ai/blog)
- **YouTube**: [AgentGuard Channel](https://youtube.com/@agentguard)
- **GitHub**: [github.com/agentguard](https://github.com/agentguard)

### Do you have case studies?
Yes! Read how teams use AgentGuard:
- [FinTech AI Safety](https://agentguard.ai/case-studies/fintech)
- [Healthcare Compliance](https://agentguard.ai/case-studies/healthcare)
- [E-commerce Chatbots](https://agentguard.ai/case-studies/ecommerce)

### Can I contribute to AgentGuard?
Yes! We're open source friendly:
- Contribute to our SDKs
- Submit bug reports
- Suggest features
- Write blog posts

---

## ❓ Still Have Questions?

**Can't find your answer?**
-  Email: support@agentguard.ai
- 💬 Slack: [Join our community](https://agentguard.ai/slack)
- 📞 Call: +1 (555) 123-4567
-  Book: [Schedule a call](https://agentguard.ai/demo)

We typically respond within 24 hours!

---

**Last Updated**: November 6, 2025  
**Version**: 1.0

*Making AI development safe, one question at a time.* 🛡

