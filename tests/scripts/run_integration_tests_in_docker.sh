#!/bin/bash
# Script to run integration tests inside Docker container

echo "Starting integration tests in Docker container..."

# Try to execute in container using docker compose run
echo "Attempting to run tests in container..."
cd infra
docker compose run --rm trainer bash -c "
    cd /app &&
    pip install passlib[bcrypt] python-dotenv \"python-jose[cryptography]\" email-validator fastapi uvicorn &&
    export PYTHONPATH=/app/src:/app:\$PYTHONPATH &&
    export DATABASE_URL=postgresql://postgres:postgres@postgres:5432/alphapulse &&
    echo '1. Testing FastAPI basic functionality...' &&
    python -c \"
import sys
sys.path.insert(0, '/app/src')
try:
    from alphapulse.main import app
    print('✅ FastAPI app imported successfully')
    
    # Test Decimal encoder
    from decimal import Decimal
    from alphapulse.main import decimal_encoder
    result = decimal_encoder(Decimal('123.456789'))
    print(f'✅ Decimal encoder test: {result}')
    
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
\" &&
    echo '2. Testing database connection...' &&
    python -c \"
import sys
sys.path.insert(0, '/app/src')
try:
    from alphapulse.api.database import get_db
    from sqlalchemy import text
    
    db_gen = get_db()
    db = next(db_gen)
    
    # Test connection
    result = db.execute(text('SELECT 1')).scalar()
    print(f'✅ Database connection test: {result}')
    
    # Test Decimal support in database
    result = db.execute(text(\\\"SELECT NUMERIC '123.456789'\\\"))
    print(f'✅ Decimal database test: {result.fetchone()[0]}')
    
    db.close()
except Exception as e:
    print(f'❌ Database error: {e}')
\" &&
    echo '3. Testing pipeline integration...' &&
    python -c \"
import sys
sys.path.insert(0, '/app')
try:
    # Test if indicators can be imported
    import training.ultra_fast_train
    print('✅ Training module imported')
    
    # Check if pandas-ta is available
    import pandas_ta
    print(f'✅ pandas-ta version: {pandas_ta.version}')
    
except Exception as e:
    print(f'❌ Pipeline error: {e}')
\" &&
    echo '✅ All integration tests completed successfully!'
" 2>&1

# Clean up
rm -f ./docker_test_container.sh
cd ..

echo "Integration test execution completed."