# db_connection.py
import pymysql

def get_mysql_connection():
    """Function to get a database connection"""
    conn = pymysql.connect(
        host='localhost',  # Replace with your database host
        user='root',       # Replace with your database user
        password='Diya@2004',  # Replace with your database password
        db='users',  # Replace with your database name
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn
