<!-- eb90b727-52a1-4a5e-b1b5-e96997d0e93d 2cd0a34f-15e3-418a-a1eb-4a304236048d -->
# AgentGuard Core Detection Engine - Implementation Plan (Optimized)

## Objective
Deliver a working hallucination detection prototype targeting IT/retail AI agent validation, capitalizing on the 6-month market window before larger players close reliability gaps. Enhanced with self-consistency sampling (reduces hallucinations 20-30%) and multi-turn conversation support for agent chains.

## Technical Architecture

### Core Components
1. **LLM-as-a-Judge (Primary)**: Claude Sonnet 4.5 API (`claude-sonnet-4-5-20250929`) for factual evaluation (90-95% accuracy baseline). Self-consistency: 3-5 generations per query with majority voting
2. **Statistical Models (Secondary)**: Enhanced token-level entropy with real-time identification (arXiv Sept 2025 scalable method for 70B+ models). Unsupervised confidence estimation for first-token hallucination detection
3. **Ensemble Pipeline**: Adaptive weighting (60% Claude + 40% statistical, tunable via MLflow) with NLI-style rescoring for disputed outputs. Target 92%+ accuracy via multi-stage verification
4. **API Layer**: FastAPI endpoints with uncertainty thresholds (>0.3 flags review)
5. **Reporting**: JSON output with hallucination scores, flagged segments, and confidence intervals

### Tech Stack
- **Backend**: Python 3.12, FastAPI
- **ML/AI**: Anthropic Claude API (`claude-sonnet-4-5-20250929`), PyTorch 2.9+, Hugging Face Transformers
- **Statistical Analysis**: scikit-learn for entropy calculations
- **Deployment**: Docker, prep for AWS ECS/GCP Cloud Run
- **Dev Tools**: pytest, MLflow, Prometheus

## Implementation Phases

### Phase 1: Project Scaffold & Core Infrastructure (Week 1)

**Setup Foundation**
- Initialize Python 3.12 project structure:
  ```
  agentguard/
  ├── src/
  │   ├── api/            # FastAPI endpoints
  │   ├── judges/         # Detection engines
  │   ├── models/         # Data models
  │   └── utils/          # Helpers
  ├── tests/
  ├── data/               # Sample datasets
  ├── config/
  ├── requirements.txt
  └── README.md
  ```
- Configure `requirements.txt` with latest stable dependencies:
  - `fastapi>=0.120.0`, `uvicorn[standard]>=0.38.0`
  - `anthropic>=0.71.0`, `torch>=2.9.0`, `transformers>=4.57.1`
  - `scikit-learn>=1.7.2`, `pydantic>=2.12.3`, `mlflow>=3.5.1`
  - `pytest>=8.4.2`, `python-dotenv>=1.1.1`

**Claude API Integration (Enhanced)**
- Create `src/judges/claude_judge.py`:
  - Implement `ClaudeJudge` class with modular provider interface
  - Use `claude-sonnet-4-5-20250929` model
  - **Self-consistency implementation**: Generate 3 independent evaluations, majority vote on outputs
  - Build evaluation method using constitutional AI prompts
  - Add prompt caching for 30-50% cost reduction
  - Implement async support for high-throughput testing
  - Add retry logic and fallback to local Llama (via Ollama integration)
  - MLflow integration for usage monitoring
- Secure API key management via environment variables
- Set up rate limiting (10 concurrent requests for dev tier)

**Statistical Model Foundation (Enhanced)**
- Create `src/judges/statistical_judge.py`:
  - Enhanced token-level entropy analysis using Transformers
  - Integrate real-time scaling method (arXiv Sept 2025) for 70B+ models
  - Add unsupervised confidence estimation for first-token detection
  - Implement uncertainty intervals via bootstrapping
  - Use lightweight models (no API calls) for efficiency

**Data Preparation**
- Source 50-100 synthetic IT/retail test scenarios:
  - Server downtime diagnostics
  - Inventory lookups
  - Policy advice queries
  - **Add multi-turn conversation chains** for VISTA alignment
- Structure as JSON: `{"agent_output": "...", "ground_truth": "...", "expected_hallucination": true/false, "conversation_history": ["..."]}`

### Phase 2: Detection Pipeline & Ensemble (Week 2)

**Unified Detection Engine (Enhanced)**
- Create `src/judges/ensemble_judge.py`:
  - **Adaptive weighting**: 60% Claude + 40% statistical (tunable via MLflow experiments)
  - Implement hallucination threshold logic (>0.5 = flagged)
  - **Add NLI-style rescoring** for ambiguous/disputed outputs
  - Generate detailed reports with flagged segments and confidence bands
  - **Bootstrap confidence intervals** for transparency
- Build data models in `src/models/schemas.py`:
  - `AgentTestRequest`, `HallucinationReport`, `JudgmentResult`
  - Add `ConversationContext`, `ConfidenceInterval` schemas

**FastAPI Endpoints (Enhanced)**
- Create `src/api/main.py`:
  - `POST /test-agent`: Accept agent output + optional ground truth + conversation history
  - `GET /health`: System health check
  - Response format: `{"hallucination_risk": float, "details": {...}, "confidence_interval": [low, high], "uncertainty": float}`
  - **Uncertainty threshold**: Flag for human review if >0.3
  - Add CORS, request validation, error handling
  - Implement logging with MLflow for experiment tracking
  - **Integrate Prometheus** for quota monitoring

