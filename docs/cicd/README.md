# CI/CD Pipeline Documentation

## Overview

This repository implements a comprehensive GitHub Actions CI/CD pipeline that automates the entire software delivery process from code commit to production release.

## Pipeline Architecture

### Workflows

#### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop` branches

**Jobs:**

##### Backend Jobs
- **lint-backend**: Code quality checks with Black and Flake8
- **test-backend-unit**: Unit tests (fast, isolated tests)
- **test-backend-integration**: Integration tests with PostgreSQL and Redis services
- **test-backend-coverage**: Full test suite with coverage reporting (80% minimum)

##### Frontend Jobs
- **lint-frontend**: ESLint code quality checks
- **test-frontend**: Vitest unit tests with coverage reporting

##### Build Validation
- **build-validation**: Validates Docker image builds for both backend and frontend

**Features:**
- ✅ Parallel job execution for faster feedback
- ✅ Dependency caching (Poetry, npm, Docker layers)
- ✅ Service containers for integration tests
- ✅ Coverage enforcement (80% minimum)
- ✅ Artifact uploads for test results and coverage reports
- ✅ Concurrency control to cancel outdated runs

#### 2. Release Pipeline (`.github/workflows/release.yml`)

**Triggers:**
- Push to `main` branch (automatic)
- Manual workflow dispatch with version bump selection

**Jobs:**

##### Versioning
- **versioning**: Calculates next version using semantic versioning
  - Auto-detects bump type from commit messages
  - Supports manual version bump override
  - Format: `v{MAJOR}.{MINOR}.{PATCH}`

##### CI Validation
- **run-ci**: Runs full CI pipeline to ensure quality before release

##### Build & Package
- **build-artifacts**: Creates production-ready artifacts
  - Backend Docker image
  - Frontend Docker image
  - Frontend production build (dist)
  - Requirements files
  - Deployment configuration files
  - Checksums for verification

##### Release Creation
- **create-release**: Creates GitHub Release
  - Auto-generated release notes from commits
  - Categorized changelog (Features, Bug Fixes, Documentation, Maintenance)
  - Git tag creation
  - Artifact attachments

##### Notifications
- **notify**: Post-release status notifications

**Features:**
- ✅ Semantic versioning with auto-detection
- ✅ Comprehensive release artifacts
- ✅ Auto-generated changelog
- ✅ Release artifact checksums
- ✅ GitHub Release creation
- ✅ Tag protection (no concurrent releases)

## Version Strategy

### Semantic Versioning

