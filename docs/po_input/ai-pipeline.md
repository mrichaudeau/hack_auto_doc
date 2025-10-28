# AI Content Pipeline with Langgraph Orchestration

## Overview / Context

The AI Pipeline is the production engine of the technology watch platform. It ensures continuous, automated flow from raw information discovery to publication of synthesized, relevant, and indexed reports. This feature transforms web content into curated technology intelligence for end users.

**Target Users:**
- System (automated background processing)
- Administrators (monitoring and troubleshooting)
- Indirectly benefits end users through quality content generation

**Strategic Importance:**
- Core value creation mechanism of the platform
- Differentiator through intelligent agent-based processing
- Enables scalable content production without manual curation

## Functional Requirements

### Stateful Agent Workflow Architecture

The pipeline uses a **Stateful Graph** orchestrated by **Langgraph** and executed by Celery workers. Each step is an autonomous agent making decisions to optimize quality:

1. **Collection Agent (Firecrawl):** Scrapes web sources defined for the subject
2. **Relevance Agent:** Analyzes raw results to determine if information is new, non-duplicate, and meets quality criteria
3. **Synthesis Agent (LLM):** Condenses relevant content and reformats into structured, readable report
4. **Verification Agent (Quality Check):** Evaluates quality, coherence, and absence of hallucinations. Can return report to Synthesis Agent for corrections (feedback loop)
5. **Indexation Agent:** Converts final report to vector embedding and stores in pgvector

### Web Scraping with Firecrawl

**Firecrawl** is the designated tool for its ability to handle dynamic sites (JavaScript) and return cleaned, structured content (Markdown), reducing preprocessing complexity.

- Web source URLs defined by administrators in Subject Management (Bloc 2)
- Handles JavaScript-rendered content automatically
- Returns Markdown format for consistent processing

### Asynchronous Task Management with Celery

All pipeline processing runs in background to avoid blocking main API.

**Task Triggering:**
- New subscription (bootstrap, see RF-SUB-004 in Bloc 2)
- Scheduled recurring tasks via **Celery Beat** (daily)

**Distributed Locking:**
- Redis-based locking mechanism (e.g., `cache.lock()`) prevents concurrent processing of same subject by multiple workers

## User Stories

### US-1: Configure Celery Worker Base Task
**As a** developer
**I want to** configure base Celery task to launch monitoring process for a given subject
**So that** the pipeline can be triggered manually or by scheduler

**Acceptance Criteria:**
- [ ] Celery task `trigger_subject_monitoring(subject_id, trigger='manual')` is defined
- [ ] Task can be called manually via Django shell or admin action
- [ ] Task executes in Celery worker (not main process)
- [ ] Task logs start and completion with subject_id
- [ ] Task accepts parameters: subject_id (required), trigger type (optional)
- [ ] Worker can process multiple subjects in parallel (different subject_ids)
- [ ] Task appears in Celery Flower monitoring dashboard

**Priority:** P1

**Technical Notes:**
- Use Celery shared_task decorator for Django integration
- Configure worker concurrency in docker-compose (default: 4)
- Redis as broker URL configured in settings

---

### US-2: Firecrawl URL Scraping
**As a** pipeline
**I want to** scrape source URLs using Firecrawl API to obtain structured raw content
**So that** I have clean data for relevance analysis and synthesis

**Acceptance Criteria:**
- [ ] Integration with Firecrawl API using official Python client
- [ ] API key loaded from environment variable `FIRECRAWL_API_KEY`
- [ ] Scrape request includes URL and returns Markdown content
- [ ] Handle Firecrawl rate limits with exponential backoff
- [ ] Store raw scraped content temporarily (Redis or database field)
- [ ] Log scraping success/failure with URL and subject_id
- [ ] Handle timeout errors (Firecrawl API timeout: 30s)
- [ ] Return structured data: {url, content_markdown, scraped_at}

**Priority:** P1

**Technical Notes:**
- Use Firecrawl Python SDK: `pip install firecrawl`
- Implement retry logic for API failures (3 attempts)
- Cache successful scrapes for 1 hour to reduce API costs

---

### US-3: Vector Embedding Generation and Storage
**As a** pipeline
**I want to** transform synthesized report into vector embedding and store in pgvector
**So that** reports are searchable and usable for recommendation engine

