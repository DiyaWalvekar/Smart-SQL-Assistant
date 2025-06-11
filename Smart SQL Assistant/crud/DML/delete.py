# crud/delete.py
from db_config import get_db_connection

def execute_delete(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return {"status": "success", "message": "✅ Record deleted successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Error deleting record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
