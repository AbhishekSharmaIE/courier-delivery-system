#!/bin/bash
# Deployment script for Courier Delivery System
# This script sets up the application on a server (e.g., EC2)

set -e

echo "=== Courier Delivery System Deployment ==="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install --break-system-packages -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env <<EOF
# Database Configuration
DB_TYPE=sqlite
# For PostgreSQL/RDS, uncomment and set:
# DB_TYPE=postgres
# DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
# DB_PORT=5432
# DB_NAME=courier_db
# DB_USER=admin
# DB_PASSWORD=your-password

# AWS Configuration (optional)
# AWS_REGION=us-east-1
# S3_BUCKET=your-bucket-name
# SNS_TOPIC_ARN=arn:aws:sns:region:account:topic-name
EOF
    echo "✓ .env file created"
else
    echo "✓ .env file already exists"
fi
echo ""

# Initialize database
echo "Initializing database..."
python3 -c "from db_config import init_db; init_db(); print('Database initialized')"
echo "✓ Database initialized"
echo ""

# Check if app is already running
if pgrep -f "python3 app.py" > /dev/null; then
    echo "Stopping existing application..."
    pkill -f "python3 app.py"
    sleep 2
fi

# Start application
echo "Starting application..."
nohup python3 app.py > app.log 2>&1 &
APP_PID=$!

# Wait a moment and check if it started
sleep 3
if ps -p $APP_PID > /dev/null; then
    echo "✓ Application started (PID: $APP_PID)"
    echo "✓ Application running on http://localhost:5000"
    echo "✓ Logs: app.log"
else
    echo "✗ Application failed to start. Check app.log for errors."
    exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo "Test the API: curl http://localhost:5000/api/health"

