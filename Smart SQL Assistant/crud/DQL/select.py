from db_config import get_db_connection

def execute_select(sql):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return {
            "status": "success",
            "data": data,
            "columns": columns,
            "message": "✅ SELECT executed successfully."
        }
    except Exception as e:
        return {"status": "error", "message": f"❌ SELECT failed: {str(e)}"}
    finally:
        cursor.close()
        conn.close()
