"""Database configuration - supports both SQLite (local) and PostgreSQL (AWS RDS)"""
import os
import sqlite3

# Database type: 'sqlite' or 'postgres'
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

# PostgreSQL/RDS configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'courier_db')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def get_db_connection():
    """Get database connection based on DB_TYPE"""
    if DB_TYPE == 'postgres':
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                sslmode='require'
            )
            return conn
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgreSQL. Install with: pip install psycopg2-binary")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    else:
        # SQLite (default)
        conn = sqlite3.connect('courier.db')
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(conn, query, params=None):
    """Execute query with proper parameter placeholders for SQLite or PostgreSQL"""
    cursor = conn.cursor()
    
    # Convert ? to %s for PostgreSQL
    if DB_TYPE == 'postgres':
        query = query.replace('?', '%s')
    
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    
    return cursor

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DB_TYPE == 'postgres':
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT,
                password TEXT,
                name TEXT,
                role TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id TEXT PRIMARY KEY,
                tracking_id TEXT,
                sender_id TEXT,
                recipient_name TEXT,
                recipient_email TEXT,
                recipient_address TEXT,
                pickup_address TEXT,
                status TEXT,
                distance REAL,
                price REAL,
                driver_id TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deliveries (
                id TEXT PRIMARY KEY,
                package_id TEXT,
                driver_id TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
    else:
        # SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users
            (id TEXT PRIMARY KEY, email TEXT, password TEXT, 
             name TEXT, role TEXT)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages
            (id TEXT PRIMARY KEY, tracking_id TEXT, 
             sender_id TEXT, recipient_name TEXT, recipient_email TEXT,
             recipient_address TEXT, pickup_address TEXT, status TEXT, 
             distance REAL, price REAL, driver_id TEXT, created_at TEXT)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deliveries
            (id TEXT PRIMARY KEY, package_id TEXT, driver_id TEXT,
             status TEXT, created_at TEXT)
        ''')
    
    conn.commit()
    conn.close()

