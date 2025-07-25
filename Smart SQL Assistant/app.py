from flask import Flask, request, jsonify, render_template, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import os
from authlib.integrations.flask_client import OAuth
from flask import url_for
from nlp_utils import match_intent, expand_query
# DDL operations
from crud.DDL.create_table import execute_create_table
from crud.DDL.alter_table import execute_alter_table
from crud.DDL.drop_table import execute_drop_table

# DQL operation
from crud.DQL.select import execute_select

# TCL operations
from crud.TCL.commit import execute_commit
from crud.TCL.rollback import execute_rollback
from crud.TCL.savepoint import execute_savepoint


# DCL operations
from crud.DCL.grant import execute_grant
from crud.DCL.revoke import execute_revoke

# Import your custom modules
from upload_handler import store_file_to_db
from voice_sql_handler import handle_text_or_voice_query
from db_config import execute_sql_query
from get_db_connection import get_mysql_connection

from utils import (
    generate_chart_data,
    generate_visualization,
    speak_text,
    convert_to_html_table,
    generate_insights
)

# CRUD operations
from crud.DML.create import execute_create
from crud.DML.update import execute_update
from crud.DML.delete import execute_delete
query_history = []


# Initialize app
app = Flask(__name__)
app.secret_key = 'secret_key'

CORS(app)

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='your-client-id',
    client_secret='your-client-secrect',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
    },

)

import secrets

@app.route('/login/google')
def login_google():
    # Generate a secure random nonce and save in session
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce

    redirect_uri = url_for('authorize_google', _external=True)
    # Pass nonce param to authorize_redirect so Google includes it in ID token
    return google.authorize_redirect(redirect_uri, nonce=nonce)


@app.route('/login/google/callback')
def authorize_google():
    # Step 1: Get token after Google OAuth callback
    token = google.authorize_access_token()

    # Step 2: Retrieve nonce from session for validation
    nonce = session.get('nonce')
    if not nonce:
        flash('Invalid login attempt: missing nonce.', 'error')
        return redirect('/login')

    # Step 3: Parse ID token to get user info (email, name, etc.)
    user_info = google.parse_id_token(token, nonce=nonce)
    user_email = user_info['email']

    # Step 4: Connect to your MySQL DB and check if user exists
    conn = get_mysql_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
    user = cursor.fetchone()

    if not user:
        # User doesn't exist - create new user with random password hash
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (user_email, generate_password_hash(os.urandom(16).hex()))
        )
        conn.commit()

    cursor.close()
    conn.close()

    # Step 5: Store user email in session and flash message
    session['user'] = user_email
    flash('Logged in successfully using Google!', 'success')

    # Step 6: Redirect user to your index/home page
    return redirect('/index')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# Setup upload folder
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Home page with Login and Signup buttons
@app.route('/')
def home():
    return render_template('home.html')  # home.html should have login and signup links in header

