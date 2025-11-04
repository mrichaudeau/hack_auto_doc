#!/usr/bin/env python
"""
Verify database configuration for migrations.
This script checks that all migration-friendly settings are properly configured.
"""
import os
import sys
import django

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veille_tech.settings')
django.setup()

from django.conf import settings
from django.db import connection


def verify_database_config():
    """Verify database configuration settings."""
    print("=" * 80)
    print("DATABASE CONFIGURATION VERIFICATION")
    print("=" * 80)

    db_config = settings.DATABASES['default']

    # Check required settings
    checks = {
        'Engine': db_config.get('ENGINE'),
        'Name': db_config.get('NAME'),
        'User': db_config.get('USER'),
        'Host': db_config.get('HOST'),
        'Port': db_config.get('PORT'),
        'Connection Pooling (CONN_MAX_AGE)': db_config.get('CONN_MAX_AGE'),
        'Connection Health Checks': db_config.get('CONN_HEALTH_CHECKS'),
        'Atomic Requests': db_config.get('ATOMIC_REQUESTS'),
    }

    print("\n1. DATABASE SETTINGS:")
    print("-" * 80)
    for key, value in checks.items():
        status = "OK" if value is not None else "MISSING"
        print(f"  {key:35s}: {value} [{status}]")

    # Verify connection pooling
    print("\n2. CONNECTION POOLING:")
    print("-" * 80)
    conn_max_age = db_config.get('CONN_MAX_AGE', 0)
    if conn_max_age == 60:
        print("  CONN_MAX_AGE: 60 seconds [OK - Optimal for migrations]")
    elif conn_max_age > 0:
        print(f"  CONN_MAX_AGE: {conn_max_age} seconds [WARNING - Recommended: 60]")
    else:
        print("  CONN_MAX_AGE: 0 (disabled) [WARNING - Connection pooling disabled]")

    # Verify atomic requests
    print("\n3. TRANSACTION SAFETY:")
    print("-" * 80)
    if db_config.get('ATOMIC_REQUESTS'):
        print("  ATOMIC_REQUESTS: True [OK - Transaction safety enabled]")
    else:
        print("  ATOMIC_REQUESTS: False [WARNING - Transaction safety disabled]")

    # Test database connection
    print("\n4. DATABASE CONNECTION TEST:")
    print("-" * 80)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"  Connection: SUCCESS")
            print(f"  PostgreSQL Version: {version}")

            # Check for pgvector extension (may not be installed yet)
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """)
            pgvector_installed = cursor.fetchone()[0]
            if pgvector_installed:
                print("  pgvector Extension: INSTALLED")
            else:
                print("  pgvector Extension: NOT INSTALLED (will be installed by migration)")
    except Exception as e:
        print(f"  Connection: FAILED")
        print(f"  Error: {str(e)}")
        return False

    # Check user privileges
    print("\n5. USER PRIVILEGES:")
    print("-" * 80)
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    usesuper AS is_superuser,
                    usecreatedb AS can_create_db
                FROM pg_user
                WHERE usename = CURRENT_USER;
            """)
            privileges = cursor.fetchone()
            is_superuser, can_create_db = privileges

            if is_superuser:
                print("  Superuser: YES [OK - Can create pgvector extension]")
            else:
                print("  Superuser: NO [WARNING - Cannot create pgvector extension]")
                print("    Resolution: ALTER USER {} WITH SUPERUSER;".format(
                    db_config.get('USER')
                ))

            if can_create_db:
                print("  Create Database: YES [OK]")
            else:
                print("  Create Database: NO [INFO]")
    except Exception as e:
        print(f"  Privilege Check: FAILED")
        print(f"  Error: {str(e)}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = verify_database_config()
    sys.exit(0 if success else 1)
