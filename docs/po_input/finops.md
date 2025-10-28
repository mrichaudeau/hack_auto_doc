# FinOps Cost Tracking and Reporting

## Overview / Context

This feature provides comprehensive cost monitoring and analysis for LLM API usage within the AI pipeline. It enables administrators and finance teams to track operational expenses, identify cost optimization opportunities, and prevent budget overruns. Cost transparency is critical for sustainable operation of AI-powered systems.

**Target Users:**
- Administrators monitoring operational costs
- Finance/FinOps teams analyzing budget and spend
- DevOps teams optimizing resource utilization
- Product owners making ROI decisions

**Strategic Importance:**
- Prevents unexpected cost overruns from LLM API usage
- Enables data-driven optimization of AI pipeline
- Supports budget planning and forecasting
- Demonstrates operational maturity and financial responsibility

## Functional Requirements

### Cost Capture Mechanism (Callback Handler)

Cost tracking is integrated directly into the AI Pipeline execution.

**Primary Tool:**
- **Custom Callback Handler** for Langgraph
- Intercepts LLM lifecycle events during pipeline execution

**Event Triggering:**
- Handler intercepts `on_llm_end` event after each LLM API call
- Captures data from Synthesis Agent, Verification Agent, and any other LLM-powered agents

**Data Captured:**
- **Model Name:** e.g., "gemini-2.5-flash-001", "gemini-2.5-pro-001"
- **Input Tokens:** Number of tokens in prompt (`prompt_tokens`)
- **Output Tokens:** Number of tokens in completion (`completion_tokens`)
- **Timestamp:** Exact time of API call
- **Subject Context:** Link to monitoring subject that triggered the pipeline

### Cost Logging Model (LLMCostLog)

All captured data stored in dedicated database model: `LLMCostLog`.

**Cost Calculation:**
- System applies unit rates (stored in environment variables or config table) to token counts
- Calculates real cost in USD (or EUR) per API call
- Formula: `cost = (input_tokens * input_rate + output_tokens * output_rate)`

**Traceability:**
- Each log entry linked to **Monitoring Subject** and **exact timestamp**
- Enables analysis by business context (which subjects are most expensive)
- Supports audit trail and cost allocation

### Dashboard and Reporting Interface

**Django Admin** interface used as FinOps dashboard for rapid development and security.

**Custom Views:**
- Filter costs by time period (day, week, month)
- Filter costs by monitoring subject (identify expensive topics)
- Display total cumulative cost by LLM model
- Export cost data to CSV or JSON for external analysis

**Aggregation:**
- Daily cost summaries
- Cost per subject
- Cost per model
- Cost trends over time

## User Stories

### US-1: Create Custom Callback Handler for Langgraph
**As a** developer
**I want to** create custom callback handler that intercepts `on_llm_end` events in Langgraph
**So that** I can capture token usage and cost data for every LLM API call

**Acceptance Criteria:**
- [ ] Custom callback class inherits from Langgraph BaseCallbackHandler
- [ ] Implements `on_llm_end(response, **kwargs)` method
- [ ] Handler registered in Langgraph pipeline configuration
- [ ] Handler called automatically after each LLM invocation
- [ ] Handler extracts: model_name, prompt_tokens, completion_tokens from response
- [ ] Handler has access to pipeline context (subject_id)
- [ ] Logs handler invocation for debugging
- [ ] Handler errors logged but do not crash pipeline

**Priority:** P1

**Technical Notes:**
- Langgraph callback documentation: https://python.langchain.com/docs/modules/callbacks/
- Pass subject_id via pipeline state or metadata
- Use try-except to ensure callback failures don't break pipeline

---

### US-2: Log Token Usage in LLMCostLog Model
**As a** system
**I want to** record token usage details in database after each LLM API call
**So that** I have permanent record for cost analysis and auditing

**Acceptance Criteria:**
- [ ] Django model `LLMCostLog` with fields: id, subject (FK), model_name, tokens_input, tokens_output, timestamp, cost_usd
- [ ] Callback handler creates LLMCostLog record on each `on_llm_end` event
- [ ] All fields populated correctly from callback data
- [ ] Database transaction handles concurrent writes (pipeline parallelism)
- [ ] Model includes indexes on: timestamp, subject_id for query performance
- [ ] Model visible in Django Admin for inspection
- [ ] Historical records never deleted (append-only log)

**Priority:** P1

**Technical Notes:**
- Use Django ORM for record creation
- Foreign key to Subject model (from Bloc 2)
- Add database indexes in migration
- Consider partitioning table by timestamp for large-scale deployments

---

