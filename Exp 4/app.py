from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret"

# MySQL config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Shivansh@123"
app.config["MYSQL_DB"] = "flaskdb"

mysql = MySQL(app)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE username=%s", (u,))
        user = cur.fetchone()

        if user and user[1] == p:
            session["user"] = user[0]
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/signup", methods=["POST"])
def signup():
    u = request.form["username"]
    p = generate_password_hash(request.form["password"])

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)", (u, p))
    mysql.connection.commit()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    cur = mysql.connection.cursor()
    cur.execute("SELECT marks FROM grades WHERE user_id=%s", (session["user"],))
    grade = cur.fetchone()
    return render_template("dashboard.html", grade=grade)

@app.route("/reset", methods=["POST"])
def reset():
    p = generate_password_hash(request.form["password"])
    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s", (p, session["user"]))
    mysql.connection.commit()
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(debug=True)
