# Backend Development Guide

## Quick Start

### Prerequisites

- Docker Desktop 24.0+ or Docker Engine 24.0+
- Docker Compose v2
- Git

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone [repository-url]
   cd hackathon_base_de_connaissance
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.backend.example .env.backend
   # Edit .env.backend with your configuration
   ```

3. **Start services**:
   ```bash
   docker-compose up -d db redis backend
   ```

4. **Run migrations**:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

## Accessing Services

- **API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/
- **PostgreSQL**: `localhost:5432` (internal only, not exposed to host)
- **Redis**: `localhost:6379` (internal only, not exposed to host)

## Development Workflow

### Hot Reload

Code changes are automatically detected and the server reloads:

1. Edit any `.py` file in `backend/`
2. Watch logs for reload: `docker-compose logs -f backend`
3. Server reloads within 2-3 seconds
4. Refresh browser to see changes

**Note**: For Windows with WSL2, ensure code is in WSL filesystem for optimal performance.

### Running Commands

#### Django Management Commands

```bash
# Django shell
docker-compose exec backend python manage.py shell

# Check configuration
docker-compose exec backend python manage.py check

# Show migrations
docker-compose exec backend python manage.py showmigrations

# Make migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Run tests
docker-compose exec backend python manage.py test
```

#### Poetry Commands

```bash
# Install dependency
docker-compose exec backend poetry add package-name

# Install dev dependency
docker-compose exec backend poetry add --group dev package-name

# Update dependencies
docker-compose exec backend poetry update

# Show installed packages
docker-compose exec backend poetry show
```

### Running Tests

```bash
# All tests
docker-compose exec backend pytest

# Specific test file
docker-compose exec backend pytest tests/integration/test_api_endpoints.py

# With coverage
docker-compose exec backend pytest --cov=. --cov-report=html

# Django tests
docker-compose exec backend python manage.py test

# Specific app tests
docker-compose exec backend python manage.py test core
```

### Code Quality

```bash
# Format code with Black
docker-compose exec backend black .

# Lint with Flake8
docker-compose exec backend flake8

# Type checking (if mypy is installed)
docker-compose exec backend mypy .
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U veille_tech_user -d veille_tech_db

# Run SQL file
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -f /docker-entrypoint-initdb.d/init-db.sql

# Backup database
docker-compose exec db pg_dump -U veille_tech_user veille_tech_db > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U veille_tech_user veille_tech_db

# Check pgvector extension
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Redis Operations

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check cache (DB 1)
docker-compose exec redis redis-cli -n 1 KEYS "*"

# Check Celery broker (DB 0)
docker-compose exec redis redis-cli -n 0 KEYS "*"

# Monitor Redis commands
docker-compose exec redis redis-cli MONITOR

# Get Redis info
docker-compose exec redis redis-cli INFO
```

## Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs backend --tail=100

# Follow logs since timestamp
docker-compose logs backend --since 2h
```

### Common Issues

#### Backend won't start

1. **Check dependencies**:
   ```bash
   docker-compose ps
   # Ensure db and redis are healthy
   ```

2. **Check environment variables**:
   ```bash
   docker-compose exec backend env | grep -E "(POSTGRES|REDIS|CELERY)"
   ```

3. **Check database connection**:
   ```bash
   docker-compose exec backend python manage.py dbshell
   ```

#### Database connection error

1. **Verify credentials in .env.backend**
2. **Check database is running**:
   ```bash
   docker-compose ps db
   ```

3. **Test connection**:
   ```bash
   docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT 1;"
   ```

#### Hot reload not working

1. **Check volume mounting**:
   ```bash
   docker-compose exec backend ls -la /app
   ```

2. **Ensure code is in WSL filesystem** (Windows with WSL2)

3. **Check file watching**:
   ```bash
   docker-compose logs backend | grep -i watching
   ```

#### Port already in use

```bash
# Stop conflicting service
docker-compose down

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

## Development Best Practices

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Django Best Practices

- Use Django ORM instead of raw SQL
- Use class-based views for consistency
- Implement proper permission checks
- Use Django forms for validation
- Never commit secrets to Git

### Testing

- Write tests for all new features
- Aim for > 80% code coverage
- Use factories for test data
- Mock external API calls
- Test edge cases and error handling

### Git Workflow

- Create feature branches from `main`
- Use conventional commit messages
- Keep commits focused and atomic
- Test before committing
- Create pull requests for review

## Performance Optimization

### Database

- Add indexes for frequently queried fields
- Use `select_related` and `prefetch_related` for joins
- Monitor slow queries with Django Debug Toolbar
- Use database connection pooling

### Cache

- Cache expensive computations
- Use Redis for session storage
- Implement cache invalidation strategies
- Monitor cache hit rates

### API

- Implement pagination for list endpoints
- Use serializers efficiently
- Add throttling for rate limiting
- Monitor response times

## Security

### Development Environment

- Never use `DEBUG=True` in production
- Change `SECRET_KEY` for production
- Use strong passwords for database
- Don't expose database/Redis ports
- Keep dependencies updated

### Production Checklist

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY`
- [ ] Secure database passwords
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Error monitoring configured
- [ ] Backups configured

## Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Poetry Documentation](https://python-poetry.org/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## Support

For questions or issues:
- Check the documentation first
- Review logs: `docker-compose logs backend`
- Check health status: http://localhost:8000/api/health/
- Consult Django Admin: http://localhost:8000/admin/
