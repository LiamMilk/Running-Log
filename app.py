from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hhh"

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(hours=1)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: 'YYYY-MM-DD'
    miles = db.Column(db.Float, nullable=False)
    time = db.Column(db.String, nullable=False)  # e.g. 30 minutes 45 seconds
    description = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="activities")



users = {}
user_plans = {}

@app.route("/")
def index():
    if 'username' in session: 
        return redirect(url_for("login"))
    else:
        return render_template("index.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("Username is taken, please choose another.")
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account Created. Please log in!")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid Username or Password")
        else:
            session["username"] = username
            flash("Login Successful!")
            return redirect(url_for("view_calendar"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.")
    return redirect(url_for("index"))

@app.route("/calendar")
def view_calendar():
    if "username" not in session:
         return redirect(url_for("login"))
    user = User.query.filter_by(username=session["username"]).first()

    start_date_str = request.args.get("start_date", None)
    if start_date_str:
        week_start = datetime.strptime(start_date_str, "%Y-%m-%d")
    else:
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())

    today = datetime.now()
    current_date = today.strftime('%Y-%m-%d')
    next_week_start = (week_start + timedelta(weeks=1)).strftime('%Y-%m-%d')
    prev_week_start = (week_start - timedelta(weeks=1)).strftime('%Y-%m-%d')
    week_dates = [
        {
            "date": (week_start + timedelta(days=i)).strftime('%Y-%m-%d'),
            "day": (week_start + timedelta(days=i)).strftime('%A'),
        }
        for i in range(7)
    ]
    activities = {a.date: f"{a.miles} miles, {a.time}, {a.description}" for a in user.activities}
    weekly_activities = [a for a in user.activities if week_start <= datetime.strptime(a.date, '%Y-%m-%d') <= (week_start + timedelta(weeks=1))]
    weekly_miles = sum([a.miles for a in weekly_activities])
    return render_template("calendar.html", username=user.username, today=current_date, week_dates=week_dates, activities=activities, next_week_start=next_week_start, prev_week_start=prev_week_start, weekly_miles=weekly_miles)

    
@app.route("/add_activity/", methods=["GET", "POST"])
def add_activity():
    if "username" not in session:
        return redirect(url_for("login"))
    user = User.query.filter_by(username=session["username"]).first()
    if request.method == "POST":
        date = request.form["date"]
        miles = float(request.form["miles"])
        time = request.form["time"]
        description = request.form["description"]

        new_activity = Activity(user_id=user.id, date=date, miles=miles, time=time, description=description)
        db.session.add(new_activity)
        db.session.commit()
        return redirect(url_for("view_calendar"))
    date = request.args.get("date", datetime.now().strftime('%Y-%m-%d'))
    return render_template(url_for("add_activity"), date=date)
        

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)