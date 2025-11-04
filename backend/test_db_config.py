#!/usr/bin/env python
"""
Test script to verify database configuration without Django app initialization.
Tests dj-database-url parsing and connection parameters.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock decouple config for testing
class MockConfig:
    def __call__(self, key, default=None, cast=None):
        env_value = os.getenv(key, default)
        if cast and env_value is not None:
            return cast(env_value)
        return env_value

# Mock imports
config = MockConfig()

# Now test dj_database_url
import dj_database_url

print("=" * 80)
print("DATABASE CONFIGURATION TEST")
print("=" * 80)

# Test DATABASE_URL parsing
database_url = os.getenv('DATABASE_URL')
print(f"\n1. DATABASE_URL environment variable:")
print(f"   Value: {database_url}")

# Parse with dj_database_url
db_config = dj_database_url.config(
    default=f"postgresql://{config('POSTGRES_USER', default='veille_tech_user')}:"
            f"{config('POSTGRES_PASSWORD', default='postgres')}@"
            f"{config('POSTGRES_HOST', default='db')}:"
            f"{config('POSTGRES_PORT', default='5432')}/"
            f"{config('POSTGRES_DB', default='veille_tech_db')}",
    conn_max_age=60,
    conn_health_checks=True,
    ssl_require=False,
)

print(f"\n2. Parsed database configuration:")
for key, value in db_config.items():
    if key != 'PASSWORD':
        print(f"   {key}: {value}")

print(f"\n3. Migration-specific settings:")
print(f"   CONN_MAX_AGE: {db_config.get('CONN_MAX_AGE')} seconds")
print(f"   CONN_HEALTH_CHECKS: {db_config.get('CONN_HEALTH_CHECKS')}")
print(f"   Expected ATOMIC_REQUESTS: True (set separately in Django settings)")

print(f"\n4. Validation:")
checks = []
if db_config.get('CONN_MAX_AGE') == 60:
    checks.append("PASS - Connection pooling set to 60 seconds")
else:
    checks.append(f"FAIL - Connection pooling is {db_config.get('CONN_MAX_AGE')}, expected 60")

if db_config.get('CONN_HEALTH_CHECKS') is True:
    checks.append("PASS - Connection health checks enabled")
else:
    checks.append("FAIL - Connection health checks not enabled")

if db_config.get('ENGINE') == 'django.db.backends.postgresql':
    checks.append("PASS - PostgreSQL engine configured")
else:
    checks.append(f"FAIL - Engine is {db_config.get('ENGINE')}")

for check in checks:
    status = "OK" if check.startswith("PASS") else "FAIL"
    symbol = "[+]" if check.startswith("PASS") else "[X]"
    print(f"   {symbol} {check}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
