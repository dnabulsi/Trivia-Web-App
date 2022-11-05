import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(category, difficulty):
    """Look up quote for symbol."""
    # Contact API

    try:
        if category == "mixed" and difficulty != "mixed":
            url = f"https://the-trivia-api.com/api/questions?limit=1&difficulty={difficulty}"
            response = requests.get(url)
            response.raise_for_status()

        elif category != "mixed" and difficulty == "mixed":
            url = f"https://the-trivia-api.com/api/questions?categories={category}&limit=1"
            response = requests.get(url)
            response.raise_for_status()

        elif category != "mixed" and difficulty != "mixed":
            url = f"https://the-trivia-api.com/api/questions?categories={category}&limit=1&difficulty={difficulty}"
            response = requests.get(url)
            response.raise_for_status()

        else:
            url = f"https://the-trivia-api.com/api/questions?limit=1"
            response = requests.get(url)
            response.raise_for_status()

    except requests.exceptions.HTTPError as error:
        raise SystemExit(error)

    # Parse response
    try:
        quote = response.json()
        return {
            "category": quote[0]["category"],
            "id": quote[0]["id"],
            "correct_answer": quote[0]["correctAnswer"],
            "incorrect_answers": quote[0]["incorrectAnswers"],
            "question": quote[0]["question"],
            "difficulty": quote[0]["difficulty"]
        }

    except (KeyError, TypeError, ValueError):
        return None