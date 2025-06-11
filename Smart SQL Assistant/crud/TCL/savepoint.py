from db_config import get_db_connection

def execute_savepoint(savepoint_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SAVEPOINT {savepoint_name}")
        conn.commit()
        return {"status": "success", "message": f"✅ SAVEPOINT '{savepoint_name}' created."}
    except Exception as e:
        return {"status": "error", "message": f"❌ SAVEPOINT creation failed: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
