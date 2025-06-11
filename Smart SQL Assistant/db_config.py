import pymysql

def get_db_connection():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="Diya@2004",  # your MySQL password
        database="voice_sql",
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

def clean_sql_query(query):
    # Remove triple backticks and language tags
    query = query.strip()
    if query.startswith("```"):
        query = query.replace("```sql", "").replace("```", "").strip()
    return query

def execute_sql_query(query):
    try:
        query = clean_sql_query(query)
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            if query.lower().startswith("select"):
                result = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                return result, columns
            else:
                conn.commit()  # For UPDATE, DELETE, and INSERT
                return {"message": "Query executed successfully!"}, None
    except Exception as e:
        print("❌ SQL Execution Error:", e)
        return None, None
