# Quick Reference: CI/CD Pipeline

## Common Commands

### Running CI Locally

**Backend:**
```bash
# Linting
cd backend
poetry install
poetry run black --check .
poetry run flake8 .

# Unit tests
poetry run pytest tests/unit -v -m "unit"

# Integration tests (requires services)
docker-compose up -d db redis
poetry run pytest tests/integration -v -m "integration"
docker-compose down

# Coverage
poetry run pytest --cov=veille_tech --cov=apps --cov-report=html --cov-fail-under=80
open htmlcov/index.html
```

**Frontend:**
```bash
# Linting
cd frontend
npm ci
npm run lint

# Tests
npm test -- --run
npm run test:coverage -- --run

# Build
npm run build
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Patch release (v1.0.0 → v1.0.1)
git commit -m "fix: resolve authentication timeout"

# Minor release (v1.0.0 → v1.1.0)
git commit -m "feat: add password reset"

# Major release (v1.0.0 → v2.0.0)
git commit -m "feat!: migrate to Django 5

BREAKING CHANGE: drops Python 3.8 support"
```

### Triggering Workflows

**Via GitHub CLI:**
```bash
# Manual CI run
gh workflow run ci.yml

# Manual release with version bump
gh workflow run release.yml -f version_bump=minor

# View workflow runs
gh run list --workflow=ci.yml
gh run list --workflow=release.yml

# Watch latest run
gh run watch

# View logs
gh run view --log
```

**Via GitHub UI:**
1. Go to repository
2. Click "Actions" tab
3. Select workflow
4. Click "Run workflow"

### Checking Workflow Status

**Status Badges:**
- CI: https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/ci.yml
- Release: https://github.com/mrichaudeau/hack_auto_doc/actions/workflows/release.yml

**Quick Status:**
```bash
# Get latest workflow run status
gh run list --limit 1

# Get detailed status
gh run view

# Download artifacts
gh run download <run-id>
```

### Troubleshooting

**CI Failing on Tests:**
```bash
# Run tests locally first
cd backend
poetry run pytest -v

# Check specific test
poetry run pytest tests/path/to/test.py::test_name -v

# Run with debugging
poetry run pytest --pdb
```

**Coverage Too Low:**
```bash
# Check coverage report
poetry run pytest --cov=veille_tech --cov-report=html
open htmlcov/index.html

# Find uncovered lines
poetry run pytest --cov=veille_tech --cov-report=term-missing
```

**Linting Failures:**
```bash
# Auto-fix most issues
cd backend
poetry run black .
poetry run isort .

cd frontend
npm run lint:fix
```

**Release Fails:**
```bash
# Check if tag already exists
git tag -l

# Delete local tag if needed
git tag -d v1.0.0

# Delete remote tag if needed (use with caution!)
git push origin :refs/tags/v1.0.0
```

### Viewing Releases

**GitHub UI:**
- Go to repository
- Click "Releases" on right sidebar
- View release notes and download artifacts

**GitHub CLI:**
```bash
# List releases
gh release list

# View specific release
gh release view v1.0.0

# Download release assets
gh release download v1.0.0

# Create manual release (not recommended - use workflow)
gh release create v1.0.0 --notes "Release notes"
```

## Workflow Structure

### CI Pipeline Jobs
```
lint-backend ─┐
              ├─> build-validation
test-backend-unit ─┤
test-backend-integration ─┤
test-backend-coverage ─┤
              ├─>
lint-frontend ─┤
test-frontend ─┘
```

### Release Pipeline Jobs
```
versioning ─> run-ci ─> build-artifacts ─> create-release ─> notify
                  |
                  └─> (full CI pipeline)
```

## Important Notes

⚠️ **Before Merging to Main:**
- Ensure all CI checks pass
- Review coverage report
- Check for breaking changes
- Update CHANGELOG if needed

⚠️ **Release Process:**
- Always use semantic commit messages
- Release pipeline auto-triggers on push to main
- Manual override available via workflow dispatch
- Tags are created automatically

⚠️ **Artifacts:**
- Stored for 90 days (releases) or 30 days (CI runs)
- Include Docker images, builds, and deployment files
- Download via GitHub UI or CLI

## Version Numbering

```
v{MAJOR}.{MINOR}.{PATCH}
  │       │       └─ Bug fixes, patches
  │       └─ New features, backward compatible
  └─ Breaking changes
```

**Examples:**
- v1.0.0 → v1.0.1: Bug fix
- v1.0.0 → v1.1.0: New feature
- v1.0.0 → v2.0.0: Breaking change

## Resources

- 📚 [Full Documentation](README.md)
- 🔧 [CI Workflow](.github/workflows/ci.yml)
- 🚀 [Release Workflow](.github/workflows/release.yml)
- 📖 [Conventional Commits](https://www.conventionalcommits.org/)
- 📋 [Semantic Versioning](https://semver.org/)