**Acceptance Criteria:**
- [ ] Use embedding model (e.g., OpenAI text-embedding-3-small or Google Gemini)
- [ ] Generate embedding from report's full text content
- [ ] Store embedding in PostgreSQL using pgvector extension
- [ ] Embedding column type: vector(1536) or appropriate dimension
- [ ] Create pgvector index for efficient similarity search (HNSW or IVFFlat)
- [ ] Link embedding to Report record via foreign key
- [ ] Log embedding generation time and model used
- [ ] Handle embedding API failures with retry logic

**Priority:** P2

**Technical Notes:**
- Use Google AI Studio API (gemini-2.5-flash-001 for embeddings per tech doc)
- Ensure pgvector extension enabled: `CREATE EXTENSION IF NOT EXISTS vector`
- Index creation: `CREATE INDEX ON reports USING hnsw (embedding vector_cosine_ops)`

---

### US-4: Langgraph Workflow Orchestration
**As a** pipeline
**I want to** orchestrate the agent workflow using Langgraph with conditional flow
**So that** processing follows intelligent decision paths based on agent outputs

**Acceptance Criteria:**
- [ ] Langgraph StatefulGraph defined with 5 agent nodes
- [ ] Workflow starts with Collection Agent
- [ ] Relevance Agent conditionally routes: relevant → Synthesis, not relevant → END
- [ ] Synthesis Agent generates report and passes to Verification Agent
- [ ] Verification Agent conditionally routes: pass → Indexation, fail → Synthesis (max 2 loops)
- [ ] Indexation Agent stores report and embedding, then END
- [ ] Workflow state persisted in memory during execution
- [ ] Complete workflow executes end-to-end in < 5 minutes
- [ ] Workflow failures logged with state snapshot for debugging

**Priority:** P2

**Technical Notes:**
- Use Langgraph `StateGraph` class
- Define state schema with TypedDict (current_stage, raw_content, report, etc.)
- Implement conditional edges for routing logic
- Set max_iterations=10 to prevent infinite loops

---

### US-5: Structured Report Synthesis
**As a** Synthesis Agent
**I want to** generate report following strict structured format using LLM
**So that** all reports are consistent and include required sections

**Acceptance Criteria:**
- [ ] LLM prompt template enforces structure: Title, Introduction, Key Points (3-5), Sources
- [ ] Report format is Markdown
- [ ] Key Points section uses bullet list
- [ ] Sources section includes clickable URLs
- [ ] Report length: 300-500 words
- [ ] LLM model: Google Gemini 2.5 Flash (cost-effective for routine synthesis)
- [ ] Prompt includes source URL and raw content context
- [ ] Generated report stored in Report model
- [ ] Report includes metadata: subject_id, generated_at, word_count

**Priority:** P2

**Technical Notes:**
- Use Google AI Studio API with structured prompt
- Implement few-shot examples in prompt for consistency
- Temperature: 0.3 for consistent output
- Max output tokens: 1024

---

### US-6: Redis Distributed Locking
**As a** system
**I want to** prevent simultaneous processing of same subject by multiple workers using Redis lock
**So that** duplicate reports are not generated and resources are not wasted

**Acceptance Criteria:**
- [ ] Redis lock acquired before starting pipeline for subject
- [ ] Lock key format: `pipeline_lock:{subject_id}`
- [ ] Lock timeout: 10 minutes (exceeds max pipeline duration)
- [ ] If lock is held, worker exits gracefully with log message
- [ ] Lock automatically released on task completion (success or failure)
- [ ] Use context manager pattern to ensure lock release
- [ ] Lock acquisition failure logged with subject_id and timestamp

**Priority:** P3

**Technical Notes:**
- Use Django cache framework with Redis backend
- Implementation: `with cache.lock(f"pipeline_lock:{subject_id}", timeout=600)`
- Fallback: If Redis unavailable, log warning and proceed (degraded mode)

---

### US-7: Verification Agent with Feedback Loop
**As a** Verification Agent
**I want to** evaluate report quality and return to Synthesis Agent if issues detected
**So that** only high-quality reports are published to users

