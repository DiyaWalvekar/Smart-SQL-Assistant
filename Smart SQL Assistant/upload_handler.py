import pandas as pd
from db_config import get_db_connection

def clean_dataframe(df):
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Drop rows that are completely empty
    df.dropna(how='all', inplace=True)

    # Fill NaN values with empty strings
    df.fillna('', inplace=True)

    # Strip whitespace from all string cells
    for col in df.columns:
        df[col] = df[col].apply(lambda x: str(x).strip() if isinstance(x, str) else str(x))
    
    return df

def store_file_to_db(file_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Read file
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)

    # Clean the dataframe
    df = clean_dataframe(df)

    # Create table if not exists with all columns as TEXT
    cols = ', '.join([f"{col} TEXT" for col in df.columns])
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})")

    # Prepare insert query
    columns = ', '.join([f"{col}" for col in df.columns])
    placeholders = ', '.join(['%s'] * len(df.columns))
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    # Insert each row
    for _, row in df.iterrows():
        values = tuple(row)
        cursor.execute(insert_query, values)

    conn.commit()
    cursor.close()
    conn.close()
