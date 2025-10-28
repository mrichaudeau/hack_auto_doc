# User Story: Development Workflow Documentation

**Story ID:** US-12
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** new developer
**I want** clear setup instructions and common commands
**So that** I can onboard and start contributing quickly

## Description

This User Story establishes comprehensive documentation that guides developers through setting up and using the local development environment. Good documentation is critical for reducing onboarding time, preventing common mistakes, and serving as a reference for experienced developers who need to remember specific commands or troubleshooting steps.

The documentation must be practical and actionable, with step-by-step instructions that assume minimal prior knowledge of Docker, Django, or React. It should cover the complete developer journey: prerequisites, initial setup, common workflows (running tests, applying migrations, viewing logs), and troubleshooting common issues.

Visual aids like architecture diagrams and port mapping tables help developers quickly understand the system structure. A troubleshooting section addresses known issues with clear resolution steps, reducing support requests and unblocking developers independently.

Success means a new developer with no prior project knowledge can follow the documentation and have a fully functional local environment within 30 minutes, ready to start development work.

## Acceptance Criteria

### Functional Criteria
- [ ] README or setup guide includes all prerequisites (Git, Docker Desktop)
- [ ] Step-by-step instructions for first-time setup (clone, configure, build, start)
- [ ] Common commands documented: build, up, down, logs, exec, restart
- [ ] Troubleshooting section for known issues with resolution steps
- [ ] Architecture diagram showing service relationships and dependencies
- [ ] Port mapping table listing all services and their localhost ports
- [ ] Instructions for accessing each service (URLs, endpoints)
- [ ] Commands for running tests, linting, migrations, and admin tasks

### Technical Criteria
- [ ] Documentation located at `docs/setup/00_setup_local_docker.md`
- [ ] Markdown format for easy version control and editing
- [ ] Code blocks with syntax highlighting for commands
- [ ] Links to external resources (Docker installation, API key registration)
- [ ] Screenshots or diagrams where helpful (architecture, admin UI)
- [ ] Table of contents for easy navigation
- [ ] Versioned documentation (update when setup changes)

### UI/UX Criteria (if applicable)
- Documentation organized logically with clear section headings
- Commands formatted consistently (use code blocks)
- Warnings and important notes highlighted with callout boxes

### Performance Criteria
- [ ] Documentation complete and readable within 10 minutes
- [ ] New developer can complete setup following docs within 30 minutes

## Technical Details

### Components Affected
- `docs/setup/00_setup_local_docker.md` (new file)
- `README.md` (updated with link to setup guide)
- Architecture diagrams (new images)
- `.github/CONTRIBUTING.md` (optional, contribution guidelines)

### API Changes
- None (documentation only)

### Database Changes
- None

### External Integrations
- Links to external documentation (Docker, Django, React)
- Links to API key registration (Google AI, Firecrawl)

## Implementation Notes

### Suggested Approach

1. **Create comprehensive setup documentation at `docs/setup/00_setup_local_docker.md`:**

   **Table of Contents:**
   - Prerequisites
   - System Requirements
   - Installation Steps
   - Configuration
   - Starting the Environment
   - Accessing Services
   - Common Commands
   - Running Tests
   - Troubleshooting
   - Architecture Overview

2. **Prerequisites section:**
   ```markdown
   ## Prerequisites

   - **Git:** Version control for cloning repository
     - Download: https://git-scm.com/downloads
   - **Docker Desktop:** Version 4.25+ (Windows/Mac) or Docker Engine 24+ (Linux)
     - Windows/Mac: https://www.docker.com/products/docker-desktop
     - Linux: https://docs.docker.com/engine/install/
   - **API Keys:**
     - Google AI API Key: https://ai.google.dev/
     - Firecrawl API Key: https://firecrawl.dev/
   ```