**Acceptance Criteria:**
- [ ] Verification prompt checks: coherence, factual accuracy, completeness, hallucination detection
- [ ] LLM model: Google Gemini 2.5 Pro (higher quality for verification)
- [ ] Verification returns: PASS or FAIL with feedback message
- [ ] On FAIL: feedback message returned to Synthesis Agent with correction instructions
- [ ] Synthesis Agent regenerates report incorporating feedback
- [ ] Maximum 2 verification loops before accepting report (prevent infinite loop)
- [ ] After 2 failures, report marked as "needs_manual_review"
- [ ] Verification decision logged with reasoning

**Priority:** P3

**Technical Notes:**
- Langgraph conditional edge: `"verify": {"pass": "indexation", "fail": "synthesis"}`
- Track loop count in workflow state
- Implement manual review queue in Django Admin

---

### US-8: Celery Retry Logic on Failure
**As a** system
**I want to** automatically retry pipeline task on API failures (LLM or Firecrawl)
**So that** transient errors do not result in missing reports

**Acceptance Criteria:**
- [ ] Celery task configured with retry decorator
- [ ] Max retries: 3 attempts
- [ ] Retry delay: exponential backoff (2^retry_count minutes)
- [ ] Retries triggered on: API timeout, rate limit, connection error
- [ ] Do NOT retry on: invalid API key, subject not found, validation errors
- [ ] Log each retry attempt with error message
- [ ] After 3 failures, task marked as failed and alert sent to monitoring
- [ ] Failed tasks visible in Django Admin for manual investigation

**Priority:** P3

**Technical Notes:**
- Use `@task(bind=True, max_retries=3, default_retry_delay=120)`
- Implement exponential backoff: `self.retry(countdown=2 ** self.request.retries * 60)`
- Use Celery exception handling for transient vs. permanent errors

## Non-Functional Requirements

### Scalability
- **RNF-SCAL-001:** System must support parallel execution of multiple pipelines (different subjects) by distinct Celery workers
- Worker pool sized to handle peak load (e.g., 10 subjects simultaneously)
- Horizontal scaling: Add more worker containers as needed

### Processing Time
- **RNF-INT-001:** Complete pipeline execution (collection to indexation) must not exceed **5 minutes** per subject
- Performance budget breakdown:
  - Collection (Firecrawl): 60s
  - Relevance: 10s
  - Synthesis: 60s
  - Verification: 30s
  - Indexation: 10s
  - Buffer: 140s
- Monitoring alerts if pipeline exceeds 5 minutes

### Data Consistency
- **RNF-CONS-001:** Distributed locking must guarantee single-processing of any subject at given time
- Redis lock prevents race conditions
- Atomic database operations for report creation

### Operational Excellence
- **RNF-OPE-003:** All pipeline stages must log to centralized monitoring system
- Log levels: INFO (start/end stages), WARN (retries), ERROR (failures)
- Logs include: timestamp, subject_id, stage name, duration, status
- Integration with structured logging (JSON format)
- Logs queryable for debugging and performance analysis

## Technical Constraints

### Technology Stack
- **Backend Framework:** Python 3.11+ with Django 3.2+
- **Orchestration:** Langgraph 0.2+ for stateful agent graphs
- **LLM Provider:** Google AI Studio (Gemini 2.5 Flash for synthesis, Gemini 2.5 Pro for verification)
- **Web Scraping:** Firecrawl API (official Python SDK)
- **Task Queue:** Celery 5.3+ with Redis broker
- **Vector Database:** PostgreSQL 15+ with pgvector extension
- **Embedding Model:** Google Gemini or OpenAI text-embedding-3-small

### Integration Requirements
- **Internal Dependencies:**
  - Subscription Management (Bloc 2) triggers bootstrap tasks
  - Report Consultation (Bloc 4) displays generated reports
  - FinOps Tracking (Bloc 6) captures LLM costs
- **External Dependencies:**
  - Firecrawl API with valid API key
  - Google AI Studio API with valid API key
  - Redis for Celery broker and distributed locking
  - PostgreSQL with pgvector extension enabled

### Infrastructure
- Docker Compose services: `worker`, `scheduler`, `redis`, `db`
- Environment variables: `FIRECRAWL_API_KEY`, `GOOGLE_API_KEY`, `REDIS_URL`, `DATABASE_URL`
- Celery Beat for scheduled recurring tasks (daily monitoring)
- Celery Flower for monitoring (optional, development only)

## Dependencies

