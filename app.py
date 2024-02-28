import os
import base64
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from dotenv import load_dotenv
load_dotenv()

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///blog.db")
print(os.getenv("DB"))



@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        # Get location from the form data
        location = request.form.get("location")

        # Ensure location is not blank
        if not location:
            return apology("must provide location", 400)

        # Obtain information from the database
        rows = db.execute("""SELECT users.username, images.ImageData,
                                articles.location, articles.title, articles.text,
                                articles.date, articles.id, profile.profile_photo
                          FROM articles
                          LEFT JOIN images ON articles.id = images.article_id
                          LEFT JOIN users ON articles.user_id = users.id
                          LEFT JOIN profile ON profile.user_id = articles.user_id
                          WHERE articles.location=?
                          ORDER BY articles.date DESC, articles.time DESC""", location)

        for row in rows:
            #Article's photo
            if row["ImageData"] is not None:
                row["ImageData"] = base64.b64encode(row["ImageData"]).decode('utf-8')
            else:
                # Set a default image
                row["ImageData"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA... (base64-encoded default image)"

            #User's photo
            row['default_photo'] = True
            if row["profile_photo"]:
                # Check if the list is not empty
                row["profile_photo"] = base64.b64encode(row["profile_photo"]).decode('utf-8')
                row['default_photo'] = False
            else:
                # Handle the case where no profile is found for the specified user_id
                row["profile_photo"] = url_for('static', filename='img/standard_avatar.jpg')

        return render_template("search.html", rows=rows, location=row['location'])

    else:
        # Obtain information from the database
        rows = db.execute("""SELECT users.username, images.ImageData,
                               articles.location, articles.title, articles.text,
                               articles.date, articles.id, profile.profile_photo
                            FROM articles
                            LEFT JOIN images ON articles.id = images.article_id
                            LEFT JOIN users ON articles.user_id = users.id
                            LEFT JOIN profile ON profile.user_id = articles.user_id
                            ORDER BY articles.date DESC, articles.time DESC""")

        for row in rows:
            #Article's photo
            if row["ImageData"] is not None:
                row["ImageData"] = base64.b64encode(row["ImageData"]).decode('utf-8')
            else:
                # Set a default image
                row["ImageData"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA... (base64-encoded default image)"

            #User's photo
            row['default_photo'] = True
            if row["profile_photo"]:
                # Check if the list is not empty
                row["profile_photo"] = base64.b64encode(row["profile_photo"]).decode('utf-8')
                row['default_photo'] = False
            else:
                # Handle the case where no profile is found for the specified user_id
                row["profile_photo"] = url_for('static', filename='img/standard_avatar.jpg')

        return render_template("index.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # Get username and password from the form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not confirmation:
            return apology("must provide confirmation", 400)

        # Ensure password match with confirmation
        if password != confirmation:
            return apology("the passwords do not match", 400)

        # Query database to ensure username isn't already taken
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=username)
        if len(rows) != 0:
            return apology("username is already taken", 400)

        #Saving data in the database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(password))


        id = db.execute("SELECT id FROM users WHERE username=?", username)

        # Remember which user has logged in
        session["user_id"] = id[0]["id"]

        # Create entry in profile table
        db.execute("INSERT INTO profile (user_id, first_name, last_name, birthday, details, profile_photo) VALUES (?,?,?,?,?,?)",
                    session["user_id"], "", "", "", "", "")

        return redirect("/change")

    else:
        session.clear()
        return render_template("register.html")

@app.route("/add_article", methods=["GET", "POST"])
@login_required
def add_article():
    user_id = session["user_id"]
    if request.method == "POST":
        # Get data from the form data
        location = request.form.get("location")
        title = request.form.get("title")
        text = request.form.get("text")
        file = request.files["file"]

        #Ensure location is not blank
        if not location:
            return apology("must provide location", 400)

        #Ensure title is not blank
        if not title:
            return apology("must provide title", 400)

        #Ensure text is not blank
        if not text:
            return apology("must provide text", 400)

        #Ensure file is not blank
        if not file:
            return apology("must provide file", 400)

        # Insert article into the database
        article_id = db.execute("INSERT INTO articles (user_id, location, title, text) VALUES (?, ?, ?, ?)",
                                user_id, location, title, text)

        # Insert image into the database
        file_content = file.read()
        db.execute("INSERT INTO images (user_id, article_id, ImageData) VALUES (?, ?, ?)",
                   user_id, article_id, file_content)

        return redirect("/")

    else:

        return render_template("add_article.html")

@app.route("/profile")
@login_required
def profile():

    # Obtain information from the database
    rows = db.execute("""SELECT users.username, images.ImageData,
                            articles.location, articles.title, articles.text,
                            articles.date, articles.id, profile.profile_photo
                      FROM articles
                      LEFT JOIN images ON articles.id = images.article_id
                      LEFT JOIN users ON articles.user_id = users.id
                      LEFT JOIN profile ON profile.user_id = articles.user_id
                      WHERE users.id=?
                      ORDER BY articles.date DESC, articles.time DESC""", session["user_id"])

    info = db.execute("SELECT * FROM profile WHERE user_id=?", session["user_id"])

    #User's photo
    default_photo = True
    if info[0]["profile_photo"]:
        info[0]["profile_photo"] = base64.b64encode(info[0]["profile_photo"]).decode('utf-8')
        default_photo = False
    else:
        #Set a default image
        info[0]["profile_photo"] = url_for('static', filename='img/standard_avatar.jpg')

    for row in rows:
        #Article's photo
        if row["ImageData"] is not None:
            row["ImageData"] = base64.b64encode(row["ImageData"]).decode('utf-8')
        else:
            # Set a default image
            row["ImageData"] = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA... (base64-encoded default image)"

        #User's photo
        row['default_photo'] = True
        if row["profile_photo"]:
            # Check if the list is not empty
            row["profile_photo"] = base64.b64encode(row["profile_photo"]).decode('utf-8')
            row['default_photo'] = False
        else:
            # Handle the case where no profile is found for the specified user_id
            row["profile_photo"] = url_for('static', filename='img/standard_avatar.jpg')

    return render_template("profile.html", rows=rows, info=info[0], default_photo=default_photo)

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        birthday = request.form.get("birthday")
        details = request.form.get("details")
        file = request.files["file"]

        #Ensure first_name is not blank
        if not first_name:
            return apology("must provide First name", 400)

        #Ensure last_name is not blank
        if not last_name:
            return apology("must provide Last name", 400)

        #Ensure birthday is not blank
        if not birthday:
            return apology("must provide Birthday", 400)

        #Ensure details is not blank
        if not details:
            return apology("must provide Details about you", 400)

        #Ensure file is not blank
        if not file:
            return apology("must provide a file", 400)

        file_content = file.read()

        db.execute("UPDATE profile SET first_name=?, last_name=?, birthday=?, details=?, profile_photo=? WHERE user_id=?",
                first_name, last_name, str(birthday), details, file_content, session["user_id"])

        return redirect("/profile")

    else:
        result = db.execute("SELECT profile_photo FROM profile WHERE user_id=?", session["user_id"])
        default_photo = True
        if result[0]["profile_photo"]:
            # Check if the list is not empty
            profile_photo = base64.b64encode(result[0]["profile_photo"]).decode('utf-8')
            default_photo = False
        else:
            # Handle the case where no profile is found for the specified user_id
            profile_photo = url_for('static', filename='img/standard_avatar.jpg')
        return render_template("change.html", profile_photo=profile_photo, default_photo=default_photo)
