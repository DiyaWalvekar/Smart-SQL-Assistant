# 🧠 Smart SQL Assistant

**Smart SQL Assistant** is an intelligent voice- and text-powered tool that turns your natural language into SQL queries and visual insights. It’s designed for both technical and non-technical users to interact with databases using speech or plain English — no SQL knowledge required.

---

## ✨ Key Highlights

- 🔐 **Google Sign-In** for secure user access
- 🗣️ **Voice Queries** using Whisper (OpenAI)
- 💡 **AI-Powered SQL Generation** with Gemini
- 📊 **Auto Charts**: Pie, Bar, and Line Graphs
- 💾 **CSV/Excel Uploads** to MySQL
- 📥 **Result Downloads** as CSV
- 📜 **Query History** saved per user
- 🔈 **Text-to-Speech** output for responses
- 🌍 **Multi-language support** 
- 🛠️ **Performs CRUD operations** like DDL,DML,DQL,TCL,DCL

---

## ⚙️ How to Run Locally

### 🔁 Step 1: Clone This Repo

```bash
git clone https://github.com/yourusername/smart-sql-assistant.git
cd smart-sql-assistant

### 🧪 Step 2: Set Up Virtual Environment

python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)

### 📦 Step 3: Install Python Requirements

pip install -r requirements.txt

### 🔐 Step 4: Add Environment Variables

Create a .env file in the root:
OPENAI_API_KEY=your_openai_key
GOOGLE_CLIENT_ID=your_google_client_id
SECRET_KEY=your_flask_secret_key

### 🛠️ Step 5: Set Up the Database

For MySQL:
mysql -u root -p < schema.sql

### 🚀 Step 6: Run the Server


python run.py
Then open: http://localhost:5000

### 🚧 Upcoming Features
🌐 Language translation for multilingual support
🧠 Voice-driven CRUD operations
📱 Mobile responsive dashboard
🔔 Real-time voice notifications

👨‍💻 Built By
 Diya Walvekar
📧 diyawalvekar4321@gmail.com
🔗 GitHub Profile