### US-3: Calculate Monetary Cost in USD
**As a** system
**I want to** calculate monetary cost of each LLM API call using configured unit rates
**So that** cost reporting shows real financial impact

**Acceptance Criteria:**
- [ ] Unit rates stored in environment variables or config table: INPUT_TOKEN_RATE_USD, OUTPUT_TOKEN_RATE_USD
- [ ] Rates configurable per model (Gemini Flash vs. Pro have different rates)
- [ ] Calculation formula: `cost = (tokens_input * input_rate) + (tokens_output * output_rate)`
- [ ] Cost stored in `cost_usd` field as Decimal (precision: 2 decimal places minimum)
- [ ] Calculation occurs in callback handler before saving to database
- [ ] Default rates provided for common models (Gemini 2.5 Flash, Gemini 2.5 Pro)
- [ ] Cost calculation logged for audit (input count, output count, rate, total)

**Priority:** P2

**Technical Notes:**
- Use Python Decimal for financial calculations (avoid float precision issues)
- Example rates (verify with Google AI pricing):
  - Gemini 2.5 Flash: Input $0.000075/1K tokens, Output $0.0003/1K tokens
  - Gemini 2.5 Pro: Input $0.00125/1K tokens, Output $0.005/1K tokens
- Store rates in Django settings or database configuration table

---

### US-4: Aggregated Cost View in Django Admin
**As an** administrator
**I want to** view aggregated cost data in Django Admin dashboard
**So that** I can quickly understand spending patterns and identify cost drivers

**Acceptance Criteria:**
- [ ] Custom Django Admin view for LLMCostLog with aggregations
- [ ] Display total cost grouped by: date (daily), subject, model
- [ ] List view shows: subject name, model name, total tokens, total cost, date
- [ ] Sortable by cost (highest to lowest)
- [ ] Summary row showing grand total cost
- [ ] Default view: Last 30 days of data
- [ ] Pagination for large datasets
- [ ] Export button visible (see US-6)

**Priority:** P2

**Technical Notes:**
- Use Django Admin custom ModelAdmin with aggregation in queryset
- Annotate with Sum() for total_cost, Sum() for total_tokens
- Use select_related() to optimize queries
- Custom template for summary row if needed

---

### US-5: Filter Costs by Date Range and Subject
**As an** administrator
**I want to** filter cost data by date range and monitoring subject
**So that** I can analyze specific time periods or identify expensive subjects

**Acceptance Criteria:**
- [ ] Django Admin list filters for: date range (start/end), subject, model
- [ ] Date filter presets: Today, Last 7 days, Last 30 days, This month, Custom range
- [ ] Subject filter dropdown populated with all subjects
- [ ] Model filter dropdown shows all models that have logged costs
- [ ] Filters applied dynamically without page reload (use Django Admin filters)
- [ ] Filtered results show aggregate totals for selected subset
- [ ] URL parameters reflect filter state for bookmarking
- [ ] Performance optimized for large datasets (indexed queries)

**Priority:** P3

**Technical Notes:**
- Use Django Admin list_filter with custom filters
- DateRangeFilter for date filtering
- SimpleListFilter for subject and model
- Add database indexes on filter fields

---

### US-6: Export Cost Data to CSV
**As an** administrator
**I want to** export cost data to CSV format
**So that** I can perform external analysis in Excel or BI tools

**Acceptance Criteria:**
- [ ] "Export to CSV" action button in Django Admin list view
- [ ] CSV includes columns: date, subject_name, model_name, tokens_input, tokens_output, cost_usd
- [ ] Export respects current filters (date range, subject, model)
- [ ] CSV filename includes timestamp: `llm_costs_YYYYMMDD_HHMMSS.csv`
- [ ] Large exports (>10K rows) handled efficiently (streaming response)
- [ ] CSV properly formatted with headers
- [ ] Download initiated automatically (Content-Disposition: attachment)

**Priority:** P3

**Technical Notes:**
- Use Django Admin custom action: `export_as_csv`
- Use Python csv module or pandas for generation
- Streaming response for large datasets: `StreamingHttpResponse`
- Test with 100K+ records for performance

## Non-Functional Requirements

### Precision
- **RNF-PREC-002:** Token measurement must be 100% accurate based on LLM API response
- No estimation or approximation acceptable for financial data
- Rely on authoritative data from API response

### Performance
- **RNF-PERF-005:** Cost logging overhead must not increase pipeline execution time by more than **50ms**
- Callback execution must be lightweight
- Database writes should not block pipeline progression
- Consider async logging if synchronous writes cause latency

### Security and Audit
- **RNF-AUD-001:** FinOps dashboard accessible only to users with Administrator or FinOps role
- Role-based access control enforced at Django Admin level
- Audit log for dashboard access and data exports
- Cost data considered sensitive financial information