3. **Step-by-step setup instructions:**
   ```markdown
   ## Installation Steps

   1. Clone the repository:
      ```bash
      git clone [REPO_URL]
      cd [REPO_NAME]
      ```

   2. Copy environment configuration files:
      ```bash
      cp env.backend.example .env.backend
      cp env.frontend.example .env.frontend
      ```

   3. Edit `.env.backend` and add your API keys:
      - `GOOGLE_AI_API_KEY=your-key-here`
      - `FIRECRAWL_API_KEY=your-key-here`

   4. Build Docker images:
      ```bash
      docker-compose build
      ```

   5. Start all services:
      ```bash
      docker-compose up -d
      ```

   6. Apply database migrations:
      ```bash
      docker-compose exec backend python manage.py migrate
      ```

   7. Create superuser account:
      ```bash
      docker-compose exec backend python manage.py createsuperuser
      ```

   8. Verify all services are running:
      ```bash
      docker-compose ps
      ```
   ```

4. **Port mapping and service access table:**
   ```markdown
   ## Service URLs

   | Service | URL | Description |
   |---------|-----|-------------|
   | Frontend | http://localhost:3000 | React SPA application |
   | Backend API | http://localhost:8000/api/ | Django REST API |
   | Django Admin | http://localhost:8000/admin/ | Admin interface & FinOps dashboard |
   | Database | localhost:5432 | PostgreSQL (internal only) |
   | Redis | localhost:6379 | Redis (internal only) |
   ```

5. **Common commands reference:**
   ```markdown
   ## Common Commands

   ### Service Management
   - Start all services: `docker-compose up -d`
   - Stop all services: `docker-compose down`
   - Restart a service: `docker-compose restart [service]`
   - View service status: `docker-compose ps`

   ### Logs
   - View all logs: `docker-compose logs`
   - View specific service: `docker-compose logs backend`
   - Follow logs in real-time: `docker-compose logs -f`
   - Last 100 lines: `docker-compose logs --tail=100`

   ### Database
   - Apply migrations: `docker-compose exec backend python manage.py migrate`
   - Create migration: `docker-compose exec backend python manage.py makemigrations`
   - Database shell: `docker-compose exec backend python manage.py dbshell`

   ### Testing
   - Run backend tests: `docker-compose exec backend pytest`
   - Run frontend tests: `docker-compose exec frontend npm test`

   ### Development
   - Django shell: `docker-compose exec backend python manage.py shell`
   - Backend bash: `docker-compose exec backend bash`
   - Frontend bash: `docker-compose exec frontend sh`
   ```

6. **Troubleshooting section:**
   ```markdown
   ## Troubleshooting

   ### Port Already in Use
   **Error:** "Bind for 0.0.0.0:8000 failed: port is already allocated"
   **Solution:** Another service is using port 8000. Stop it or change port mapping in docker-compose.yml

   ### Database Connection Refused
   **Error:** "OperationalError: could not connect to server"
   **Solution:** Ensure database service is healthy: `docker-compose ps db`

   ### Hot Reload Not Working
   **Issue:** Code changes not reflected in browser
   **Solution:** Ensure code is mounted as volume; check docker-compose.yml volume mounts

   ### API Key Errors
   **Error:** "GOOGLE_AI_API_KEY not found"
   **Solution:** Verify .env.backend file exists and contains API key
   ```

7. **Architecture diagram:**
   - Create diagram showing service relationships
   - Include arrows for data flow (Frontend → Backend → Database)
   - Show Celery worker/scheduler connections to Redis and database

### Technical Considerations

**Performance:**
- Documentation should load quickly in browser or code editor
- Avoid large image files that slow loading

**Security:**
- Never include actual API keys or secrets in documentation
- Clearly indicate which credentials are placeholders

**Scalability:**
- Documentation structure should scale as project grows
- Use separate files for different topics if needed

**Backward Compatibility:**
- Version documentation alongside code changes
- Note breaking changes prominently

### Known Challenges

**Challenge:** Documentation quickly becomes outdated
**Solution:** Review and update docs with each PR that changes setup process; include in Definition of Done

**Challenge:** Different platforms (Windows/Mac/Linux) have subtle differences
**Solution:** Note platform-specific issues in troubleshooting section

**Challenge:** Developers skip reading documentation
**Solution:** Make docs concise, scannable, with clear headings; link from README

## Dependencies

### Depends On
- All other User Stories in this feature (documents the complete setup)

### Blocks
- None (documentation is final step)

## Test Scenarios

