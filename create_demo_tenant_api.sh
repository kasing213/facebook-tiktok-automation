#!/bin/bash
# Script to create demo tenant via Railway API

echo "Creating demo tenant via Railway API..."

curl -X POST "https://web-production-3ed15.up.railway.app/api/tenants" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Organization",
    "slug": "demo-tenant",
    "admin_email": "admin@demo.com",
    "admin_username": "demo_admin"
  }'

echo ""
echo "Demo tenant creation attempted!"