@app.route('/index')
def index():
    if 'user' not in session:
        return redirect('/login')
    return render_template('index.html')  # your main logged-in page

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No file provided"}), 400

    try:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        table_name = os.path.splitext(filename)[0].lower().replace(' ', '_')
        store_file_to_db(filepath, table_name)

        return jsonify({"message": "File uploaded successfully", "table": table_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Query endpoint (text/voice)
@app.route('/query', methods=['POST'])
def query():
    mode = request.form.get('mode')  # 'text' or 'voice'
    text = request.form.get('text')  # SQL or voice input

    try:
        # Convert input to SQL
        if mode == 'text':
            sql = handle_text_or_voice_query("text", text)
        elif mode == 'voice':
            sql = handle_text_or_voice_query(mode, text)
        else:
            raise ValueError("Invalid mode. Use 'text' or 'voice'.")

        print("Executing SQL:", sql)

        # Execute the SQL query
        data, columns = execute_sql_query(sql)

        if not data and not columns:
            raise ValueError("The query executed but returned no results.")

        # Save query to history if user is logged in
        user_email = session.get('user')
        if user_email:
            try:
                conn = get_mysql_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO query_history (user_email, query) VALUES (%s, %s)",
                    (user_email, sql)
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print("Error saving query history:", e)

        # Generate UI components
        table_html = convert_to_html_table(data, columns)
        chart_json = generate_chart_data(data, columns)
        chart_image = generate_visualization(data, columns)
        insights = generate_insights(data, columns)
        chart_type = detect_chart_type(columns, data)

        # Speak insights (optional)
        try:
            speak_text(insights)
        except Exception as e:
            print(f"Text-to-speech failed: {e}")

        # Send response
        return jsonify({
            "sql": sql,
            "table": table_html,
            "chart": chart_json,
            "chart_image": chart_image,
            "chart_type": chart_type,
            "insights": insights
        })

    except Exception as e:
        print(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500

    
# Create endpoint
@app.route('/DML/create', methods=['POST'])
def create():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_create(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update endpoint
@app.route('/DML/update', methods=['POST'])
def update():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_update(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_history')
def get_history():
    user_email = session.get('user')  # ensure the user is logged in
    if not user_email:
        return jsonify([])

    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query, timestamp FROM query_history WHERE user_email = %s ORDER BY timestamp DESC",
            (user_email,)
        )
        history = cursor.fetchall()  # Already a list of dictionaries

        cursor.close()
        conn.close()
        return jsonify(history)

    except Exception as e:
        print("Error fetching history:", e)
        return jsonify([])



# Delete endpoint
@app.route('/DML/delete', methods=['POST'])
def delete():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_delete(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def detect_chart_type(columns, data):
    if not columns or not data:
        return "bar"

    if len(columns) >= 2:
        x, y = data[0][columns[0]], data[0][columns[1]]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return "scatter"

    if isinstance(data[0][columns[0]], str):
        if len(columns) == 1:
            return "pie"
        elif len(columns) == 2 and isinstance(data[0][columns[1]], (int, float)) and len(data) <= 10:
            return "pie"

    if len(columns) == 2 and isinstance(data[0][columns[0]], (int, float)) and isinstance(data[0][columns[1]], (int, float)):
        return "line"

    if len(columns) == 1 and isinstance(data[0][columns[0]], (int, float)):
        return "histogram"

    return "bar"

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password_input):
            session['user'] = user['email']
            return redirect('/index')
        else:
            flash("Invalid email or password", "error")

    return render_template("login.html")

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Signup successful. Please log in.", "success")
            return redirect('/login')
        except:
            flash("Email already exists or error occurred.", "error")

    return render_template("signup.html")

# Dashboard page (optional)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return f"<h1>Welcome, {session['user']}!</h1><a href='/logout'>Logout</a>"

import pandas as pd

@app.route('/export', methods=['POST'])
def export():
    sql_query = request.form.get('sql_query')
    try:
        data, columns = execute_sql_query(sql_query)
        df = pd.DataFrame(data, columns=columns)
        export_path = os.path.join("downloads", "query_results.csv")
        df.to_csv(export_path, index=False)
        return jsonify({"download_link": f"/{export_path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/DQL/select', methods=['POST'])
def select():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_select(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/DDL/create_table', methods=['POST'])
def ddl_create_table():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_create_table(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/DDL/alter_table', methods=['POST'])
def ddl_alter_table():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_alter_table(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/DDL/drop_table', methods=['POST'])
def ddl_drop_table():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_drop_table(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/TCL/commit', methods=['POST'])
def tcl_commit():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_commit(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/TCL/rollback', methods=['POST'])
def tcl_rollback():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_rollback(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/DCL/grant', methods=['POST'])
def dcl_grant():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_grant(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/DCL/revoke', methods=['POST'])
def dcl_revoke():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_revoke(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/TCL/savepoint', methods=['POST'])
def tcl_savepoint():
    sql_query = request.form.get('sql_query')
    try:
        result = execute_savepoint(sql_query)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/suggest', methods=['POST'])
def suggest():
    query = request.form.get('query', '')

    # 1. Get intent and confidence (NumPy float32)
    intent, confidence = match_intent(query)

    # 2. Expand query (may contain lists)
    expansion = expand_query(query)

    # 3. Convert to serializable types
    confidence = float(confidence)          # cast to Python float
    # If expansion is nested lists, flatten and cast:
    flat_expansion = []
    for item in expansion:
        if isinstance(item, (list, tuple)):
            for sub in item:
                flat_expansion.append(str(sub))
        else:
            flat_expansion.append(str(item))

    return jsonify({
        "intent": intent,
        "confidence": confidence,
        "expansion": flat_expansion
    })

if __name__ == '__main__':
    app.run(debug=True)
/*from flask import Flask, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
import os, secrets, pandas as pd

from get_db_connection import get_mysql_connection
from upload_handler import store_file_to_db
from voice_sql_handler import handle_text_or_voice_query
from utils import (
    convert_to_html_table,
    generate_chart_data,
    generate_visualization,
    speak_text,
    generate_insights
)

# CRUD + NLP modules
from crud.DML.create import execute_create
from crud.DML.update import execute_update
from crud.DML.delete import execute_delete
from crud.DQL.select import execute_select
from crud.DDL.create_table import execute_create_table
from crud.DDL.alter_table import execute_alter_table
from crud.DDL.drop_table import execute_drop_table
from crud.TCL.commit import execute_commit
from crud.TCL.rollback import execute_rollback
from crud.TCL.savepoint import execute_savepoint
from crud.DCL.grant import execute_grant
from crud.DCL.revoke import execute_revoke
from nlp_utils import match_intent, expand_query

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='your-client-id',
    client_secret='your-client-secret',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/api/v1/auth/google')
def login_google():
    session['nonce'] = secrets.token_urlsafe(16)
    return google.authorize_redirect(url_for('authorize_google', _external=True), nonce=session['nonce'])

@app.route('/api/v1/auth/google/callback')
def authorize_google():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, nonce=session.get('nonce'))
    email = user_info['email']
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, generate_password_hash(os.urandom(16).hex())))
        conn.commit()
    session['user'] = email
    cursor.close(); conn.close()
    return redirect('/dashboard')

@app.route('/api/v1/auth/logout')
def logout():
    session.pop('user', None)
    return jsonify({"message": "Logged out"})

# --------------------
# 📦 Core REST Endpoints
# --------------------

@app.route('/api/v1/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No file provided"}), 400
    try:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        table_name = os.path.splitext(filename)[0].lower().replace(' ', '_')
        store_file_to_db(filepath, table_name)
        return jsonify({"message": "File uploaded", "table": table_name})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/query', methods=['POST'])
def query():
    mode = request.form.get('mode')
    input_text = request.form.get('text')
    try:
        sql = handle_text_or_voice_query(mode, input_text)
        data, columns = execute_select(sql)
        if not data: raise ValueError("No results")
        if session.get('user'):
            conn = get_mysql_connection(); cursor = conn.cursor()
            cursor.execute("INSERT INTO query_history (user_email, query) VALUES (%s, %s)", (session['user'], sql))
            conn.commit(); cursor.close(); conn.close()
        chart_json = generate_chart_data(data, columns)
        chart_img = generate_visualization(data, columns)
        table_html = convert_to_html_table(data, columns)
        insights = generate_insights(data, columns)
        try: speak_text(insights)
        except: pass
        return jsonify({
            "sql": sql,
            "table": table_html,
            "chart": chart_json,
            "chart_image": chart_img,
            "insights": insights
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/history', methods=['GET'])
def get_history():
    if not session.get('user'):
        return jsonify([])
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT query, timestamp FROM query_history WHERE user_email = %s ORDER BY timestamp DESC", (session['user'],))
        data = cursor.fetchall(); cursor.close(); conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify([])

@app.route('/api/v1/export', methods=['POST'])
def export():
    sql = request.form.get('sql_query')
    try:
        data, cols = execute_select(sql)
        df = pd.DataFrame(data, columns=cols)
        path = os.path.join("downloads", "query_results.csv")
        df.to_csv(path, index=False)
        return jsonify({"download_link": f"/{path}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/suggest', methods=['POST'])
def suggest():
    query = request.form.get('query', '')
    intent, confidence = match_intent(query)
    expansion = expand_query(query)
    return jsonify({
        "intent": intent,
        "confidence": float(confidence),
        "expansion": [str(i) for sub in expansion for i in (sub if isinstance(sub, (list, tuple)) else [sub])]
    })

# --------------------
# 🧠 SQL Operation Endpoints (Modular)
# --------------------

@app.route('/api/v1/dml/create', methods=['POST'])     # POST = Create
def create(): return _exec_sql_op(execute_create)

@app.route('/api/v1/dml/update', methods=['PUT'])       # PUT = Update
def update(): return _exec_sql_op(execute_update)

@app.route('/api/v1/dml/delete', methods=['DELETE'])    # DELETE = Delete
def delete(): return _exec_sql_op(execute_delete)

@app.route('/api/v1/dql/select', methods=['POST'])      # POST = Custom Select
def select(): return _exec_sql_op(execute_select)

@app.route('/api/v1/ddl/create_table', methods=['POST'])
def ddl_create_table(): return _exec_sql_op(execute_create_table)

@app.route('/api/v1/ddl/alter_table', methods=['POST'])
def ddl_alter_table(): return _exec_sql_op(execute_alter_table)

@app.route('/api/v1/ddl/drop_table', methods=['DELETE'])
def ddl_drop_table(): return _exec_sql_op(execute_drop_table)

@app.route('/api/v1/tcl/commit', methods=['POST'])
def tcl_commit(): return _exec_sql_op(execute_commit)

@app.route('/api/v1/tcl/rollback', methods=['POST'])
def tcl_rollback(): return _exec_sql_op(execute_rollback)

@app.route('/api/v1/tcl/savepoint', methods=['POST'])
def tcl_savepoint(): return _exec_sql_op(execute_savepoint)

@app.route('/api/v1/dcl/grant', methods=['POST'])
def dcl_grant(): return _exec_sql_op(execute_grant)

@app.route('/api/v1/dcl/revoke', methods=['POST'])
def dcl_revoke(): return _exec_sql_op(execute_revoke)

# --------------------
# 📦 Utility Function to Wrap SQL Functions
# --------------------
def _exec_sql_op(func):
    try:
        sql = request.form.get('sql_query')
        return jsonify(func(sql))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --------------------
# ▶ Run the Server
# --------------------
if __name__ == '__main__':
    app.run(debug=True)
*/
