# Functional Specification Management

This project uses the Functional Spec Planner plugin for managing Product Owner specifications and generating development tasks.

## Directory Structure

```
./specs/              # Generated specifications (DO NOT EDIT MANUALLY)
├── <feature>/
│   ├── feature.md
│   ├── user-stories.md
│   └── <user-story>/
│       ├── user-story.md
│       ├── tasks.md
│       ├── dependencies.json
│       └── github-issues.json

./docs/po_input/      # Product Owner input documents
└── <feature>.md      # Raw PO specifications

./templates/          # Template files for reference
├── feature-template.md
├── user-story-template.md
└── po-input-guide.md
```

## Quick Start

### 1. Product Owner creates specification
- Write functional spec in `./docs/po_input/<feature-name>.md`
- See `./templates/po-input-guide.md` for guidance on writing effective specifications

### 2. Parse specification
```bash
/spec-parse docs/po_input/<feature-name>.md
```
This converts your raw PO document into structured Feature and User Story files.

**Output:**
- `./specs/<feature>/feature.md` - Structured Feature specification
- `./specs/<feature>/US-*/user-story.md` - Individual User Story files
- `./specs/<feature>/user-stories.md` - Overview of all User Stories

### 3. Generate tasks for User Story
```bash
/spec-generate-tasks <feature>/<user-story>
```
This breaks down the User Story into granular, implementable development tasks.

**Output:**
- `./specs/<feature>/<user-story>/tasks.md` - Detailed task breakdown
- `./specs/<feature>/<user-story>/dependencies.json` - Task dependency graph

### 4. Review tasks manually
**IMPORTANT:** Always review `./specs/<feature>/<user-story>/tasks.md` before creating GitHub issues!

Verify:
- Task breakdown is appropriate and complete
- Acceptance criteria are specific and testable
- Dependencies are correct
- Effort estimates are realistic
- Technical approach is sound

### 5. Create GitHub issues
```bash
/spec-create-issues <feature>/<user-story>
```
Creates GitHub issues from the verified tasks.md file.

**Requirements:**
- tasks.md file must exist and be reviewed
- GitHub MCP must be configured

**Output:**
- GitHub issues created with labels, dependencies, and metadata
- `./specs/<feature>/<user-story>/github-issues.json` - Issue mapping

## Available Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/spec-help` | Show interactive help guide | Anytime you need help |
| `/spec-init` | Initialize project structure | First time setup (already done!) |
| `/spec-parse <file>` | Parse PO specs | When you have functional specs |
| `/spec-generate-tasks <path>` | Generate development tasks | After User Story is defined |
| `/spec-create-issues <path>` | Create GitHub issues | After manual task verification |
| `/spec-full-pipeline <file>` | Complete workflow | Run parse→stories→tasks in one go |
| `/spec-update <file>` | Regenerate after changes | When PO docs are modified |

## Common Workflows

### Workflow A: Step-by-Step (Recommended for New Users)

Maximum control with verification at each stage:

1. **Create PO document** in `./docs/po_input/my-feature.md`
2. **Parse**: `/spec-parse docs/po_input/my-feature.md`
3. **Review** generated specs in `./specs/my-feature/`
4. **Generate tasks**: `/spec-generate-tasks my-feature/US-1`
5. **Review** `./specs/my-feature/US-1/tasks.md` manually
6. **Create issues**: `/spec-create-issues my-feature/US-1`
7. **Repeat** for each User Story

### Workflow B: Batch Processing (For Well-Defined Features)

Faster workflow when requirements are clear:

1. **Run full pipeline**: `/spec-full-pipeline docs/po_input/my-feature.md`
2. **Review all tasks.md files** in `./specs/my-feature/*/tasks.md`
3. **Batch create issues**: `/spec-create-issues my-feature/*`

### Workflow C: Update After Changes

When Product Owner modifies requirements:

1. **Edit PO document** in `./docs/po_input/my-feature.md`
2. **Regenerate specs**: `/spec-update docs/po_input/my-feature.md`
3. **Review changes** in `./specs/my-feature/`
4. **Regenerate affected tasks**: `/spec-generate-tasks my-feature/US-1`
5. **Handle GitHub issues manually** (close obsolete, create new)

## Your Project: AI-Powered Technology Watch Platform

Based on your existing documentation structure, here's a suggested approach:

