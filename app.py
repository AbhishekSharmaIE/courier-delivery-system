from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import uuid
from datetime import datetime
import jwt
import os
from delivery_optimizer import Location, DistanceCalculator, PricingEngine
from db_config import get_db_connection, init_db
from aws_services import S3Service, SNSService, SESService
from geocoder import geocode_ireland_address

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'quick-secret-123'

# Initialize database (SQLite or PostgreSQL based on DB_TYPE env var)
init_db()

# Helper function
def get_db():
    return get_db_connection()

def execute_db_query(conn, query, params=None):
    """Execute query with proper parameter placeholders"""
    cursor = conn.cursor()
    
    # Convert ? to %s for PostgreSQL
    if os.getenv('DB_TYPE') == 'postgres':
        query = query.replace('?', '%s')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor

# 1. REGISTER
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    user_id = str(uuid.uuid4())
    
    conn = get_db()
    cursor = execute_db_query(conn, 'INSERT INTO users VALUES (?, ?, ?, ?, ?)',
                 (user_id, data['email'], data['password'], 
                  data['name'], data['role']))
    conn.commit()
    conn.close()
    
    token = jwt.encode({'user_id': user_id}, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token, 'user_id': user_id})

# 2. LOGIN
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cursor = execute_db_query(conn, 'SELECT * FROM users WHERE email=? AND password=?',
                       (data['email'], data['password']))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Convert to dict for PostgreSQL compatibility
        if hasattr(user, 'keys'):
            user = dict(user)
        token = jwt.encode({'user_id': user['id']}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user_id': user['id']})
    return jsonify({'error': 'Invalid credentials'}), 401

# 3. CREATE PACKAGE
@app.route('/api/packages', methods=['POST'])
def create_package():
    data = request.json
    
    # Get addresses
    pickup_address = data.get('pickup_address', '')
    delivery_address = data.get('recipient_address', '')
    
    # Convert addresses to coordinates (Ireland geocoding)
    pickup_lat, pickup_lon = geocode_ireland_address(pickup_address)
    delivery_lat, delivery_lon = geocode_ireland_address(delivery_address)
    
    # If coordinates are provided, use them (for backward compatibility)
    if 'pickup_lat' in data and 'pickup_lon' in data:
        pickup_lat = data['pickup_lat']
        pickup_lon = data['pickup_lon']
    if 'delivery_lat' in data and 'delivery_lon' in data:
        delivery_lat = data['delivery_lat']
        delivery_lon = data['delivery_lon']
    
    # Calculate distance using custom library
    pickup = Location(pickup_lat, pickup_lon, pickup_address)
    delivery = Location(delivery_lat, delivery_lon, delivery_address)
    distance = DistanceCalculator.calculate(pickup, delivery)
    
    # Calculate price using custom library
    pricing = PricingEngine()
    price = pricing.calculate(distance, data.get('weight_kg', 1.0))
    
    package_id = str(uuid.uuid4())
    tracking_id = f"TRK{uuid.uuid4().hex[:8].upper()}"
    
    recipient_email = data.get('recipient_email', '')
    
    conn = get_db()
    # Insert with email and driver_id (NULL initially)
    # Column order: id, tracking_id, sender_id, recipient_name, recipient_email, 
    #               recipient_address, pickup_address, status, distance, price, driver_id, created_at
    execute_db_query(conn, 'INSERT INTO packages (id, tracking_id, sender_id, recipient_name, recipient_email, recipient_address, pickup_address, status, distance, price, driver_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 (package_id, tracking_id, data.get('sender_id', 'guest'),
                  data['recipient_name'], recipient_email, data['recipient_address'],
                  data['pickup_address'], 'pending', distance, price, None,
                  datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Send email notification if email provided
    if recipient_email:
        try:
            SESService.send_package_created_email(
                tracking_id, data['recipient_name'], recipient_email,
                data['recipient_address'], distance, price
            )
        except Exception as e:
            print(f"Email notification error: {e}")
    
    # Send SNS notification
    try:
        SNSService.notify_package_status(tracking_id, 'pending', recipient_email)
    except Exception as e:
        print(f"SNS notification error: {e}")
    
    return jsonify({
        'package_id': package_id,
        'tracking_id': tracking_id,
        'distance_km': distance,
        'estimated_price': price,
        'status': 'pending',
        'email_sent': bool(recipient_email)
    }), 201

# 4. TRACK PACKAGE
@app.route('/api/packages/<tracking_id>', methods=['GET'])
def track_package(tracking_id):
    conn = get_db()
    # Use explicit column names
    cursor = execute_db_query(conn, '''
        SELECT id, tracking_id, sender_id, recipient_name, recipient_email, 
               recipient_address, pickup_address, status, distance, price, driver_id, created_at
        FROM packages WHERE tracking_id=?
    ''', (tracking_id,))
    package = cursor.fetchone()
    conn.close()
    
    if package:
        # Convert to dict for PostgreSQL/SQLite compatibility
        if hasattr(package, 'keys'):
            package = dict(package)
        elif isinstance(package, tuple):
            # Column order: id, tracking_id, sender_id, recipient_name, recipient_email, 
            #               recipient_address, pickup_address, status, distance, price, driver_id, created_at
            package = {
                'id': package[0],
                'tracking_id': package[1],
                'sender_id': package[2],
                'recipient_name': package[3],
                'recipient_email': package[4] if len(package) > 4 and package[4] else '',
                'recipient_address': package[5] if len(package) > 5 else '',
                'pickup_address': package[6] if len(package) > 6 else '',
                'status': package[7] if len(package) > 7 else '',
                'distance': package[8] if len(package) > 8 else 0,
                'price': package[9] if len(package) > 9 else 0,
                'driver_id': package[10] if len(package) > 10 else None,
                'created_at': package[11] if len(package) > 11 else ''
            }
        return jsonify(package)
    return jsonify({'error': 'Not found'}), 404

# 5. LIST PACKAGES
@app.route('/api/packages', methods=['GET'])
def list_packages():
    conn = get_db()
    # Use explicit column names to ensure correct order
    cursor = execute_db_query(conn, '''
        SELECT id, tracking_id, sender_id, recipient_name, recipient_email, 
               recipient_address, pickup_address, status, distance, price, driver_id, created_at
        FROM packages ORDER BY created_at DESC LIMIT 10
    ''')
    packages = cursor.fetchall()
    conn.close()
    # Convert to dict for PostgreSQL compatibility
    result = []
    for p in packages:
        if hasattr(p, 'keys'):
            result.append(dict(p))
        elif isinstance(p, tuple):
            # Column order: id, tracking_id, sender_id, recipient_name, recipient_email, 
            #               recipient_address, pickup_address, status, distance, price, driver_id, created_at
            result.append({
                'id': p[0],
                'tracking_id': p[1],
                'sender_id': p[2],
                'recipient_name': p[3],
                'recipient_email': p[4] if len(p) > 4 and p[4] else '',
                'recipient_address': p[5] if len(p) > 5 else '',
                'pickup_address': p[6] if len(p) > 6 else '',
                'status': p[7] if len(p) > 7 else '',
                'distance': p[8] if len(p) > 8 else 0,
                'price': p[9] if len(p) > 9 else 0,
                'driver_id': p[10] if len(p) > 10 else None,
                'created_at': p[11] if len(p) > 11 else ''
            })
        else:
            result.append(p)
    return jsonify(result)

# 6. UPDATE STATUS
@app.route('/api/packages/<package_id>/status', methods=['PUT'])
def update_status(package_id):
    data = request.json
    new_status = data['status']
    
    conn = get_db()
    # Get package info for notification
    cursor = execute_db_query(conn, 'SELECT * FROM packages WHERE id=?', (package_id,))
    package = cursor.fetchone()
    
    execute_db_query(conn, 'UPDATE packages SET status=? WHERE id=?',
                 (new_status, package_id))
    conn.commit()
    conn.close()
    
    # Send notifications if package found
    if package:
        if hasattr(package, 'keys'):
            package = dict(package)
        elif isinstance(package, tuple):
            # Handle tuple from PostgreSQL
            package = {
                'id': package[0],
                'tracking_id': package[1],
                'sender_id': package[2],
                'recipient_name': package[3],
                'recipient_email': package[4] if len(package) > 4 else '',
                'recipient_address': package[5] if len(package) > 5 else '',
                'pickup_address': package[6] if len(package) > 6 else '',
                'status': package[7] if len(package) > 7 else '',
                'distance': package[8] if len(package) > 8 else 0,
                'price': package[9] if len(package) > 9 else 0,
                'driver_id': package[10] if len(package) > 10 else None,
                'created_at': package[11] if len(package) > 11 else ''
            }
        
        tracking_id = package.get('tracking_id', '')
        recipient_email = package.get('recipient_email', '')
        recipient_name = package.get('recipient_name', 'Customer')
        recipient_address = package.get('recipient_address', '')
        
        # Send email notification
        if recipient_email:
            try:
                SESService.send_status_update_email(
                    tracking_id, new_status, recipient_name, 
                    recipient_email, recipient_address
                )
            except Exception as e:
                print(f"Email notification error: {e}")
        
        # Send SNS notification
        try:
            SNSService.notify_package_status(tracking_id, new_status, recipient_email or 'customer@example.com')
        except Exception as e:
            print(f"SNS notification error: {e}")
    
    return jsonify({'success': True, 'status': new_status})

# 7. ASSIGN DRIVER
@app.route('/api/deliveries/accept/<package_id>', methods=['POST'])
def accept_delivery(package_id):
    data = request.json
    driver_id = data.get('driver_id', '')
    driver_name = data.get('driver_name', 'Driver')
    
    delivery_id = str(uuid.uuid4())
    
    conn = get_db()
    # Get package info before updating
    cursor = execute_db_query(conn, 'SELECT * FROM packages WHERE id=?', (package_id,))
    package = cursor.fetchone()
    
    execute_db_query(conn, 'INSERT INTO deliveries VALUES (?, ?, ?, ?, ?)',
                 (delivery_id, package_id, driver_id,
                  'accepted', datetime.now().isoformat()))
    execute_db_query(conn, 'UPDATE packages SET status=?, driver_id=? WHERE id=?',
                 ('assigned', driver_id, package_id))
    conn.commit()
    conn.close()
    
    # Send email notification
    if package:
        if hasattr(package, 'keys'):
            package = dict(package)
        elif isinstance(package, tuple):
            package = {
                'tracking_id': package[1],
                'recipient_name': package[3],
                'recipient_email': package[4] if len(package) > 4 else ''
            }
        
        recipient_email = package.get('recipient_email', '')
        if recipient_email:
            try:
                SESService.send_driver_assigned_email(
                    package.get('tracking_id', ''),
                    package.get('recipient_name', 'Customer'),
                    recipient_email,
                    driver_name
                )
            except Exception as e:
                print(f"Email notification error: {e}")
    
    return jsonify({'delivery_id': delivery_id, 'status': 'assigned'})

# 8. UPLOAD FILE TO S3
@app.route('/api/packages/<package_id>/upload', methods=['POST'])
def upload_package_file(package_id):
    """Upload file/document for a package to S3"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Read file content
    file_content = file.read()
    file_name = f"{package_id}_{file.filename}"
    
    # Upload to S3
    s3_url = S3Service.upload_file(file_content, file_name, file.content_type)
    
    if s3_url:
        return jsonify({
            'success': True,
            'file_url': s3_url,
            'file_name': file_name
        }), 200
    else:
        return jsonify({'error': 'Failed to upload to S3'}), 500

# 9. GET S3 FILE URL
@app.route('/api/packages/<package_id>/files/<file_name>', methods=['GET'])
def get_package_file_url(package_id, file_name):
    """Get presigned URL for package file"""
    url = S3Service.get_file_url(file_name)
    if url:
        return jsonify({'file_url': url}), 200
    else:
        return jsonify({'error': 'File not found'}), 404

# Serve UI
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# 10. DASHBOARD STATISTICS
@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    conn = get_db()
    
    # Total packages
    cursor = execute_db_query(conn, 'SELECT COUNT(*) FROM packages')
    total_packages = cursor.fetchone()[0] if cursor.fetchone() else 0
    cursor = execute_db_query(conn, 'SELECT COUNT(*) FROM packages')
    total = cursor.fetchone()
    total_packages = total[0] if total else 0
    
    # Packages by status
    cursor = execute_db_query(conn, 'SELECT status, COUNT(*) FROM packages GROUP BY status')
    status_counts = {}
    for row in cursor.fetchall():
        status = row[0] if isinstance(row, tuple) else row['status']
        count = row[1] if isinstance(row, tuple) else row['COUNT(*)']
        status_counts[status] = count
    
    # Total revenue
    cursor = execute_db_query(conn, 'SELECT SUM(price) FROM packages')
    total_revenue = cursor.fetchone()[0] if cursor.fetchone() else 0
    cursor = execute_db_query(conn, 'SELECT SUM(price) FROM packages')
    revenue = cursor.fetchone()
    total_revenue = float(revenue[0]) if revenue and revenue[0] else 0.0
    
    # Average distance
    cursor = execute_db_query(conn, 'SELECT AVG(distance) FROM packages')
    avg_distance = cursor.fetchone()[0] if cursor.fetchone() else 0
    cursor = execute_db_query(conn, 'SELECT AVG(distance) FROM packages')
    avg_dist = cursor.fetchone()
    avg_distance = float(avg_dist[0]) if avg_dist and avg_dist[0] else 0.0
    
    conn.close()
    
    return jsonify({
        'total_packages': total_packages,
        'status_counts': status_counts,
        'total_revenue': round(total_revenue, 2),
        'average_distance': round(avg_distance, 2)
    })

# 11. GET PACKAGES BY STATUS
@app.route('/api/packages/status/<status>', methods=['GET'])
def get_packages_by_status(status):
    conn = get_db()
    cursor = execute_db_query(conn, 'SELECT * FROM packages WHERE status=? ORDER BY created_at DESC', (status,))
    packages = cursor.fetchall()
    conn.close()
    
    result = []
    for p in packages:
        if hasattr(p, 'keys'):
            result.append(dict(p))
        elif isinstance(p, tuple):
            result.append({
                'id': p[0],
                'tracking_id': p[1],
                'sender_id': p[2],
                'recipient_name': p[3],
                'recipient_email': p[4] if len(p) > 4 else '',
                'recipient_address': p[5] if len(p) > 5 else '',
                'pickup_address': p[6] if len(p) > 6 else '',
                'status': p[7] if len(p) > 7 else '',
                'distance': p[8] if len(p) > 8 else 0,
                'price': p[9] if len(p) > 9 else 0,
                'driver_id': p[10] if len(p) > 10 else None,
                'created_at': p[11] if len(p) > 11 else ''
            })
        else:
            result.append(p)
    return jsonify(result)

# 12. UPDATE PACKAGE (Full Update)
@app.route('/api/packages/<package_id>', methods=['PUT'])
def update_package(package_id):
    data = request.json
    
    conn = get_db()
    # Get existing package
    cursor = execute_db_query(conn, 'SELECT * FROM packages WHERE id=?', (package_id,))
    package = cursor.fetchone()
    
    if not package:
        conn.close()
        return jsonify({'error': 'Package not found'}), 404
    
    # Update package fields
    recipient_name = data.get('recipient_name', package[3] if isinstance(package, tuple) else package.get('recipient_name'))
    recipient_email = data.get('recipient_email', package[4] if isinstance(package, tuple) and len(package) > 4 else package.get('recipient_email', ''))
    recipient_address = data.get('recipient_address', package[5] if isinstance(package, tuple) and len(package) > 5 else package.get('recipient_address'))
    pickup_address = data.get('pickup_address', package[6] if isinstance(package, tuple) and len(package) > 6 else package.get('pickup_address'))
    weight_kg = data.get('weight_kg', 1.0)
    
    # Recalculate distance and price if addresses changed
    if 'recipient_address' in data or 'pickup_address' in data:
        pickup_lat, pickup_lon = geocode_ireland_address(pickup_address)
        delivery_lat, delivery_lon = geocode_ireland_address(recipient_address)
        pickup = Location(pickup_lat, pickup_lon, pickup_address)
        delivery = Location(delivery_lat, delivery_lon, recipient_address)
        distance = DistanceCalculator.calculate(pickup, delivery)
        pricing = PricingEngine()
        price = pricing.calculate(distance, weight_kg)
    else:
        distance = package[8] if isinstance(package, tuple) and len(package) > 8 else package.get('distance', 0)
        price = package[9] if isinstance(package, tuple) and len(package) > 9 else package.get('price', 0)
    
    # Update package
    execute_db_query(conn, '''
        UPDATE packages 
        SET recipient_name=?, recipient_email=?, recipient_address=?, 
            pickup_address=?, distance=?, price=?
        WHERE id=?
    ''', (recipient_name, recipient_email, recipient_address, 
          pickup_address, distance, price, package_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Package updated successfully',
        'package_id': package_id,
        'distance_km': distance,
        'price': price
    })

# 13. DELETE PACKAGE
@app.route('/api/packages/<package_id>', methods=['DELETE'])
def delete_package(package_id):
    conn = get_db()
    
    # Check if package exists
    cursor = execute_db_query(conn, 'SELECT * FROM packages WHERE id=?', (package_id,))
    package = cursor.fetchone()
    
    if not package:
        conn.close()
        return jsonify({'error': 'Package not found'}), 404
    
    # Get tracking_id for notification
    if isinstance(package, tuple):
        tracking_id = package[1]
        recipient_email = package[4] if len(package) > 4 else ''
    else:
        tracking_id = package.get('tracking_id', '')
        recipient_email = package.get('recipient_email', '')
    
    # Delete package
    execute_db_query(conn, 'DELETE FROM packages WHERE id=?', (package_id,))
    conn.commit()
    conn.close()
    
    # Send notification email if email exists
    if recipient_email:
        try:
            SESService.send_email(
                recipient_email,
                f'Package {tracking_id} Deleted',
                f'<p>Your package with tracking ID {tracking_id} has been deleted from the system.</p>',
                f'Your package with tracking ID {tracking_id} has been deleted from the system.'
            )
        except Exception as e:
            print(f"Email notification error: {e}")
    
    return jsonify({
        'success': True,
        'message': 'Package deleted successfully',
        'tracking_id': tracking_id
    })

# 14. GET SINGLE PACKAGE BY ID
@app.route('/api/packages/id/<package_id>', methods=['GET'])
def get_package_by_id(package_id):
    conn = get_db()
    # Use explicit column names
    cursor = execute_db_query(conn, '''
        SELECT id, tracking_id, sender_id, recipient_name, recipient_email, 
               recipient_address, pickup_address, status, distance, price, driver_id, created_at
        FROM packages WHERE id=?
    ''', (package_id,))
    package = cursor.fetchone()
    conn.close()
    
    if package:
        if hasattr(package, 'keys'):
            package = dict(package)
        elif isinstance(package, tuple):
            # Column order: id, tracking_id, sender_id, recipient_name, recipient_email, 
            #               recipient_address, pickup_address, status, distance, price, driver_id, created_at
            package = {
                'id': package[0],
                'tracking_id': package[1],
                'sender_id': package[2],
                'recipient_name': package[3],
                'recipient_email': package[4] if len(package) > 4 and package[4] else '',
                'recipient_address': package[5] if len(package) > 5 else '',
                'pickup_address': package[6] if len(package) > 6 else '',
                'status': package[7] if len(package) > 7 else '',
                'distance': package[8] if len(package) > 8 else 0,
                'price': package[9] if len(package) > 9 else 0,
                'driver_id': package[10] if len(package) > 10 else None,
                'created_at': package[11] if len(package) > 11 else ''
            }
        return jsonify(package)
    return jsonify({'error': 'Not found'}), 404

# HEALTH CHECK
@app.route('/api/health', methods=['GET'])
def health():
    # Check S3 configuration
    s3_bucket = os.getenv('S3_BUCKET', '')
    s3_status = 'configured' if s3_bucket else 'not configured'
    
    # Check database connection
    try:
        conn = get_db()
        conn.close()
        db_status = 'connected'
    except:
        db_status = 'disconnected'
    
    return jsonify({
        'status': 'ok', 
        'services': ['RDS', 'S3', 'SNS', 'SES', 'CloudWatch', 'IAM'],
        's3_status': s3_status,
        's3_bucket': s3_bucket if s3_bucket else 'not configured',
        'database_status': db_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)