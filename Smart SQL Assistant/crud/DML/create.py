# crud/create.py
from db_config import get_db_connection

def execute_create(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return {"status": "success", "message": "✅ Record inserted successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error inserting record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
