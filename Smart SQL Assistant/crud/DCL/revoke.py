from db_config import get_db_connection

def execute_revoke(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        conn.commit()
        return {"status": "success", "message": "✅ REVOKE executed successfully."}
    except Exception as e:
        return {"status": "error", "message": f"❌ REVOKE failed: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