### Option 1: Convert Existing Bloc Documentation

Your existing docs are well-structured and can serve as PO input:

```bash
# Start with Authentication (Bloc 1)
/spec-parse docs/01_Authentification_Autorisation.md

# Then process other blocs
/spec-parse docs/02_Gestion_Sujets_Abonnements.md
/spec-parse docs/03_Pipeline_Contenu_IA.md
# ... etc
```

### Option 2: Use Existing Backlog

If `docs/action_plan/Backlog_Global.md` contains detailed user stories:

```bash
/spec-parse docs/action_plan/Backlog_Global.md
```

### Recommended Implementation Order

Based on `CLAUDE.md`, follow this sequence:

1. **Bloc 1: Authentication** - Foundation for security
2. **Bloc 2: Subscription Management** - Defines user demand
3. **Bloc 3: AI Pipeline (Basic)** - Core value creation
4. **Bloc 4: Report Consultation** - Delivers value to users
5. **Bloc 5: Recommendation Engine** - Requires embeddings from Bloc 3
6. **Bloc 6: FinOps Tracking** - Administrative requirement

## Best Practices

### Before Creating GitHub Issues
- ✅ Always review tasks.md - it's your quality gate!
- ✅ Check acceptance criteria are specific and testable
- ✅ Verify dependencies are correct
- ✅ Confirm effort estimates are realistic
- ✅ Ensure technical approach aligns with project architecture

### Organizing Your Work
- 📁 Keep PO docs in `docs/po_input/` for version control
- 📊 Use dependency graphs to identify parallel work
- 🎯 Start with P0/P1 tasks, defer P3 for later
- 🔄 Update PO docs first, then regenerate specs

### GitHub Integration
- 🏷️ Use labels to filter and organize issues
- 📌 Create GitHub Projects to visualize dependencies
- 👥 Assign issues to team members
- 🗓️ Use milestones to track feature completion

## File Management

### What's Safe to Edit
- ✅ `./docs/po_input/*.md` - Your source specifications
- ✅ `./templates/*.md` - Customize for your project

### What's Auto-Generated (Don't Edit)
- ⚠️ `./specs/**/*.md` - Regenerated from PO input
- ⚠️ `./specs/**/dependencies.json` - Auto-generated dependency graph
- ⚠️ `./specs/**/github-issues.json` - GitHub issue mapping

### Version Control
The `.gitignore` has been updated to exclude `github-issues.json` files (they contain transient GitHub issue numbers), but keeps all other specs in version control for documentation and history.

## Getting Help

### Interactive Help
```bash
/spec-help                    # Full interactive guide
/spec-help --quick-start      # Quick-start workflow only
/spec-help --github-setup     # GitHub MCP configuration steps
/spec-help --examples         # Usage examples with your files
```

### Documentation
- 📖 **PO Input Guide:** `./templates/po-input-guide.md`
- 📋 **Feature Template:** `./templates/feature-template.md`
- 📄 **User Story Template:** `./templates/user-story-template.md`

### Project Context
- 📚 **Project Overview:** `CLAUDE.md`
- 📖 **Functional Specs:** `docs/*.md`
- 📊 **Action Plan:** `docs/action_plan/Backlog_Global.md`

## Tips for Your AI Platform

### Technology Stack Considerations
When reviewing generated tasks, ensure they align with:
- Python 3.11+ with Django/DRF
- Langgraph for AI agent orchestration
- Celery + Redis for async execution
- PostgreSQL 15 with pgvector
- React SPA frontend

### Security Requirements
Verify tasks include:
- Argon2 password hashing
- JWT token authentication
- Permission-based access control
- Rate limiting on sensitive endpoints

### Performance Targets
Check that acceptance criteria match:
- Auth endpoints: < 300ms (P95)
- Pipeline execution: < 5 minutes per subject
- Recommendation queries: < 500ms
- Cost logging overhead: < 50ms

## Next Steps

1. **Read the PO Input Guide**: `./templates/po-input-guide.md`
2. **Choose your first feature**: Start with Bloc 1 (Authentication)
3. **Prepare PO document**: Create or adapt from existing docs
4. **Run the workflow**: Parse → Generate Tasks → Review → Create Issues

---

**Generated by:** Functional Spec Planner Plugin
**Project:** AI-Powered Technology Watch Platform
**Initialized:** 2025-10-28
