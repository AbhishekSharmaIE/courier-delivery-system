# AWS Setup Guide - Courier Delivery System

This guide walks you through setting up AWS resources for the Courier Delivery System.

## Prerequisites

1. **AWS Account** - You need an active AWS account
2. **AWS CLI** - Install and configure AWS CLI
3. **AWS Credentials** - Configure your AWS credentials

### Step 1: Install and Configure AWS CLI

```bash
# Install AWS CLI (if not already installed)
pip3 install --break-system-packages awscli

# Configure AWS credentials
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### Step 2: Verify AWS Configuration

```bash
# Test your AWS credentials
aws sts get-caller-identity
```

You should see your AWS account ID and user ARN.

### Step 3: Run AWS Setup Script

```bash
# Make the script executable (if not already)
chmod +x setup_aws.sh

# Run the setup script
./setup_aws.sh
```

This script will:
- Create an S3 bucket for storing package documents
- Create an SNS topic for notifications
- Create an IAM user for application access
- Save resource information to `aws_resources.env`

### Step 4: Create RDS PostgreSQL Instance

RDS instances take 10-15 minutes to create. Run:

```bash
aws rds create-db-instance \
  --db-instance-identifier courier-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password 'YourSecurePassword123!' \
  --allocated-storage 20 \
  --publicly-accessible \
  --db-name courier_db \
  --backup-retention-period 0 \
  --region us-east-1
```

**Important:** Replace `YourSecurePassword123!` with a strong password.

### Step 5: Wait for RDS to be Available

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier courier-db

# Wait until "DBInstanceStatus" is "available" (takes 10-15 minutes)
```

### Step 6: Get RDS Endpoint

Once RDS is available, get the endpoint:

```bash
aws rds describe-db-instances \
  --db-instance-identifier courier-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

Save this endpoint - you'll need it for configuration.

### Step 7: Configure Application for AWS

Create or update `.env` file:

```bash
cat > .env <<EOF
# Database Configuration
DB_TYPE=postgres
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=courier_db
DB_USER=admin
DB_PASSWORD=YourSecurePassword123!

# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
SNS_TOPIC_ARN=arn:aws:sns:region:account:courier-delivery
EOF
```

Replace the values with your actual AWS resource information.

### Step 8: Verify SES Email (Optional)

To send emails via SES, verify your email address:

```bash
aws ses verify-email-identity --email-address your-email@example.com --region us-east-1
```

Check your email and click the verification link.

### Step 9: Test the Application

```bash
# Start the application
python3 app.py

# In another terminal, test the health endpoint
curl http://localhost:5000/api/health
```

### Step 10: Test Database Connection

Test if the application can connect to RDS:

```bash
# Set environment variables
export DB_TYPE=postgres
export DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=courier_db
export DB_USER=admin
export DB_PASSWORD=YourSecurePassword123!

# Test database connection
python3 -c "from db_config import get_db_connection, init_db; init_db(); print('RDS connection successful!')"
```

## Troubleshooting

### RDS Connection Issues

1. **Check Security Groups**: Ensure your RDS security group allows inbound connections on port 5432 from your IP
2. **Check Public Accessibility**: Verify RDS is set to publicly accessible
3. **Check Credentials**: Verify DB_USER and DB_PASSWORD are correct

### S3 Access Issues

1. **Check IAM Permissions**: Ensure your IAM user/role has S3 permissions
2. **Check Bucket Name**: Verify S3_BUCKET environment variable is set correctly

### SNS/SES Issues

1. **Check Region**: Ensure AWS_REGION matches where resources were created
2. **Check ARNs**: Verify SNS_TOPIC_ARN is correct
3. **SES Verification**: Ensure email addresses are verified in SES

## Cost Considerations

- **RDS db.t3.micro**: ~$15/month (free tier eligible for first year)
- **S3**: Pay per GB stored (~$0.023/GB/month)
- **SNS**: First 1 million requests free, then $0.50 per million
- **SES**: First 62,000 emails free per month

## Cleanup (When Done Testing)

To avoid charges, delete AWS resources:

```bash
# Delete RDS instance
aws rds delete-db-instance \
  --db-instance-identifier courier-db \
  --skip-final-snapshot

# Delete S3 bucket (first empty it)
aws s3 rm s3://your-bucket-name --recursive
aws s3 rb s3://your-bucket-name

# Delete SNS topic
aws sns delete-topic --topic-arn your-topic-arn

# Delete IAM user (optional)
aws iam delete-user --user-name courier-app-user
```

