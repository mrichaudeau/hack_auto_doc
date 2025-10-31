# Security Checklist

This document provides a security checklist for the Technology Watch Platform to ensure secrets and sensitive data are properly protected.

## Pre-Commit Security Checklist

Before committing code, verify the following:

- [ ] No `.env` files committed to Git
- [ ] No `.env.backend` or `.env.frontend` files committed
- [ ] No hardcoded API keys in source code
- [ ] No hardcoded passwords or secrets in source code
- [ ] No accidentally committed database dumps with sensitive data
- [ ] All example files use placeholder values (`your-*-key-here`)

## Git Security Verification

### Check if .env Files Are Ignored

```bash
# Should return the file names (meaning they ARE ignored)
git check-ignore .env .env.backend .env.frontend
```

**Expected output:**
```
.env
.env.backend
.env.frontend
```

If files are NOT ignored, they will not be listed. This is a problem!

### Search Git History for Accidentally Committed Secrets

**Check for .env files in history:**
```bash
git log --all --full-history -- ".env*"
```

If this returns any commits, .env files were accidentally committed in the past.

**Search for specific secret patterns:**
```bash
# Search for Google AI API keys
git log --all -S"AIzaSy" --source --all

# Search for common environment variable names
git log --all -S"SECRET_KEY" --source --all
git log --all -S"POSTGRES_PASSWORD" --source --all
git log --all -S"GOOGLE_AI_STUDIO_API_KEY" --source --all
```

**Search current codebase for potential secrets:**
```bash
# Search for potential API keys (long alphanumeric strings)
grep -r "AIzaSy[A-Za-z0-9_-]" .
grep -r "sk-[A-Za-z0-9]" .

# Search for password-like environment variable assignments
grep -r "PASSWORD\s*=" . --include="*.py" --include="*.js"
```

### Remove Accidentally Committed Secrets

If secrets were accidentally committed, they must be removed from Git history:

**Option 1: BFG Repo-Cleaner (Recommended)**
```bash
# Install BFG
# Windows: choco install bfg
# Mac: brew install bfg
# Linux: Download from https://rtyley.github.io/bfg-repo-cleaner/

# Remove .env files from history
bfg --delete-files .env*

# Clean up repository
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

**Option 2: git filter-branch (Manual)**
```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env .env.backend .env.frontend' \
  --prune-empty --tag-name-filter cat -- --all
```

**After removing secrets:**
1. Force push to remote (if already pushed): `git push origin --force --all`
2. **IMMEDIATELY rotate all exposed secrets** (generate new keys, update in provider dashboards)
3. Notify team members to re-clone repository

## Runtime Security Checklist

### Local Development

- [ ] `.env.backend` created from `.env.backend.example`
- [ ] `.env.frontend` created from `.env.frontend.example`
- [ ] All placeholder values replaced with actual secrets
- [ ] Secrets generated using cryptographically secure methods
- [ ] `SECRET_KEY` minimum 50 characters (alphanumeric)
- [ ] `JWT_SECRET_KEY` minimum 50 characters (different from SECRET_KEY)
- [ ] `POSTGRES_PASSWORD` minimum 16 characters (strong password)
- [ ] `DEBUG=True` set for development (never production)

### Secret Generation

Use the provided utility:
```bash
# Generate Django SECRET_KEY and JWT_SECRET_KEY
python backend/scripts/generate_secrets.py
```

Or use OpenSSL:
```bash
# Generate 64-character base64 string
openssl rand -base64 48

