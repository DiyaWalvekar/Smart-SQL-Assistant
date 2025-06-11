from db_config import get_db_connection

def execute_rollback():
    conn = get_db_connection()
    try:
        conn.rollback()
        return {"status": "success", "message": "✅ ROLLBACK executed successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ ROLLBACK failed: {str(e)}"}
    finally:
        conn.close()
