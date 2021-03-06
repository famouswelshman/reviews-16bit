import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env
  
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

placeholder_image = "{{ url_for('static', filename='images/Logo.png') }}"


@app.route("/")
@app.route("/home")
def get_reviews():
    
    reviews = mongo.db.reviews.find()
    return render_template("home.html", reviews=reviews)


@app.route("/register", methods=["GET", "POST"])
def register():
    ''' Checks that the username is already registered in MongoDB '''
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration was Successful")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    ''' user can login via page and database checks
    exisiting username and password matches '''
    if request.method == "POST":

        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Checks hash password is a match
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Hi, {}".format(
                    request.form.get("username")))
                return redirect(url_for(
                        "profile", username=session["user"]))
            else:
                # invalid password entered
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username does not exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    ''' Gets the session username from MongoDB '''
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    ''' Removes the user from the session cookies '''
    flash("You have successfully logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/create_review", methods=["GET", "POST"])
def create_review():
    ''' Open the create review page and enables user to add a review '''
    if session.get('user') is None:
        return redirect(url_for("login"))
    if request.method == "POST":
        review = {
            "console_name": request.form.get("console_name"),
            "game_name": request.form.get("game_name"),
            "review_title": request.form.get("review_title"),
            "review_input": request.form.get("review_input"),
            "img_url": request.form.get("img_url"),
            "created_by": session["user"]
        }
        mongo.db.reviews.insert_one(review)
        flash("Review Successfully Added")
        return redirect(url_for("get_reviews"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("create_review.html", categories=categories)


@app.route("/open_review/<review_id>", methods=["GET"])
def open_review(review_id):
    ''' Opens the selected review in review page'''
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("open_review.html", review=review)


@app.route("/search", methods=["GET", "POST"])
def search():
    ''' Search function based on text search across
    all fields in Mongo DB returns result'''
    query = request.form.get("query")
    reviews = list(mongo.db.reviews.find({"$text": {"$search": query}}))
    return render_template("home.html", reviews=reviews)


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    ''' Open the relevant review as user and edit and update to MongoDB'''
    if session.get('user') is None:
        return redirect(url_for("login"))
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        return redirect(url_for("login"))
    if review['created_by'] != session["user"]:
        return redirect(url_for("login"))
    if request.method == "POST":
        submit = {
            "console_name": request.form.get("console_name"),
            "game_name": request.form.get("game_name"),
            "review_title": request.form.get("review_title"),
            "review_input": request.form.get("review_input"),
            "img_url": request.form.get("img_url"),
            "created_by": session["user"]
        }
        mongo.db.reviews.update({"_id": ObjectId(review_id)}, submit)
        flash("Review Successfully Updated")
        return redirect(url_for("get_reviews"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
        "edit_review.html", review=review, categories=categories)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    ''' User can access their specific review and be able to delete from DB '''
    mongo.db.reviews.remove({"_id": ObjectId(review_id)})
    flash("Review Successfully Deleted")
    return redirect(url_for("get_reviews"))


@app.route("/scripts_js")
def scripts_js():
    ''' Javascript Link '''
    render_template("/js/scripts.js")


@app.route("/user_reviews/")
def user_reviews():
    ''' User can access all review data which is relevant to them as user '''
    reviews = mongo.db.reviews.find()
    return render_template("user_reviews.html", reviews=reviews)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
