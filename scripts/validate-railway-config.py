#!/usr/bin/env python3
"""
Railway Configuration Validation Script
Validates Redis and PostgreSQL service configuration
"""

import os
import sys
import json
import re
from typing import Dict, List, Tuple

def load_env_file(env_file: str) -> Dict[str, str]:
    """Load environment variables from file"""
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

def validate_railway_config() -> Tuple[bool, List[str]]:
    """Validate Railway configuration"""
    errors = []
    warnings = []

    # Check railway.json configuration
    railway_json_path = 'railway.json'
    if os.path.exists(railway_json_path):
        try:
            with open(railway_json_path, 'r') as f:
                config = json.load(f)

            # Check for multi-service configuration
            if 'services' not in config:
                warnings.append("railway.json lacks explicit service configuration, may cause service identification errors")
            else:
                services = config.get('services', {})
                if 'redis' not in services:
                    errors.append("railway.json missing Redis service configuration")
                if 'postgres' not in services:
                    errors.append("railway.json missing PostgreSQL service configuration")

        except json.JSONDecodeError as e:
            errors.append(f"railway.json format error: {e}")

    # Check environment variable configuration
    env_files = ['.env', '.env.example', '.env.railway']
    for env_file in env_files:
        if os.path.exists(env_file):
            env_vars = load_env_file(env_file)

            # Check key environment variables
            if 'DATABASE_URL' not in env_vars:
                warnings.append(f"{env_file} missing DATABASE_URL configuration")
            if 'REDIS_URL' not in env_vars:
                warnings.append(f"{env_file} missing REDIS_URL configuration")

            # Check for confused variable naming
            redis_url = env_vars.get('REDIS_URL', '')
            if redis_url and 'postgres' in redis_url.lower():
                errors.append(f"{env_file} REDIS_URL contains postgres, possible configuration error")

            database_url = env_vars.get('DATABASE_URL', '')
            if database_url and 'redis' in database_url.lower():
                errors.append(f"{env_file} DATABASE_URL contains redis, possible configuration error")

    return len(errors) == 0, errors + warnings

def check_railway_service_patterns():
    """Check Railway service naming patterns"""
    print("Checking Railway service configuration...")

    # Validate configuration files
    is_valid, messages = validate_railway_config()

    if not messages:
        print("No configuration files found")
    else:
        for message in messages:
            if "error" in message.lower() or "missing" in message.lower():
                print(f"[ERROR] {message}")
            else:
                print(f"[WARNING] {message}")

    # Provide configuration suggestions
    print("\nRailway Service Configuration Suggestions:")
    print("1. Service Naming Standards:")
    print("   - PostgreSQL service: must contain 'postgres' or 'database' keywords")
    print("   - Redis service: must contain 'redis' keywords")
    print("   - Avoid confusing names")

    print("\n2. Environment Variable Checklist:")
    print("   [OK] PostgreSQL service should provide: DATABASE_URL")
    print("   [OK] Redis service should provide: REDIS_URL")
    print("   [X] Redis service should NOT provide: DATABASE_PUBLIC_URL")
    print("   [X] PostgreSQL service should NOT provide: REDIS_URL")

    print("\n3. Verification Methods:")
    print("   - Check service environment variables in Railway console")
    print("   - Confirm service type display is correct")
    print("   - Check Source Image matches service type")

    return is_valid

if __name__ == "__main__":
    print("ChaiWord Duck Project Railway Configuration Validation Tool")
    print("=" * 60)

    success = check_railway_service_patterns()

    if success:
        print("\n[SUCCESS] Configuration validation passed")
        sys.exit(0)
    else:
        print("\n[ERROR] Configuration issues found, please fix according to suggestions")
        sys.exit(1)