### Internal Dependencies
- **Bloc 2 (Subscription Management):** Provides bootstrap trigger and subject definitions
- **Bloc 4 (Report Consultation):** Consumes generated reports
- **Bloc 6 (FinOps):** Monitors LLM API costs

### External Dependencies
- **Firecrawl API:** Web scraping service (paid API, rate limits apply)
- **Google AI Studio:** LLM API for synthesis and verification
- **Redis:** Task broker and distributed locking
- **PostgreSQL + pgvector:** Database and vector storage

### Blockers
- Firecrawl API key must be provisioned before testing
- Google AI Studio API key and project setup required
- pgvector extension must be installed in PostgreSQL database
- Subscription management must define subjects with URLs

## Success Metrics

### Key Performance Indicators (KPIs)
- **Pipeline Success Rate:** Target 95% of tasks complete successfully without manual intervention
- **Average Pipeline Duration:** Target < 3 minutes (well under 5-minute requirement)
- **Content Quality Score:** Target 90% of reports pass verification on first attempt

### Operational Metrics
- Celery task queue depth (should remain < 10)
- Worker utilization (target 60-80%)
- API failure rate (Firecrawl, LLM) - target < 5%
- Retry rate - target < 10% of tasks require retries

### Cost Metrics
- LLM API costs per report (tracked by Bloc 6)
- Firecrawl API costs per subject
- Target: < $0.10 per report generated

## Testing Strategy

### Test Coverage
- **Unit Tests:**
  - Individual agent logic (Collection, Relevance, Synthesis, Verification, Indexation)
  - Langgraph state transitions and conditional routing
  - Redis lock acquisition and release
  - Celery task configuration and retry logic
  - Report format validation

- **Integration Tests:**
  - End-to-end Langgraph workflow with mocked LLM responses
  - Firecrawl API integration (use test URLs)
  - Vector embedding generation and storage in pgvector
  - Celery task execution in worker
  - Distributed locking behavior with multiple workers

- **End-to-End Tests:**
  - Complete pipeline: trigger → scrape → synthesize → verify → index → report visible
  - Bootstrap task triggered by subscription
  - Scheduled task execution via Celery Beat
  - Failure scenarios with retry behavior

### Performance Testing
- Load test with 20 concurrent subjects
- Measure pipeline duration under load
- Verify distributed locking prevents race conditions
- Test Redis lock behavior under high contention

### User Acceptance Testing
- Admin triggers manual pipeline execution for test subject
- Verify generated report quality and format
- Check report appears in user dashboard (Bloc 4)
- Review Celery logs for completeness

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Celery worker configuration and base task
- Firecrawl API integration and scraping
- Basic report model and storage
- Manual task triggering

### Phase 2: Agent Orchestration (Week 2)
- Langgraph workflow definition
- Synthesis Agent with structured output
- Vector embedding generation and pgvector storage
- Redis distributed locking

### Phase 3: Quality & Resilience (Week 3)
- Verification Agent with feedback loop
- Celery retry logic for failures
- Comprehensive logging and monitoring
- Performance optimization

## Rollout Strategy

- Deploy worker service initially with manual triggering only
- Enable bootstrap trigger after testing Phase 1
- Enable Celery Beat scheduled tasks after Phase 2 validation
- Monitor costs and performance for first week before full rollout

## Risk Mitigation

- **API Rate Limits:** Implement exponential backoff and caching
- **Cost Overruns:** Set budget alerts in Google AI Studio and Firecrawl dashboards
- **Quality Issues:** Manual review queue for reports failing verification 2x
- **Performance Degradation:** Auto-scaling worker containers based on queue depth

## Documentation Requirements
- [ ] Langgraph workflow diagram (Mermaid or Graphviz)
- [ ] Developer guide for adding new agents
- [ ] Runbook for troubleshooting failed pipeline tasks
- [ ] API integration documentation (Firecrawl, Google AI Studio)

## Timeline
- **Phase 1:** 1 week (Foundation)
- **Phase 2:** 1 week (Orchestration)
- **Phase 3:** 1 week (Quality & Resilience)
- **Total:** 3 weeks

## Stakeholders
- **Product Owner:** Defines report quality standards
- **Tech Lead:** Reviews Langgraph architecture and agent design
- **Backend Team:** Implements pipeline and Celery tasks
- **DevOps:** Configures worker infrastructure and monitoring
- **Data Science:** Optimizes LLM prompts and embedding strategy
