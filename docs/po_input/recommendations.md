# Semantic Recommendation Engine

## Overview / Context

This feature provides intelligent subject discovery capabilities using semantic similarity. Rather than recommending individual reports, it suggests new **monitoring subjects** relevant to the user's interests that they haven't yet subscribed to. This increases engagement depth and helps users expand their technology watch coverage.

**Target Users:**
- End users seeking to discover relevant technology topics
- Platform (automated personalization)

**Strategic Importance:**
- Increases user engagement by expanding subscription base
- Demonstrates AI/ML sophistication through semantic understanding
- Drives content consumption and platform stickiness
- Differentiator vs. simple rule-based recommendations

## Functional Requirements

### User Interest Profiling

The system creates a semantic profile for each user based on their subscription behavior.

**Profile Vector Calculation:**
- User's interest profile = **arithmetic mean** of all vector embeddings from reports belonging to subscribed subjects
- This single vector represents user's semantic position in knowledge space
- Stored in User model for efficient retrieval

**Asynchronous Updates:**
- Profile vector recalculated when:
  - User subscribes to new subject
  - User unsubscribes from subject
  - New report generated for subscribed subject
- Update triggered asynchronously (Celery task) to avoid blocking API

### Semantic Recommendation Mechanism

**Vector Search:**
- Recommendation endpoint uses user's **profile vector** for **cosine similarity** search (Nearest Neighbor)
- Search performed on pgvector index in PostgreSQL

