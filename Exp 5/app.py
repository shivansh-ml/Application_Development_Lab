from flask import Flask, request, jsonify, render_template
from flask_mysqldb import MySQL
from google import genai

app = Flask(__name__)

# ==============================
# GEMINI API KEY (PUT YOUR KEY)
# ==============================

client = genai.Client(
    api_key="AIzaSyBqMO-_utw075_6GFHf6oUm2LFaRYwL50c"
)

# ==============================
# MYSQL CONFIG
# ==============================

# MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Shivansh@123"   # change if needed
app.config["MYSQL_DB"] = "flaskdb"

mysql = MySQL(app)
# ==============================
# SAFE SQL EXECUTION
# ==============================

def execute_safe_sql(query):
    query_upper = query.strip().upper()

    # Allow only SELECT
    if not query_upper.startswith("SELECT"):
        return "Error: Only SELECT queries allowed."

    # Block password column access
    if "PASSWORD" in query_upper:
        return "Error: Access to password column is restricted."

    try:
        cur = mysql.connection.cursor()
        cur.execute(query)

        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()
        return results

    except Exception as e:
        return f"DB Error: {str(e)}"


# ==============================
# ROUTES
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_question = data.get('question')

    try:
        # STEP 1: Generate SQL
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are a MySQL expert.

Convert the user question into SQL.

Database schema:
users(id PRIMARY KEY, username, password)
grades(user_id FOREIGN KEY references users(id), marks)

Return ONLY SQL query.
Question: {user_question}
"""
        )

        generated_sql = response.text.strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        # STEP 2: Execute SQL
        db_results = execute_safe_sql(generated_sql)

        # STEP 3: Human explanation
        summary_resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
User asked: {user_question}

SQL result: {db_results}

Explain the answer in simple words.
"""
        )

        return jsonify({
            "sql": generated_sql,
            "results": db_results,
            "summary": summary_resp.text
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# ==============================
# RUN SERVER
# ==============================

if __name__ == '__main__':
    app.run(debug=True)