The pipeline uses [Semantic Versioning 2.0.0](https://semver.org/):

```
v{MAJOR}.{MINOR}.{PATCH}
```

**Version Bump Detection:**

| Commit Pattern | Bump Type | Example |
|----------------|-----------|---------|
| `BREAKING CHANGE:`, `feat!:`, `fix!:` | Major | v1.0.0 → v2.0.0 |
| `feat:` | Minor | v1.0.0 → v1.1.0 |
| `fix:`, `docs:`, `chore:`, etc. | Patch | v1.0.0 → v1.0.1 |

**Commit Message Format:**

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature (MINOR bump)
- `fix`: Bug fix (PATCH bump)
- `docs`: Documentation only
- `chore`: Maintenance tasks
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `style`: Code style changes (formatting)
- `perf`: Performance improvements

**Examples:**

```bash
# Patch release (v1.0.0 → v1.0.1)
git commit -m "fix: resolve authentication timeout issue"

# Minor release (v1.0.0 → v1.1.0)
git commit -m "feat: add password reset functionality"

# Major release (v1.0.0 → v2.0.0)
git commit -m "feat!: migrate to Django 5.0

BREAKING CHANGE: Django 5.0 drops support for Python 3.8"
```

## Usage Guide

### Running CI Pipeline

The CI pipeline runs automatically on:
- Every push to `main` or `develop`
- Every pull request to `main` or `develop`

**Manual Trigger:**
```bash
# Via GitHub CLI
gh workflow run ci.yml

# Via GitHub UI
Actions → CI Pipeline → Run workflow
```

### Creating a Release

#### Automatic Release (Recommended)

1. Commit your changes with semantic commit messages:
   ```bash
   git commit -m "feat: add new analytics dashboard"
   ```

2. Push to main branch:
   ```bash
   git push origin main
   ```

3. The release pipeline automatically:
   - Determines version from commit messages
   - Runs full CI suite
   - Builds artifacts
   - Creates GitHub Release
   - Generates changelog

#### Manual Release

1. Go to Actions → Release Pipeline
2. Click "Run workflow"
3. Select version bump type (major/minor/patch)
4. Click "Run workflow"

### Deploying a Release

1. Download release artifacts from GitHub Releases
2. Extract `deployment-files.tar.gz`:
   ```bash
   tar -xzf deployment-files.tar.gz
   ```

3. Configure environment variables:
   ```bash
   cp .env.backend.example .env.backend
   cp .env.frontend.example .env.frontend
   # Edit .env files with production values
   ```

4. Load Docker images:
   ```bash
   docker load < backend-docker-image.tar
   docker load < frontend-docker-image.tar
   ```

5. Start services:
   ```bash
   docker-compose up -d
   ```

## Configuration

### Required Secrets

No additional secrets required. The pipeline uses:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Optional Secrets

For enhanced features, add these secrets in repository settings:

| Secret | Purpose | Required |
|--------|---------|----------|
| `CODECOV_TOKEN` | Code coverage tracking | No |
| `SLACK_WEBHOOK_URL` | Slack notifications | No |
| `DOCKER_HUB_USERNAME` | Docker Hub publishing | No |
| `DOCKER_HUB_TOKEN` | Docker Hub publishing | No |

**Adding Secrets:**
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value

### Branch Protection Rules

**Recommended Configuration for `main` branch:**

1. Go to Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Select: `lint-backend`, `test-backend-unit`, `test-backend-integration`, `test-backend-coverage`, `lint-frontend`, `test-frontend`, `build-validation`
   - ✅ Require branches to be up to date before merging
   - ✅ Require conversation resolution before merging
   - ✅ Include administrators

## Monitoring & Troubleshooting

### Viewing Workflow Runs

**Via GitHub UI:**
1. Go to Actions tab
2. Select workflow (CI Pipeline or Release Pipeline)
3. Click on specific run to view details

**Via GitHub CLI:**
```bash
# List recent workflow runs
gh run list

# View specific run
gh run view <run-id>

# View logs
gh run view <run-id> --log
```

### Common Issues

#### Issue: Test Failures

**Symptoms:** CI pipeline fails on test jobs

**Solutions:**
1. Run tests locally:
   ```bash
   cd backend
   poetry run pytest -v
   ```
2. Check test logs in GitHub Actions artifacts
3. Ensure test database is properly configured

#### Issue: Coverage Below Threshold

**Symptoms:** `test-backend-coverage` job fails with coverage < 80%

**Solutions:**
1. Check coverage report artifact
2. Add tests for uncovered code:
   ```bash
   poetry run pytest --cov=veille_tech --cov-report=html
   open htmlcov/index.html
   ```

#### Issue: Docker Build Failures

**Symptoms:** `build-validation` or `build-artifacts` jobs fail

**Solutions:**
1. Test build locally:
   ```bash
   docker build -t test-backend ./backend
   docker build -t test-frontend ./frontend
   ```
2. Check Dockerfile syntax
3. Verify all dependencies are in pyproject.toml/package.json

#### Issue: Release Creation Fails

**Symptoms:** `create-release` job fails

**Solutions:**
1. Verify `GITHUB_TOKEN` has sufficient permissions
2. Check if tag already exists: `git tag -l`
3. Ensure all artifacts were uploaded successfully

### Debugging Workflows

**Enable debug logging:**
1. Go to repository Settings → Secrets
2. Add secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run workflow

**Download logs:**
```bash
# Download all logs
gh run download <run-id>

# Download specific artifact
gh run download <run-id> --name backend-test-results
```

## Status Badges

Add these badges to your README.md:

```markdown
[![CI Pipeline](https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/ci.yml/badge.svg)](https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/ci.yml)
[![Release Pipeline](https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/release.yml/badge.svg)](https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/release.yml)
```

## Support

For issues or questions:
1. Check this documentation
2. Review workflow logs in GitHub Actions
3. Contact DevOps team
4. Open an issue in the repository