**Search Base:**
- Each monitoring subject has representative vector (mean of all its reports' embeddings)
- Search compares user profile vector against all subject representative vectors

**Intelligent Filtering:**
Results must exclude:
1. Subjects user is already subscribed to
2. Archived or inactive subjects

### Display and Interaction

Recommendation page displays paginated list of suggested subjects, ranked by similarity score (highest relevance first).

**Interaction:**
- Each subject card shows: name, description, similarity score (optional), subscriber count
- Simple "Subscribe" button for immediate action
- Links to Subscription Management (Bloc 2) API

## User Stories

### US-1: Calculate and Store User Profile Vector
**As a** system
**I want to** calculate user's interest profile vector from embeddings of subscribed subjects' reports
**So that** I can perform semantic similarity search for recommendations

**Acceptance Criteria:**
- [ ] User model has `profile_embedding` field (vector type, dimension matching report embeddings)
- [ ] Calculation function computes mean of all report embeddings for user's subscribed subjects
- [ ] If user has no subscriptions, profile_embedding is NULL or zero vector
- [ ] Profile vector stored in database with timestamp of last update
- [ ] Calculation handles edge cases: single subscription, newly created reports
- [ ] Profile update triggered by signal/webhook on subscription change
- [ ] Celery task for async profile calculation: `update_user_profile(user_id)`

**Priority:** P1

**Technical Notes:**
- Use NumPy for efficient vector averaging: `np.mean(embeddings, axis=0)`
- Store as pgvector type for consistent querying
- Index profile_embedding column for performance

---

### US-2: Calculate Subject Representative Vector
**As a** system
**I want to** calculate representative embedding for each monitoring subject
**So that** I can compare subjects against user profiles for recommendations

**Acceptance Criteria:**
- [ ] Subject model has `embedding_mean` field (vector type)
- [ ] Calculation function computes mean of all report embeddings for subject
- [ ] Representative vector updated after each new report generation
- [ ] Update can be async or synchronous depending on performance needs
- [ ] Subjects with no reports have NULL embedding (excluded from recommendations)
- [ ] Calculation logged with subject_id and timestamp

**Priority:** P1

**Technical Notes:**
- Trigger update in Indexation Agent (Bloc 3) after storing report embedding
- Use same dimensionality as report embeddings
- Consider incremental update formula for performance: `new_mean = (old_mean * n + new_vector) / (n + 1)`

---

### US-3: Return Paginated Subjects Ranked by Similarity
**As a** user
**I want to** API to return monitoring subjects ranked by semantic relevance to my interests
**So that** I can discover new technology topics aligned with my current subscriptions

**Acceptance Criteria:**
- [ ] Endpoint `/api/recommendations/` returns list of recommended subjects
- [ ] Requires authentication (JWT token)
- [ ] Uses pgvector cosine similarity operator: `<=>` or `<->`
- [ ] Results sorted by similarity score (highest first)
- [ ] Paginated: 10 subjects per page
- [ ] Each result includes: subject_id, name, description, similarity_score (optional)
- [ ] Response time < 500ms (P95)
- [ ] Empty list if user profile_embedding is NULL

**Priority:** P1

**Technical Notes:**
- SQL query: `SELECT *, profile_embedding <-> embedding_mean AS distance FROM subjects ORDER BY distance LIMIT 10`
- Use DRF pagination for consistent API design
- Consider caching recommendations per user for 1 hour

---

### US-4: Exclude Subscribed Subjects from Recommendations
**As a** system
**I want to** exclude subjects user is already subscribed to from recommendation results
**So that** recommendations are actionable and don't show redundant suggestions

**Acceptance Criteria:**
- [ ] Recommendation query filters out subjects in user's subscription list
- [ ] SQL uses LEFT JOIN or NOT IN clause for exclusion
- [ ] Exclusion logic tested with various subscription combinations
- [ ] Performance optimized with proper indexing
- [ ] Archived subjects also excluded from results
- [ ] Recommendation count adjusts dynamically as user subscribes

**Priority:** P2

**Technical Notes:**
- Efficient query: `WHERE subject_id NOT IN (SELECT subject_id FROM subscriptions WHERE user_id = ?)`
- Alternative: Use Django ORM exclude()
- Index subscription table on user_id and subject_id

---

### US-5: Subscribe Directly from Recommendations
**As a** user
**I want to** subscribe to recommended subject directly from recommendations page
**So that** I can act on suggestions immediately without navigation overhead

**Acceptance Criteria:**
- [ ] Each recommendation card has "Subscribe" button
- [ ] Button calls existing subscription API: `POST /api/subscriptions/`
- [ ] On success, button changes to "Subscribed" or is disabled
- [ ] Subject immediately removed from recommendations list (frontend optimistic update)
- [ ] Error handling displays message if subscription fails
- [ ] Subscription triggers bootstrap task as per Bloc 2 behavior

**Priority:** P2

**Technical Notes:**
- Reuse existing subscription endpoint from Bloc 2
- Frontend: Optimistic UI update, rollback on error
- Trigger profile recalculation after subscription (async)

---

### US-6: Async Profile Update Triggers
**As a** system
**I want to** trigger async profile recalculation when user's subscriptions or reports change
**So that** recommendations stay fresh and relevant without blocking user actions

**Acceptance Criteria:**
- [ ] Django signal on Subscription create/delete triggers profile update
- [ ] Signal on Report creation triggers profile update for subscribed users
- [ ] Celery task `update_user_profile(user_id)` queued asynchronously
- [ ] Task executes in background worker, does not block API response
- [ ] Failed profile updates logged but do not affect user operations
- [ ] Rate limiting: Max one profile update per user per 5 minutes (debouncing)

**Priority:** P3

**Technical Notes:**
- Use Django signals: `post_save` on Subscription, `post_save` on Report
- Debouncing with Redis: Check last update timestamp before queuing
- Task should handle concurrent execution gracefully

---

### US-7: ANN Index Configuration and Optimization
**As a** developer
**I want to** configure Approximate Nearest Neighbor (ANN) index for profile embeddings
**So that** similarity searches scale efficiently as user and subject base grows

**Acceptance Criteria:**
- [ ] pgvector HNSW or IVFFlat index created on Subject.embedding_mean
- [ ] Index parameters tuned for dataset size and query patterns
- [ ] Query execution plan uses index (verify with EXPLAIN)
- [ ] Recommendation query time < 500ms even with 10,000+ subjects
- [ ] Index maintenance scheduled (periodic VACUUM and REINDEX)
- [ ] Documentation includes index choice rationale

**Priority:** P3

**Technical Notes:**
- HNSW recommended for high recall: `CREATE INDEX ON subjects USING hnsw (embedding_mean vector_cosine_ops)`
- IVFFlat for larger datasets: `CREATE INDEX ON subjects USING ivfflat (embedding_mean vector_cosine_ops) WITH (lists = 100)`
- Test with realistic data volumes before choosing
- Monitor index size and query performance

## Non-Functional Requirements

### Performance
- **RNF-PERF-004:** Recommendation query must not exceed **500ms** (including profile vector calculation if cached)
- Critical for user experience and real-time feel
- Optimization: ANN indexing, query optimization, caching

### Precision
- **RNF-PRECI-001:** Cosine similarity must be used as primary ranking metric
- Industry standard for semantic similarity
- Provides interpretable similarity scores (0-1 range)

### Scalability
- **RNF-SCAL-002:** Vector index must be optimized (HNSW or IVFFlat) for fast search with thousands of subjects
- Support dataset growth without linear performance degradation
- Horizontal scaling: Read replicas for recommendation queries

## Technical Constraints

### Technology Stack
- **Backend Framework:** Django 3.2+ with Django REST Framework
- **Vector Database:** PostgreSQL 15+ with pgvector extension
- **Vector Operations:** NumPy for Python-side calculations
- **Task Queue:** Celery for async profile updates
- **Caching:** Redis for query caching and debouncing

### Integration Requirements
- **Internal Dependencies:**
  - Authentication (Bloc 1) for user identification
  - Subscription Management (Bloc 2) for exclusion filtering and subscribe action
  - AI Pipeline (Bloc 3) for report embeddings source data
- **External Dependencies:**
  - PostgreSQL with pgvector extension
  - Redis for Celery broker and caching

### Infrastructure
- pgvector extension must be enabled in PostgreSQL
- Database migrations for profile_embedding and embedding_mean fields
- Celery worker capacity for profile update tasks
- Redis for task queue and caching layer

## Dependencies

### Internal Dependencies
- **Bloc 1 (Authentication):** Provides user identification
- **Bloc 2 (Subscription Management):** Provides subscription data and subscribe API
- **Bloc 3 (AI Pipeline):** Generates report embeddings used for profiling

### External Dependencies
- **PostgreSQL + pgvector:** Vector storage and similarity search
- **Redis:** Task queue and caching
- **NumPy:** Vector arithmetic operations

### Blockers
- Cannot calculate profiles until AI Pipeline (Bloc 3) generates report embeddings
- Subscription data from Bloc 2 required for exclusion filtering
- pgvector extension must be installed before testing

## Success Metrics

### Key Performance Indicators (KPIs)
- **Recommendation Adoption Rate:** Target 30% of users subscribe to at least one recommended subject per month
- **Recommendation Relevance:** Target 80% user satisfaction with recommendations (via survey)
- **Discovery Rate:** Target 50% of subscriptions come from recommendations (vs. catalog browsing)

### User Engagement Metrics
- Click-through rate on recommendations page: Target 40%
- Subscribe button click rate: Target 25% per page view
- Returning users to recommendations page: Target 60% within one week

### Technical Performance
- Recommendation API response time P95 < 500ms
- Profile update task completion time: Target < 30s
- Index query performance with 10,000+ subjects

## Testing Strategy

### Test Coverage
- **Unit Tests:**
  - Profile vector calculation logic
  - Subject representative vector calculation
  - Cosine similarity computation
  - Filtering logic (subscribed, archived)
  - Edge cases: no subscriptions, single subscription

- **Integration Tests:**
  - End-to-end recommendation flow with database
  - Async profile update triggering
  - Subscription exclusion filtering
  - pgvector similarity queries
  - Pagination

- **End-to-End Tests:**
  - User subscribes → profile updates → sees updated recommendations
  - User subscribes from recommendations → subject disappears from list
  - Recommendations change as user's subscriptions evolve

### Performance Testing
- Load test with 1,000 concurrent recommendation queries
- Test with datasets: 100, 1,000, 10,000 subjects
- Profile calculation performance with varying subscription counts
- Index performance comparison (HNSW vs. IVFFlat)

### User Acceptance Testing
- Users review recommendations and rate relevance
- A/B testing: cosine similarity vs. other metrics
- Monitor subscription conversion from recommendations

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Add profile_embedding and embedding_mean fields
- Implement profile calculation logic
- Basic recommendation API without optimization

### Phase 2: Optimization (3 days)
- pgvector ANN index creation
- Query performance optimization
- Async profile updates with Celery
- Caching layer

### Phase 3: Integration (2 days)
- Subscription exclusion filtering
- Direct subscribe from recommendations
- Frontend recommendations page
- Comprehensive testing

## Rollout Strategy

- Deploy with feature flag for gradual testing
- Start with small user segment to validate relevance
- A/B test: recommendations vs. no recommendations for subscription growth
- Monitor performance and adjust index parameters
- Full rollout after validation phase

## Risk Mitigation

- **Poor Recommendations:** Implement feedback mechanism to tune algorithm
- **Performance Issues:** Use caching aggressively, consider read replicas
- **Cold Start Problem:** Provide default recommendations for new users (popular subjects)
- **Computational Cost:** Batch profile updates, use incremental calculations

## Documentation Requirements
- [ ] API documentation for recommendation endpoint
- [ ] Developer guide for vector similarity and pgvector
- [ ] Admin guide for monitoring recommendation performance
- [ ] Algorithm explanation for stakeholders

## Timeline
- **Phase 1:** 1 week (Foundation)
- **Phase 2:** 3 days (Optimization)
- **Phase 3:** 2 days (Integration)
- **Total:** ~2 weeks

## Stakeholders
- **Product Owner:** Defines recommendation UX and success metrics
- **Tech Lead:** Reviews vector search architecture and performance
- **Backend Team:** Implements recommendation engine and profile calculation
- **Frontend Team:** Builds recommendations page UI
- **Data Science:** Tunes similarity algorithm and evaluation metrics
