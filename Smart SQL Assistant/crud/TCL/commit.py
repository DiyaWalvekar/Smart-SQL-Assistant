from db_config import get_db_connection

def execute_commit():
    conn = get_db_connection()
    try:
        conn.commit()
        return {"status": "success", "message": "✅ COMMIT executed successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ COMMIT failed: {str(e)}"}
    finally:
        conn.close()
