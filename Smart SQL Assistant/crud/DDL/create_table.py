from db_config import get_db_connection

def execute_create_table(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return {"status": "success", "message": "✅ Table created successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ CREATE TABLE failed: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