# Generate 24-character base64 string
openssl rand -base64 18
```

### API Key Validation

- [ ] Google AI Studio API key obtained from [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
- [ ] Firecrawl API key obtained from [https://firecrawl.dev/](https://firecrawl.dev/)
- [ ] API keys tested and working
- [ ] API usage monitored in provider dashboards
- [ ] API keys NOT shared via email, Slack, or other insecure channels

### Docker Security

- [ ] Database port (5432) NOT exposed to host (internal network only)
- [ ] Redis port (6379) NOT exposed to host (internal network only)
- [ ] Backend/frontend ports (8000/3000) only exposed for development
- [ ] Containers run as non-root users (`appuser`, `node`)
- [ ] Multi-stage builds minimize attack surface
- [ ] Health checks configured for all services

## Production Deployment Checklist

### Environment Configuration

- [ ] `DEBUG=False` set in production
- [ ] `ALLOWED_HOSTS` restricted to production domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` restricted to production frontend domain(s)
- [ ] `SESSION_COOKIE_SECURE=True` (HTTPS only)
- [ ] `CSRF_COOKIE_SECURE=True` (HTTPS only)
- [ ] Unique secrets for production (different from dev/staging)

### Secret Management

- [ ] Secrets stored in secure vault (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Secrets rotated regularly (every 90 days recommended)
- [ ] Access to secrets restricted (least privilege principle)
- [ ] Audit logging enabled for secret access
- [ ] Backup/recovery plan for secrets

### Database Security

- [ ] PostgreSQL password uses strong entropy (min 24 characters)
- [ ] Database NOT exposed to public internet
- [ ] SSL/TLS required for connections
- [ ] Regular backups configured
- [ ] Backup encryption enabled
- [ ] Access restricted to application service account only

### Redis Security

- [ ] Redis authentication (AUTH) enabled
- [ ] Redis NOT exposed to public internet
- [ ] TLS encryption enabled for connections
- [ ] Memory limits configured
- [ ] Persistence disabled (or secured if enabled)

### Network Security

- [ ] All services behind firewall/security groups
- [ ] HTTPS enforced for all external connections
- [ ] Rate limiting configured
- [ ] DDoS protection enabled
- [ ] Security headers configured (CSP, HSTS, X-Content-Type-Options, etc.)

### Monitoring & Incident Response

- [ ] Secret exposure monitoring (GitHub secret scanning, GitGuardian, etc.)
- [ ] Failed authentication monitoring
- [ ] Unusual API usage monitoring
- [ ] Incident response plan documented
- [ ] On-call rotation configured

## Secret Rotation Schedule

| Secret | Rotation Frequency | Triggered By |
|--------|-------------------|--------------|
| Django SECRET_KEY | Every 90 days | Scheduled |
| JWT_SECRET_KEY | Every 90 days | Scheduled |
| Database passwords | Every 90 days | Scheduled |
| API keys | Annually or on compromise | Scheduled / Incident |
| SSL/TLS certificates | Before expiration (typically 90 days) | Scheduled |

## Automated Security Checks

### GitHub Actions (Optional)

Create `.github/workflows/security-check.yml`:
```yaml
name: Security Check
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check for secrets in code
        run: |
          # Fail if .env files are committed
          if git ls-files | grep -E '\.env$|\.env\.backend$|\.env\.frontend$'; then
            echo "ERROR: .env files should not be committed!"
            exit 1
          fi
      - name: Run secret scanning
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
```

### Pre-Commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Pre-commit hook to prevent committing .env files

if git diff --cached --name-only | grep -E '\.env$|\.env\.backend$|\.env\.frontend$'; then
  echo "ERROR: Attempting to commit .env files!"
  echo "These files contain secrets and should never be committed."
  echo "Remove them from staging with: git reset HEAD .env*"
  exit 1
fi

# Check for potential API keys in staged files
if git diff --cached | grep -E 'AIzaSy[A-Za-z0-9_-]{33}|sk-[A-Za-z0-9]{20,}'; then
  echo "WARNING: Potential API keys detected in staged changes!"
  echo "Please review carefully before committing."
  read -p "Continue anyway? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [Google Cloud Secret Management Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)

## Contact

For security incidents or concerns, contact the security team immediately:
- Email: security@example.com (update with actual contact)
- On-call: [Configure PagerDuty/OpsGenie] (update with actual on-call)

**For critical security vulnerabilities, do NOT create public GitHub issues.**
