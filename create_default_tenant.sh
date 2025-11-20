#!/bin/bash

# Create a default tenant using Railway CLI
# This tenant will be used for user registration

echo "Creating default tenant in Railway database..."

railway run python -c "
import sys
sys.path.insert(0, '.')
from app.core.db import get_db
from app.repositories.tenant import TenantRepository
from datetime import datetime

try:
    db = next(get_db())
    tenant_repo = TenantRepository(db)

    # Check if default tenant already exists
    tenants = db.execute('SELECT id, name, slug FROM tenant LIMIT 1').fetchone()

    if tenants:
        print(f'✅ Default tenant already exists:')
        print(f'   ID: {tenants[0]}')
        print(f'   Name: {tenants[1]}')
        print(f'   Slug: {tenants[2]}')
    else:
        # Create default tenant
        result = db.execute('''
            INSERT INTO tenant (name, slug, is_active, created_at, updated_at)
            VALUES ('Default Organization', 'default', true, NOW(), NOW())
            RETURNING id, name, slug
        ''')
        db.commit()
        tenant = result.fetchone()
        print(f'✅ Created default tenant:')
        print(f'   ID: {tenant[0]}')
        print(f'   Name: {tenant[1]}')
        print(f'   Slug: {tenant[2]}')

except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

echo "Done!"
