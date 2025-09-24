from flask import Flask, request, render_template, redirect, url_for
import sqlite3, os

app = Flask(__name__)
app.secret_key = "your-secret-key"
DB_FILE = "signup.db"

# ================= 数据库 =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        limit_num INTEGER NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS signups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        classroom TEXT NOT NULL,
        class_name TEXT NOT NULL,
        class_id INTEGER NOT NULL
    )''')
    conn.commit()
    conn.close()

init_db()

# ================= 报名页面 =================
@app.route("/", methods=["GET", "POST"])
def signup():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, limit_num FROM classes")
    classes = []
    for cid, name, limit_num in c.fetchall():
        c.execute("SELECT COUNT(*) FROM signups WHERE class_id=?", (cid,))
        count = c.fetchone()[0]
        if count < limit_num:
            classes.append((cid, name, count, limit_num))
    conn.close()

    if request.method == "POST":
        student_name = request.form["student_name"]
        classroom = request.form["classroom"]
        class_id = int(request.form["class_id"])

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # 检查是否已报名
        c.execute("SELECT * FROM signups WHERE student_name=?", (student_name,))
        if c.fetchone():
            conn.close()
            return render_template("signup.html", classes=classes, error="你已经报名过一个兴趣班了")

        # 检查是否满额
        c.execute("SELECT name, limit_num FROM classes WHERE id=?", (class_id,))
        class_info = c.fetchone()
        if not class_info:
            conn.close()
            return "兴趣班不存在"
        class_name, limit_num = class_info
        c.execute("SELECT COUNT(*) FROM signups WHERE class_id=?", (class_id,))
        count = c.fetchone()[0]
        if count >= limit_num:
            conn.close()
            return render_template("signup.html", classes=classes, error="该兴趣班已满额")

        # 插入报名
        c.execute("INSERT INTO signups (student_name, classroom, class_name, class_id) VALUES (?, ?, ?, ?)",
                  (student_name, classroom, class_name, class_id))
        conn.commit()
        conn.close()

        return render_template("signup_success.html", student_name=student_name, class_name=class_name)

    return render_template("signup.html", classes=classes, error=None)

# ================= 管理员后台 =================
@app.route("/admin")
def admin():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, limit_num FROM classes")
    rows = c.fetchall()
    classes = []
    for cid, name, limit_num in rows:
        c.execute("SELECT COUNT(*) FROM signups WHERE class_id=?", (cid,))
        count = c.fetchone()[0]
        classes.append((cid, name, limit_num, count))
    conn.close()
    return render_template("admin.html", classes=classes)

@app.route("/admin/add", methods=["GET", "POST"])
def add_class():
    if request.method == "POST":
        name = request.form["name"]
        limit_num = int(request.form["limit_num"])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO classes (name, limit_num) VALUES (?, ?)", (name, limit_num))
        conn.commit()
        conn.close()
        return redirect(url_for("admin"))
    return render_template("add_class.html")

@app.route("/admin/delete/<int:cid>")
def delete_class(cid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM classes WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
