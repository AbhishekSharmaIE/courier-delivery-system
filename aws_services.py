"""AWS Services Integration - S3, SNS, SES"""
import os
import boto3
from botocore.exceptions import ClientError

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', '')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', '')
SES_FROM_EMAIL = os.getenv('SES_FROM_EMAIL', 'abhishekmsharma21@gmail.com')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION) if S3_BUCKET else None
sns_client = boto3.client('sns', region_name=AWS_REGION) if SNS_TOPIC_ARN else None
ses_client = boto3.client('ses', region_name=AWS_REGION)

class S3Service:
    """S3 service for storing package documents/images"""
    
    @staticmethod
    def upload_file(file_content, file_name, content_type='application/octet-stream'):
        """Upload file to S3"""
        if not s3_client or not S3_BUCKET:
            return None
        
        try:
            key = f"packages/{file_name}"
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=file_content,
                ContentType=content_type
            )
            url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
            return url
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
            return None
    
    @staticmethod
    def get_file_url(file_name):
        """Get presigned URL for file"""
        if not s3_client or not S3_BUCKET:
            return None
        
        try:
            key = f"packages/{file_name}"
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': key},
                ExpiresIn=3600
            )
            return url
        except ClientError as e:
            print(f"Error generating S3 URL: {e}")
            return None

class SNSService:
    """SNS service for notifications"""
    
    @staticmethod
    def publish_notification(message, subject="Courier Delivery Update"):
        """Publish notification to SNS topic"""
        if not sns_client or not SNS_TOPIC_ARN:
            print("SNS not configured - skipping notification")
            return False
        
        try:
            response = sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Message=message,
                Subject=subject
            )
            print(f"SNS notification sent: {response.get('MessageId')}")
            return response.get('MessageId') is not None
        except ClientError as e:
            print(f"Error publishing to SNS: {e}")
            return False
    
    @staticmethod
    def notify_package_status(tracking_id, status, recipient_email):
        """Send package status notification via SNS"""
        message = f"""Package Tracking Update

Tracking ID: {tracking_id}
Status: {status}

Your package status has been updated.
"""
        return SNSService.publish_notification(
            message,
            f"Package {tracking_id} - Status Update"
        )

class SESService:
    """SES service for sending emails"""
    
    @staticmethod
    def send_email(to_email, subject, body_html=None, body_text=None, from_email=None):
        """Send email using SES"""
        if not from_email:
            from_email = SES_FROM_EMAIL
        
        # If no HTML provided, use text as both
        if not body_html:
            body_html = body_text.replace('\n', '<br>') if body_text else ''
        if not body_text:
            body_text = body_html.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
        
        try:
            message = {
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                    'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                }
            }
            
            response = ses_client.send_email(
                Source=from_email,
                Destination={'ToAddresses': [to_email]},
                Message=message
            )
            print(f"Email sent successfully to {to_email}: {response.get('MessageId')}")
            return response.get('MessageId') is not None
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            if error_code == 'MessageRejected':
                print(f"Email not sent - address not verified: {to_email}")
                print(f"  Note: Verify email in SES: aws ses verify-email-identity --email-address {to_email}")
            elif 'Email address not verified' in error_message or 'not verified' in error_message.lower():
                print(f"Email not sent - address not verified: {to_email}")
                print(f"  Note: Check your email inbox and click the verification link from AWS SES")
            else:
                print(f"Error sending email via SES: {error_code} - {error_message}")
            return False
        except Exception as e:
            print(f"Unexpected error sending email: {e}")
            return False
    
    @staticmethod
    def send_package_created_email(tracking_id, recipient_name, recipient_email, 
                                   recipient_address, distance, price):
        """Send email when package is created"""
        subject = f"📦 Package Created - Tracking ID: {tracking_id}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">Package Created Successfully!</h2>
                <p>Dear {recipient_name},</p>
                <p>Your package has been created and is ready for delivery.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Tracking ID:</strong> {tracking_id}</p>
                    <p><strong>Delivery Address:</strong> {recipient_address}</p>
                    <p><strong>Distance:</strong> {distance} km</p>
                    <p><strong>Estimated Price:</strong> €{price}</p>
                </div>
                
                <p>You can track your package using the tracking ID above.</p>
                <p>Thank you for using our courier service!</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""Package Created Successfully!

Dear {recipient_name},

Your package has been created and is ready for delivery.

Tracking ID: {tracking_id}
Delivery Address: {recipient_address}
Distance: {distance} km
Estimated Price: €{price}

You can track your package using the tracking ID above.
Thank you for using our courier service!
"""
        
        return SESService.send_email(recipient_email, subject, body_html, body_text)
    
    @staticmethod
    def send_status_update_email(tracking_id, status, recipient_name, recipient_email, 
                                 recipient_address=None):
        """Send email when package status is updated"""
        status_messages = {
            'pending': 'Your package is pending and awaiting assignment.',
            'assigned': 'A driver has been assigned to your package.',
            'in_transit': 'Your package is on the way!',
            'out_for_delivery': 'Your package is out for delivery today!',
            'delivered': 'Your package has been delivered successfully!',
            'cancelled': 'Your package has been cancelled.'
        }
        
        status_message = status_messages.get(status.lower(), 'Your package status has been updated.')
        
        subject = f"📦 Package Update - {tracking_id} - {status.upper()}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">Package Status Update</h2>
                <p>Dear {recipient_name},</p>
                <p>{status_message}</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Tracking ID:</strong> {tracking_id}</p>
                    <p><strong>Current Status:</strong> <span style="color: #667eea; font-weight: bold;">{status.upper()}</span></p>
                    {f'<p><strong>Delivery Address:</strong> {recipient_address}</p>' if recipient_address else ''}
                </div>
                
                <p>You can track your package using the tracking ID above.</p>
                <p>Thank you for using our courier service!</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""Package Status Update

Dear {recipient_name},

{status_message}

Tracking ID: {tracking_id}
Current Status: {status.upper()}
{f'Delivery Address: {recipient_address}' if recipient_address else ''}

You can track your package using the tracking ID above.
Thank you for using our courier service!
"""
        
        return SESService.send_email(recipient_email, subject, body_html, body_text)
    
    @staticmethod
    def send_driver_assigned_email(tracking_id, recipient_name, recipient_email, driver_name=None):
        """Send email when driver is assigned"""
        subject = f"🚚 Driver Assigned - Package {tracking_id}"
        
        driver_info = f"Driver: {driver_name}" if driver_name else "A driver has been assigned"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">Driver Assigned</h2>
                <p>Dear {recipient_name},</p>
                <p>Great news! {driver_info} to deliver your package.</p>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Tracking ID:</strong> {tracking_id}</p>
                    <p><strong>Status:</strong> <span style="color: #667eea; font-weight: bold;">ASSIGNED</span></p>
                </div>
                
                <p>Your package will be picked up soon!</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""Driver Assigned

Dear {recipient_name},

Great news! {driver_info} to deliver your package.

Tracking ID: {tracking_id}
Status: ASSIGNED

Your package will be picked up soon!
"""
        
        return SESService.send_email(recipient_email, subject, body_html, body_text)