### Happy Path
1. New developer with no project knowledge reads documentation
2. Follows prerequisites section and installs Docker Desktop
3. Clones repository following instructions
4. Copies and configures .env files as documented
5. Runs build command from documentation
6. Runs up command to start services
7. Applies migrations using documented command
8. Creates superuser using documented command
9. Accesses frontend at http://localhost:3000
10. Accesses Django Admin at http://localhost:8000/admin/
11. Complete setup takes < 30 minutes

### Alternative Paths
1. Developer encounters issue during setup
2. Checks troubleshooting section
3. Finds matching error with clear resolution steps
4. Applies fix and continues setup successfully

### Error Scenarios
1. **Missing prerequisite:** Developer does not have Docker installed
   - Expected: Prerequisites section clearly lists Docker requirement with download link
   - Developer installs Docker and continues

2. **Unclear command:** Developer unsure which command to run next
   - Expected: Step-by-step instructions clearly numbered with explanation
   - Developer follows sequential steps without confusion

3. **Port conflict:** Port 8000 already in use
   - Expected: Troubleshooting section addresses this issue
   - Developer follows resolution steps and resolves conflict

### Edge Cases
1. **Platform-specific issue:** Windows Docker Desktop requires WSL2
   - Expected: Documentation notes Windows-specific setup requirements
   - Developer enables WSL2 and continues

2. **Outdated documentation:** Setup process changed but docs not updated
   - Expected: Documentation versioned and updated with code changes
   - Developer reports outdated section for correction

## UI/UX Specifications

### Documentation Layout
- Clear hierarchy with heading levels (H1, H2, H3)
- Table of contents at top for easy navigation
- Code blocks with syntax highlighting
- Tables for structured information (ports, services)
- Callout boxes for warnings and important notes

### Architecture Diagram
- Visual representation of all 6 services
- Data flow arrows showing communication patterns
- Port numbers labeled on each service
- External integrations (APIs) clearly marked

## Security Considerations

- Never include actual API keys or credentials in documentation
- Clearly mark placeholder values in example commands
- Document security best practices (strong passwords, API key protection)
- Note that local development credentials should not be used in production

## Performance Requirements

- **Documentation Reading Time:** < 10 minutes to read complete guide
- **Setup Time:** < 30 minutes for new developer to complete setup
- **Command Reference Access:** < 30 seconds to find specific command

## Accessibility Requirements

- Markdown format accessible to screen readers
- Clear heading structure for navigation
- Alt text for images and diagrams

## Definition of Done

- [ ] Comprehensive setup guide created at `docs/setup/00_setup_local_docker.md`
- [ ] README.md updated with link to setup guide
- [ ] Prerequisites section lists all required software with download links
- [ ] Step-by-step setup instructions complete and tested
- [ ] Common commands documented with examples
- [ ] Port mapping table created
- [ ] Service access instructions provided (URLs)
- [ ] Troubleshooting section addresses common issues
- [ ] Architecture diagram created showing service relationships
- [ ] Commands for tests, migrations, and admin tasks documented
- [ ] Code reviewed by tech lead
- [ ] Tested: New developer can complete setup following docs within 30 minutes
- [ ] All acceptance criteria verified
- [ ] No critical or high-severity issues

## Tasks

Detailed development tasks will be generated in [tasks.md](./tasks.md) using the `/spec-generate-tasks` command.

### Task Summary
- **Total Tasks:** TBD
- **Completed:** 0
- **In Progress:** 0
- **Blocked:** 0

## Notes

### Questions / Open Items
- [ ] Should we create video walkthroughs in addition to written documentation?
- [ ] Do we need separate documentation for Windows/Mac/Linux platforms?
- [ ] Should we include a quick start checklist (1-page summary)?

### Assumptions
- Developers comfortable with command-line interfaces
- Basic understanding of Docker concepts (containers, images, volumes)
- Markdown documentation format acceptable

### Out of Scope
- Video tutorials or screencasts
- Interactive documentation (runnable notebooks)
- Automated setup scripts (document manual setup only)
- Production deployment documentation (separate guide)

## Related User Stories

- All User Stories in Local Development Environment feature (US-1 through US-11)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
