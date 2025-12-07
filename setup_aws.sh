#!/bin/bash
# AWS Setup Script for Courier Delivery System
# Make sure AWS CLI is configured with credentials before running this script

set -e  # Exit on error

echo "=== AWS Courier Delivery System Setup ==="
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS CLI is not configured or credentials are invalid."
    echo "Please run: aws configure"
    echo "Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
    exit 1
fi

echo "✓ AWS credentials verified"
echo ""

# Get AWS account ID and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

# 1. Create S3 bucket
echo "1. Creating S3 bucket..."
BUCKET_NAME="courier-delivery-$(date +%s)"
if aws s3 mb "s3://$BUCKET_NAME" --region "$AWS_REGION" 2>&1; then
    echo "✓ S3 bucket created: $BUCKET_NAME"
    echo "S3_BUCKET=$BUCKET_NAME" >> aws_resources.env
else
    echo "✗ Failed to create S3 bucket"
    exit 1
fi
echo ""

# 2. Create SNS topic
echo "2. Creating SNS topic..."
SNS_ARN=$(aws sns create-topic --name courier-delivery --region "$AWS_REGION" --query 'TopicArn' --output text 2>/dev/null || echo "")
if [ -n "$SNS_ARN" ]; then
    echo "✓ SNS topic created: $SNS_ARN"
    echo "SNS_TOPIC_ARN=$SNS_ARN" >> aws_resources.env
else
    echo "✗ Failed to create SNS topic"
    exit 1
fi
echo ""

# 3. Create IAM user (optional - for application access)
echo "3. Creating IAM user for application..."
IAM_USER_NAME="courier-app-user"
if aws iam get-user --user-name "$IAM_USER_NAME" &>/dev/null; then
    echo "✓ IAM user already exists: $IAM_USER_NAME"
else
    if aws iam create-user --user-name "$IAM_USER_NAME" &>/dev/null; then
        echo "✓ IAM user created: $IAM_USER_NAME"
        
        # Attach policies for S3, SNS, SES access
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" \
            --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess &>/dev/null || true
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" \
            --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess &>/dev/null || true
        aws iam attach-user-policy --user-name "$IAM_USER_NAME" \
            --policy-arn arn:aws:iam::aws:policy/AmazonSESFullAccess &>/dev/null || true
        
        echo "✓ Policies attached to IAM user"
    else
        echo "⚠ Warning: Could not create IAM user (may need admin permissions)"
    fi
fi
echo ""

# 4. Note about SES email verification
echo "4. SES Email Verification:"
echo "   To use SES, you need to verify your email address:"
echo "   aws ses verify-email-identity --email-address your-email@example.com --region $AWS_REGION"
echo "   Then check your email and click the verification link."
echo ""

# 5. RDS will be created separately (takes 10-15 minutes)
echo "5. RDS PostgreSQL Database:"
echo "   RDS instances take 10-15 minutes to create."
echo "   Run the following command to create RDS:"
echo ""
echo "   aws rds create-db-instance \\"
echo "     --db-instance-identifier courier-db \\"
echo "     --db-instance-class db.t3.micro \\"
echo "     --engine postgres \\"
echo "     --master-username admin \\"
echo "     --master-user-password 'YourSecurePassword123!' \\"
echo "     --allocated-storage 20 \\"
echo "     --publicly-accessible \\"
echo "     --db-name courier_db \\"
echo "     --backup-retention-period 0 \\"
echo "     --region $AWS_REGION"
echo ""

echo "=== Setup Summary ==="
echo "Created resources saved to: aws_resources.env"
if [ -f aws_resources.env ]; then
    cat aws_resources.env
fi
echo ""
echo "Next steps:"
echo "1. Create RDS instance (command shown above)"
echo "2. Wait for RDS to be available (check: aws rds describe-db-instances)"
echo "3. Get RDS endpoint and update app.py configuration"
echo "4. Verify SES email address"
echo ""

