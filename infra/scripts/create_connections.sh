#!/bin/bash
set -e

echo "Creating Airflow Connections..."

# Create postgres_default connection
airflow connections add postgres_default \
    --conn-uri postgresql://postgres:postgres@postgres:5432/alphapulse \
    || echo "Connection postgres_default already exists or failed to create"

echo "Connections created successfully."
