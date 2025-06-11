# crud/update.py
from db_config import get_db_connection

def execute_update(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return {"status": "success", "message": "✅ Record updated successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error updating record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