## Technical Constraints

### Technology Stack
- **Backend Framework:** Django 3.2+ with Django Admin
- **AI Orchestration:** Langgraph with custom callback handlers
- **Database:** PostgreSQL 15 for cost log storage
- **Data Processing:** Pandas for CSV export (optional)

### Integration Requirements
- **Internal Dependencies:**
  - AI Pipeline (Bloc 3) for callback integration
  - Subscription Management (Bloc 2) for subject linkage
- **External Dependencies:**
  - Google AI Studio API (provides token counts)
  - PostgreSQL for data storage

### Infrastructure
- Django Admin interface with custom views
- Database migrations for LLMCostLog model
- Environment variables for token unit rates
- Role-based access control configuration

## Dependencies

### Internal Dependencies
- **Bloc 3 (AI Pipeline):** Callback handler integrated into Langgraph workflow
- **Bloc 2 (Subscription Management):** Subject model used as foreign key

### External Dependencies
- **Google AI Studio API:** Source of token count data
- **PostgreSQL:** Storage for cost logs

### Blockers
- Cannot implement until AI Pipeline (Bloc 3) Langgraph workflow is functional
- Requires LLM API integration to return token counts
- Django Admin must be configured with admin users

## Success Metrics

### Key Performance Indicators (KPIs)
- **Cost Tracking Coverage:** 100% of LLM API calls logged (no missed calls)
- **Cost Visibility:** 100% of administrators access dashboard at least weekly
- **Cost Optimization:** 20% reduction in cost per report within 3 months (via optimization)

### Operational Metrics
- Average cost per report generated
- Cost per monitoring subject (identify expensive topics)
- Cost trend over time (increasing, stable, decreasing)
- Model usage distribution (Flash vs. Pro)

### Financial Metrics
- Monthly LLM API spend vs. budget
- Cost per active user (total spend / active users)
- ROI: Value delivered vs. operational cost

## Testing Strategy

### Test Coverage
- **Unit Tests:**
  - Callback handler token extraction logic
  - Cost calculation formula
  - LLMCostLog model validation
  - CSV export formatting

- **Integration Tests:**
  - End-to-end: LLM call → callback → database log
  - Callback handler registered in Langgraph
  - Django Admin view with aggregations
  - Filter functionality
  - CSV export with filters

- **End-to-End Tests:**
  - Pipeline execution → cost logged → visible in Admin
  - Admin user logs in → views dashboard → filters data → exports CSV
  - Non-admin user cannot access FinOps dashboard

### Performance Testing
- Callback overhead measurement (should be < 50ms)
- Database write performance under high concurrency
- CSV export with 100K+ records
- Admin dashboard load time with large datasets

### User Acceptance Testing
- Admin users test dashboard navigation and filtering
- Finance team validates cost calculations against API invoices
- Export functionality tested with real analysis workflows

## Implementation Phases

### Phase 1: Foundation (Week 1)
- LLMCostLog model and migrations
- Custom callback handler implementation
- Basic token logging

### Phase 2: Cost Calculation (2 days)
- Unit rate configuration
- Cost calculation logic
- Database storage of costs

### Phase 3: Dashboard and Reporting (3 days)
- Django Admin custom views
- Aggregation and filtering
- CSV export functionality
- Access control configuration

## Rollout Strategy

- Deploy callback handler in pilot phase with single subject
- Validate cost calculations against Google AI Studio usage reports
- Enable dashboard for admin users
- Monitor callback performance overhead
- Full rollout after validation

## Risk Mitigation

- **Callback Failures:** Ensure failures don't crash pipeline (try-except wrapping)
- **Cost Accuracy:** Regular reconciliation with Google AI Studio invoices
- **Performance Impact:** Async logging if overhead exceeds 50ms
- **Data Growth:** Implement data archival strategy for old logs (>1 year)

## Documentation Requirements
- [ ] Developer guide for callback handler integration
- [ ] Admin user guide for FinOps dashboard usage
- [ ] Cost calculation methodology documentation
- [ ] API pricing reference and rate updates

## Timeline
- **Phase 1:** 1 week (Foundation)
- **Phase 2:** 2 days (Cost Calculation)
- **Phase 3:** 3 days (Dashboard)
- **Total:** ~2 weeks

## Stakeholders
- **Product Owner:** Defines cost monitoring requirements
- **Tech Lead:** Reviews callback architecture and performance
- **Backend Team:** Implements callback handler and Django Admin views
- **Finance/FinOps:** Uses dashboard for cost analysis and budgeting
- **DevOps:** Monitors cost trends and optimization opportunities