**Testing Infrastructure**
- Write unit tests for both judges (`tests/test_judges.py`)
- End-to-end API tests with sample scenarios
- Target **85%+ code coverage**
- Validate **92%+ detection accuracy** on test set using SemEval-2025 metrics

### Phase 3: Polish & Demo Preparation (Week 3-4)

**CLI Interface (Enhanced)**
- Create `agentguard_cli.py`:
  - Command: `python agentguard_cli.py --input sample.json --output report.json --multi-turn`
  - Support batch testing and multi-turn conversation demos

**Deployment Package**
- Dockerize application (`Dockerfile`, `docker-compose.yml`)
- Environment configuration templates
- **Add air-gapped mode** with local models for enterprise security
- Health checks and monitoring hooks

**Documentation (Enhanced)**
- README with:
  - Setup instructions
  - **API specification with OpenAPI docs**
  - Sample use cases (IT agent testing)
  - Demo scripts
  - Architecture diagram
  - **Cost estimates for Claude 4.5 pricing**
  - Scaling notes
- Architecture diagram
- Performance benchmarks

**Demo Assets (Enhanced)**
- Prepare 3-5 enterprise scenarios with multi-turn support:
  1. IT agent detecting hallucinated server fixes in conversation chains
  2. Retail agent validating inventory queries with conversation history
  3. Employee assistance agent policy checks across multiple exchanges
- Performance benchmarks: **<0.5s latency, 92%+ accuracy**
- Client pitch deck integration points

## Key Implementation Details

### Claude Judge Prompt Template (Self-Consistency)
```
You are an impartial AI judge evaluating factual accuracy. Generate 3 independent evaluations and vote on the final.

Agent Output: {agent_output}
Ground Truth/Reference: {ground_truth}
Conversation History: {history}

For each evaluation:
1. Score factual accuracy 0-1 (1=fully accurate, 0=completely hallucinated)
2. Explain any inaccuracies or hallucinations
3. List specific hallucinated segments

Final Response in JSON: {"score": float (majority), "explanation": "str (consensus)", "hallucinated_segments": ["list"], "samples": [...]}
```

### Ensemble Scoring Logic (Enhanced)
- Claude score (0-1) weighted at 60%
- Entropy score (0-1) weighted at 40%
- Add confidence interval via bootstrapping (10 samples)
- Final hallucination risk = 1 - combined_score
- Flag if risk > 0.5
- **Escalate to human review if uncertainty > 0.3**
- NLI-style rescoring for ambiguous cases

### Cost Management
- Dev tier budget: $10-50 for prototype testing
- Estimated production cost: $0.50-$2 per 100 tests (lower with caching)
- Implement prompt caching to reduce token costs 30-50%
- Monitor via MLflow and Prometheus

## Deliverables

1. **Working Prototype**: API/CLI tool with multi-turn conversation support and 92%+ accuracy
2. **Code Repository**: Clean, documented, SOC-2-ready codebase
3. **Test Suite**: 85%+ coverage with validated accuracy metrics
4. **Docker Container**: One-command deployment with air-gapped mode
5. **Documentation**: Setup, OpenAPI specs, demo scripts, architecture diagrams
6. **Demo Package**: 3-5 enterprise scenarios with latency/accuracy benchmarks

## Risk Mitigation

- **API Quotas**: Monitor with Prometheus, implement fallback to local Llama via Ollama
- **Accuracy Variance**: Cross-validate with statistical models, tune ensemble weights via MLflow, add diversity per 2025 ensemble strategies
- **Dataset Quality**: Use high-fidelity synthetic data, validate against known hallucinations, incorporate edge cases from real-time detection methods
- **Market Timing**: Target 6-8 week alpha launch, focus on mid-size retail/IT clients
- **Model Reliability**: Self-consistency sampling and NLI rescoring reduce false positives by 20-30%

## Next Steps Post-Prototype

1. Client alpha testing with 3-5 early adopters
2. Add Diversion Decoding and MHAD methods (Phase 2, Month 2-3)
3. Build enterprise dashboard and analytics
4. Implement integration layer for LangChain, CrewAI
5. SOC 2 compliance audit and white-label features


### To-dos

- [ ] Initialize Python 3.12 project structure (agentguard/) with src/, tests/, config/ directories and requirements.txt with latest 2025 dependencies
- [ ] Implement ClaudeJudge class with Sonnet 4.5 API, self-consistency sampling (3 generations + voting), caching, and retry logic
- [ ] Build enhanced statistical judge with token-level entropy, real-time scaling (arXiv Sept 2025), and unsupervised confidence estimation
- [ ] Create 50-100 synthetic IT/retail test scenarios with ground truth labels and multi-turn conversation histories
- [ ] Build adaptive ensemble judge with NLI rescoring, confidence intervals, and uncertainty thresholding (0.3 review trigger)
- [ ] Create FastAPI app with /test-agent (multi-turn support) and /health endpoints, Prometheus monitoring, and uncertainty handling
- [ ] Write unit and integration tests targeting 85%+ coverage and 92%+ detection accuracy (SemEval-2025 metrics)
- [ ] Build CLI tool with multi-turn support for batch testing and demos (agentguard_cli.py)
- [ ] Create Dockerfile, docker-compose.yml with air-gapped mode for local model fallback
- [ ] Write README with OpenAPI specs, architecture docs, Claude 4.5 cost estimates, and demo scripts
- [ ] Prepare 3-5 enterprise multi-turn demo scenarios with <0.5s latency and 92%+ accuracy benchmarks