from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, Admin, Course, Student
from enrollment import enroll_bp
from attendance import attendance_bp
from view_attendance import view_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

with app.app_context():
    db.create_all()

    if not Admin.query.first():
        db.session.add(
            Admin(
                username="admin",
                password=generate_password_hash("admin123")
            )
        )

    courses = [
        "Data Science and Analytics",
        "Artificial Intelligence",
        "Full Stack Developer"
    ]

    for c in courses:
        if not Course.query.filter_by(name=c).first():
            db.session.add(Course(name=c))

    db.session.commit()

# ---------- ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Admin.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/dashboard")
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        students_count=Student.query.count(),
        courses_count=Course.query.count()
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# ---------- BLUEPRINTS ----------
app.register_blueprint(enroll_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(view_bp)

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)
