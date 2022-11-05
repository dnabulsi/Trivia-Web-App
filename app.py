import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup
from random import shuffle
from jinja2 import Environment
import random

app = Flask(__name__)

CATEGORIES = {
    'mixed': "Mixed",
    'arts_and_literature': "Arts & Literature",
    'film_and_tv': "Film & TV",
    'food_and_drink': "Food & Drink",
    'general_knowledge': "General Knowledge",
    'geography': "Geography",
    'history': "History",
    'music': "Music",
    'science': "Science",
    'society_and_culture': "Society & Culture",
    'sport_and_leisure': "Sport & Leisure"
}

categories_keys = list(CATEGORIES.keys())
categories_values = list(CATEGORIES.values())

DIFFICULTY = {
    'mixed': "Mixed",
    'easy': "Easy",
    'medium': "Medium",
    'hard': "Hard"
}

difficulty_keys = list(DIFFICULTY.keys())
difficulty_values = list(DIFFICULTY.values())

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
@login_required
def index():
    """Show main page"""

    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif not request.form.get("confirmation"):
            return apology("must confirm password", 400)

        elif not (request.form.get("password") == request.form.get("confirmation")):
            return apology("must match password and confirmation", 400)

        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("must choose a unique username", 400)

        else:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"),
                       (generate_password_hash(request.form.get("password"), method='plain', salt_length=8)))

        return render_template("login.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("must check username/password", 400)

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """Confirm user's username and password"""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("old_password"):
            return apology("must provide old password", 400)

        elif not request.form.get("new_password"):
            return apology("must provide new password", 400)

        elif not request.form.get("confirmation"):
            return apology("must confirm new password", 400)

        if not db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("must check username", 400)

        database_dict = db.execute("SELECT username, hash FROM users WHERE username = ?", request.form.get("username"))
        database_username = database_dict[0]["username"]
        database_hash = database_dict[0]["hash"]

        if check_password_hash(database_hash, request.form.get("old_password")) == False:
            return apology("must check password", 400)

        elif not (request.form.get("new_password") == request.form.get("confirmation")):
            return apology("must match new password and confirmation", 400)

        else:

            db.execute("UPDATE users SET hash = ? WHERE username = ?", (generate_password_hash(
                       request.form.get("new_password"), method='plain', salt_length=8)), request.form.get("username"))

            return render_template("success.html")

    return render_template("changepassword.html")


@app.route("/about")
def about():
    """Show information about the project"""

    return render_template("about.html")


@app.route("/highscores", methods=["GET", "POST"])
@login_required
def highscores():
    """Show highscores of games"""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)
        username = request.form.get("username")

        rows = db.execute("SELECT * FROM highscores WHERE userID = (SELECT id FROM users WHERE username = ?) ORDER BY score DESC",
                          username)

        return render_template("highscores.html", rows=rows)

    return render_template("highscores.html")


@app.route("/history", methods=["GET", "POST"])
@login_required
def history():
    """Display history page"""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)
        username = request.form.get("username")

        rows = db.execute("SELECT * FROM history WHERE userID = (SELECT id FROM users WHERE username = ?) ORDER BY time DESC", username)

        return render_template("history.html", rows=rows)

    return render_template("history.html")


@app.route("/success", methods=["GET", "POST"])
@login_required
def success():
    """Display success page"""


    if request.method == "POST":

        return redirect("/")

    return render_template("success.html")


@app.route("/newgame", methods=["GET", "POST"])
@login_required
def newgame():
    """Initialize a new game"""

    if request.method == "POST":

        if not request.form.get("category"):
            return apology("must select category", 400)
        global proper_category
        proper_category = request.form.get("category")
        position_category = categories_values.index(request.form.get("category"))
        global category
        category = categories_keys[position_category]

        if not request.form.get("difficulty"):
            return apology("must select difficulty", 400)
        global proper_difficulty
        proper_difficulty = request.form.get("difficulty")
        position_difficulty = difficulty_values.index(request.form.get("difficulty"))
        global difficulty
        difficulty = difficulty_keys[position_difficulty]

        global lookup_results
        lookup_results = lookup(category, difficulty)
        if lookup_results == None:
            return apology("must fix lookup", 400)

        proper_difficulty = [lookup_results["difficulty"]][0]
        proper_category = [lookup_results["category"]][0]

        answers = [lookup_results["correct_answer"]]
        global correct
        correct = [lookup_results["correct_answer"]][0]

        for row in lookup_results["incorrect_answers"]:
            answers.append(row)
        random.shuffle(answers)

        global points
        points = 0

        global question_number
        question_number = 1

        return render_template("game.html", lookup_results=lookup_results, points=points, question_number=question_number, answers=answers, correct=correct, proper_category=proper_category, proper_difficulty=proper_difficulty.capitalize())

    return render_template("newgame.html", categories=CATEGORIES, difficulty=DIFFICULTY)


@app.route("/game", methods=["GET", "POST"])
@login_required
def game():
    """Process the current game"""

    if request.method == "POST":
        global correct
        if correct == request.form.get("answer"):
            global points
            points = points + 1
            global question_number
            question_number = question_number + 1

            lookup_results = lookup(category, difficulty)
            if lookup_results == None:
                return apology("must fix lookup", 404)

            global proper_difficulty
            proper_difficulty = [lookup_results["difficulty"]][0]
            global proper_category
            proper_category = [lookup_results["category"]][0]

            answers = [lookup_results["correct_answer"]]
            correct = [lookup_results["correct_answer"]][0]

            for row in lookup_results["incorrect_answers"]:
                answers.append(row)
            random.shuffle(answers)

            return render_template("game.html", lookup_results=lookup_results, points=points, question_number=question_number, answers=answers, correct=correct, proper_category=proper_category, proper_difficulty=proper_difficulty.capitalize())

        else:
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            db.execute("INSERT INTO history (score, time, userID, category, difficulty) VALUES(?, ?, ?, ?, ?)",
                   points, now, session["user_id"], proper_category, proper_difficulty.capitalize())

            if db.execute("SELECT * FROM highscores WHERE category = ? AND difficulty = ? AND userID = ?",
                proper_category, proper_difficulty.capitalize(), session["user_id"]):

                score_dict = db.execute("SELECT * FROM highscores WHERE category = ? AND difficulty = ? AND userID = ?",
                proper_category, proper_difficulty.capitalize(), session["user_id"])
                oldHS = score_dict[0]["score"]

                if oldHS < points:
                    db.execute("UPDATE highscores SET score = ? WHERE category = ? AND difficulty = ? AND userID = ?",
                    points, proper_category, proper_difficulty.capitalize(), session["user_id"])

            else:
                db.execute("INSERT INTO highscores (score, time, userID, category, difficulty) VALUES(?, ?, ?, ?, ?)", points, now, session["user_id"], proper_category, proper_difficulty.capitalize())

            return render_template("gameover.html", points=points, proper_category=proper_category, proper_difficulty=proper_difficulty, question_number = question_number)

    return redirect("/newgame")


@app.route("/gameover", methods=["GET", "POST"])
@login_required
def gameover():
    """Display gameover page"""

    if request.method == "POST":
        if request.form['button'] == 'highscores':
            return redirect("/highscores")

        return redirect("/newgame")

    return redirect("/newgame")


@app.route("/howtoplay")
@login_required
def howtoplay():
    """Display how to play page"""

    return render_template("howtoplay.html")