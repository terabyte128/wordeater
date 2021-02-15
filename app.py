import re
import random
import sqlite3

from flask import request, Flask, g, render_template, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "somethingreallysecret"

DATABASE = "db.sqlite3"


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.before_first_request
def create_tables():
    db = get_db()
    c = db.cursor()
    c.execute(
        """
            CREATE TABLE IF NOT EXISTS words (
            id integer primary key,
            word text unique
            )
        """
    )
    db.commit()


@app.route("/word", methods=("POST",))
def add_word():
    db = get_db()
    c = db.cursor()

    word = request.form["word"].lower().strip()
    if len(word) == 0:
        flash("Your word cannot be empty. Try again?")
        return redirect(url_for("index"))

    if not len(word) <= 30:
        flash("Your word cannot be longer than 30 characters. Try again?")
        return redirect(url_for("index"))

    if not re.fullmatch(r"[a-z\s]+", word):
        flash("Your word can only contain letters or spaces. Try again?")
        return redirect(url_for("index"))

    try:
        c.execute("INSERT INTO words (word) VALUES (?)", (word,))
        db.commit()
    except sqlite3.IntegrityError:
        pass

    flash("Your word has been submitted! Why not submit another?")
    return redirect(url_for("index"))


@app.route("/")
def index():
    db = get_db()
    c = db.cursor()

    c.execute("select count(*) from words")
    count = c.fetchone()[0]

    approx = random.randint(count - 5, count + 5)

    params = {"count": approx}
    return render_template("index.html", **params)


@app.route("/supersecretdontlookhere")
def get_words():
    db = get_db()
    c = db.cursor()

    c.execute("select word from words")
    words = map(lambda x: x[0], c.fetchall())

    return (",".join(words), 200)


@app.route("/nukeit", methods=("DELETE",))
def delete_words():
    if request.form.get("really", "") != "yes":
        return ("not allowed", 401)

    db = get_db()
    c = db.cursor()

    c.execute("delete from words")

    db.commit()

    return ("", 204)
