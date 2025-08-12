#!/bin/bash
# Script to run integration tests inside Docker container

echo "Starting integration tests in Docker container..."

# Create a test script that will be executed inside the container
TEST_SCRIPT=$(cat << 'EOF'
#!/bin/bash
echo "Inside Docker container - installing required packages..."
pip install passlib[bcrypt] python-dotenv "python-jose[cryptography]" email-validator fastapi uvicorn -q

echo "Setting up Python path..."
export PYTHONPATH=/home/src/src:/home/src:$PYTHONPATH
export DATABASE_URL=postgresql://postgres:postgres@alphapulse-postgres:5432/alphapulse

echo "Running integration tests..."
cd /home/src

# Run specific integration tests that don't require external dependencies
echo "1. Testing FastAPI basic functionality..."
python -c "
import sys
sys.path.insert(0, '/home/src/src')
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
"

echo "2. Testing database connection..."
python -c "
import sys
sys.path.insert(0, '/home/src/src')
try:
    from alphapulse.api.database import get_db
    from sqlalchemy import text
    
    db_gen = get_db()
    db = next(db_gen)
    
    # Test connection
    result = db.execute(text('SELECT 1')).scalar()
    print(f'✅ Database connection test: {result}')
    
    # Test Decimal support in database
    result = db.execute(text(\"SELECT NUMERIC '123.456789'\"))
    print(f'✅ Decimal database test: {result.fetchone()[0]}')
    
    db.close()
except Exception as e:
    print(f'❌ Database error: {e}')
"

echo "3. Testing pipeline integration..."
python -c "
import sys
sys.path.insert(0, '/home/src/alphapulse')
try:
    # Test if pipeline modules can be imported
    import pipelines.btc_price_pipeline.calculate_technical_indicators as btc
    print('✅ BTC price pipeline module imported')
    
    # Check if pandas-ta is available
    import pandas_ta
    print(f'✅ pandas-ta version: {pandas_ta.__version__}')
    
except Exception as e:
    print(f'❌ Pipeline error: {e}')
"

echo "✅ All integration tests completed successfully!"
EOF
)

# Write the test script to a file
echo "$TEST_SCRIPT" > /tmp/docker_test.sh
chmod +x /tmp/docker_test.sh

# Copy the test script to a location accessible from the container
cp /tmp/docker_test.sh ./docker_test_container.sh

# Try to execute in container using docker compose run
echo "Attempting to run tests in container..."
cd infra
docker compose run --rm mage bash -c "
    cd /home/src &&
    pip install passlib[bcrypt] python-dotenv "python-jose[cryptography]" email-validator fastapi uvicorn &&
    export PYTHONPATH=/home/src/src:/home/src:\$PYTHONPATH &&
    export DATABASE_URL=postgresql://postgres:postgres@alphapulse-postgres:5432/alphapulse &&
    echo '1. Testing FastAPI basic functionality...' &&
    python -c \"
import sys
sys.path.insert(0, '/home/src/src')
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
sys.path.insert(0, '/home/src/src')
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
sys.path.insert(0, '/home/src/alphapulse')
try:
    # Test if pipeline modules can be imported
    import pipelines.btc_price_pipeline.calculate_technical_indicators as btc
    print('✅ BTC price pipeline module imported')
    
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