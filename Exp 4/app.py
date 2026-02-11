from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "secret"

# MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Shivansh@123"   # change if needed
app.config["MYSQL_DB"] = "flaskdb"

mysql = MySQL(app)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and user[1] == password:
            session["user_id"] = user[0]
            return redirect("/dashboard")

        return "Invalid Username or Password"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",
                (username, password))
    mysql.connection.commit()

    return redirect("/")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    cur = mysql.connection.cursor()
    cur.execute("SELECT marks FROM grades WHERE user_id=%s",
                (session["user_id"],))
    grade = cur.fetchone()

    return render_template("dashboard.html", grade=grade)


# ---------------- RESET PASSWORD ----------------
@app.route("/reset", methods=["POST"])
def reset():
    if "user_id" not in session:
        return redirect("/")

    new_password = request.form["password"]

    cur = mysql.connection.cursor()
    cur.execute("UPDATE users SET password=%s WHERE id=%s",
                (new_password, session["user_id"]))
    mysql.connection.commit()

    return redirect("/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
