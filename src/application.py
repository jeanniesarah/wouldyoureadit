import os

from flask import Flask, session, render_template, url_for, request, flash, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import login_required

import requests

app = Flask(__name__)

# Check for env variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), pool_size=10, max_overflow=20)
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    """ Default app route """
    
    # Render index.html welcome page
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Request registration details, hash password, check user has not already registered and passwords match, add to user table """
    
    # Error message variable declaration
    error = None
    
    # As soon as user posts registration details from form on register.html run 
    if request.method == "POST":
        
        # Request registration form data values
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        passwordcheck = request.form.get("passwordcheck")
        
        # Hash the given password, salt length will be default value 8 for security 
        hashed_password = generate_password_hash(password, "sha256")
        
        # Check if a user exists with given email address, update error message if so
        if db.execute("SELECT * FROM users WHERE user_email = :email", {"email": email}).rowcount == 1:
            error = 'Oops! This email address is already registered.'
        
        # check if username row exists with given username, update error message if so
        elif db.execute("SELECT * FROM users WHERE user_username = :username", {"username": username}).rowcount == 1:
            error = 'Oops! This username is already in use. Please choose an alternative.'
        
        # check if the password and password confirmation values given by user match, update error message if so
        elif not password == passwordcheck:
            error = 'Oops! Passwords do not match. Please try again.'
        
        # if all error checks succeed then insert user details into the users table and redirect user to login 
        else:
            db.execute("INSERT INTO users (user_email, user_username, user_hashpw) VALUES (:email, :username, :hashed_password)", {"email": email, "username": username, "hashed_password": hashed_password})
            db.commit()
            flash('Success. Registration complete! Please login.')
            return redirect(url_for('login'))
    
    # GET request for register, render registration page with error string if a previous attempt failed
    return render_template("register.html", error=error)
 
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """ Request username and password, check if registered password correct, update session variable """
    
    # Error message variable 
    error = None
    
    # When user posts login details from form on login.html run 
    if request.method == "POST":
        
        # Request login form data values
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Select user hashed password from users table where username matches given username
        user = db.execute("SELECT user_hashpw FROM users WHERE user_username = :username", {"username": username}).fetchone()
        
        # If no user is found or password check failure, update error message
        if user is None or check_password_hash(user.user_hashpw, password) is False:
            error = 'Username or password incorrect. Please try again or register.'
        
        # If checks succeed, update session variable "username" (for later logged in status check) and redirect user to search 
        else:
            session["username"] = username
            return redirect(url_for('search'))
    
    # GET request for login, render the login page with error message if a previous attempt failed
    return render_template("login.html", error=error)
    
    
@app.route("/logout")
@login_required
def logout():
    """ Clear username session variable then render the logout confirmation page """
    
    # Route redirects to login if login_required returns false 
    
    # Update username session variable then render the logged out confirmation page
    session.pop("username", None)
    return render_template("logout.html")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """ Request search value and query books table """
    
    # Route redirects to login if login_required returns false 
    
    # Error message variable declaration
    error = None
    
    # When user posts search value from form on search.html run 
    if request.method == "POST":
        
        # Request search data value from form
        search_value = request.form.get("search_value")
        
        # Add symbols to search value so partial matches can be found
        wild_value = "%" + search_value + "%"

        # Query books table with search value for any matches in the isbn, title or author fields
        results = db.execute("SELECT * FROM books WHERE book_isbn ILIKE :wild_value OR book_title ILIKE :wild_value OR book_author ILIKE :wild_value", {"wild_value": wild_value}).fetchall()

        # If number of rows of results is 0 then update error message
        if len(results) == 0:
            error = 'Oops! No search results found.'
        
        # Else render results.html page, passing the query results
        else:
            return render_template("results.html", results=results)
    
    # GET request for search, render search page with error message if previous search found no matches
    return render_template("search.html", error=error)
       
    
@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    """ Display book details for given isbn and any user reviews, allow current user to add review """
    
    # Route redirects to login if login_required returns false
    
    # Review count and average variable declarations
    rev_count = None
    rev_avg = None
    
    # If route receives posted form data which includes "review" then run this code
    if "review" in request.form:
        
        # Request review form data
        review = request.form.get("review")
        rating = request.form.get("rating")
        
        # Select book_id where book_isbn matches these parameter values, to be used for insert later
        book = db.execute("SELECT book_id FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        
        # Select user_id for session user to be used for insert later
        user = db.execute("SELECT user_id FROM users WHERE user_username = :username", {"username": session["username"]}).fetchone()
        
        # Insert review into reviews table
        db.execute("INSERT INTO reviews (review_rating, review_text, user_id, book_id) VALUES (:rating, :review, :user, :book)", {"rating": rating, "review": review, "user": user[0], "book": book[0]})
        db.commit()
        
        # Redirect user to page confirming review submitted
        return redirect(url_for('submitted'))
    
    # Select details for book with ISBN matching isbn parameter values
    book = db.execute("SELECT book_isbn, book_title, book_author, book_year FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # If query returns none, then isbn was not found in books table, render error page with message 
    if book is None:
        return render_template("error.html", message="Oops! ISBN not found.")
    
    # Set key and isbn parameters for goodreads API request, then make GET request
    params = {"key": "ak3jRQAe93UDwh2Q2tWg", "isbns": book.book_isbn}
    goodreads_data = requests.get("https://www.goodreads.com/book/review_counts.json", params=params)
    
    # Parse data from goodreads request
    goodreads_parse = goodreads_data.json()
    
    # Retrieve required rating data from JSON object
    ratings_count = goodreads_parse["books"][0]["ratings_count"]
    average_rating = goodreads_parse["books"][0]["average_rating"]
    
    # Select reviews for book_isbn matching these isbn parameter values, using join to retrieve reviewer username, limit of 4 rows are returned
    reviews = db.execute("SELECT user_username, review_text, review_rating FROM users JOIN reviews USING (user_id) JOIN books USING (book_id) WHERE book_isbn = :isbn  ORDER BY review_id DESC LIMIT 2", {"isbn": isbn}).fetchall()
    
    # If reviews found, calculate rating count and average
    if len(reviews) > 0:
        r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
        rev_count = r_count[0]
        rev_avg = round(r_avg[0], 2)

    # Check if the current user has left review for this book, set reviewed variable to true if so, this hides review form on page    
    reviewed = False
    if db.execute("SELECT * FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE book_isbn = :isbn AND user_username = :username", {"isbn": isbn, "username": session["username"]}).rowcount == 1:
        reviewed = True    

    # Render book.html page, passing all book and review info
    return render_template("book.html", book=book, reviews=reviews, ratings_count=ratings_count, average_rating=average_rating, reviewed=reviewed, rev_count=rev_count, rev_avg=rev_avg)


@app.route("/submitted")
@login_required
def submitted():
    """ Confirmation page when review is submitted """
    
    # When user is redirected after a successful review submission, render the confirmation reviewed.html page
    return render_template("reviewed.html")


@app.route("/reviews/<isbn>", methods=["GET", "POST"])
@login_required
def reviews(isbn):
    """ Query for total list of reviews, not limited to four """
    
    # Route redirects to login if login_required returns false
    
    # Select details for book with ISBN matching these isbn parameter values
    book = db.execute("SELECT book_isbn, book_title, book_author, book_year FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # Select reviews for book_isbn matching isbn parameter values, using join to retrieve reviewer username
    reviews = db.execute("SELECT user_username, review_text, review_rating FROM users JOIN reviews USING (user_id) JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchall()
    
    # If there are reviews found calculate the rating count and average
    if len(reviews) > 0:
        r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
        r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
        rev_count = r_count[0]
        rev_avg = round(r_avg[0], 2)        
    
    # Else render error.html page with message
    else:
        return render_template("error.html", message="Oops! No reviews found for that ISBN.")

    # Render reviews page, passing all the book and review information  
    return render_template("reviews.html", book=book, reviews=reviews, rev_count=rev_count, rev_avg=rev_avg)


@app.route("/myreviews")
@login_required
def myreviews():
    """ Query to return all reviews by user """
    
    reviews = db.execute("SELECT book_isbn, book_title, book_author, review_text, review_rating FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE user_username = :username", {"username": session["username"]}).fetchall()
    
    return render_template("myreviews.html", reviews=reviews)


@app.route("/reviewedby/<username>")
@login_required
def reviewedby(username):
    """ Query to return all reviews by given user """
    
    if db.execute("SELECT * FROM users WHERE user_username = :username", {"username": username}).rowcount == 0:
        return render_template("error.html", message="404 - not found.")
    
    reviews = db.execute("SELECT book_isbn, book_title, book_author, review_text, review_rating FROM books JOIN reviews USING (book_id) JOIN users USING (user_id) WHERE user_username = :username", {"username": username}).fetchall()
    
    return render_template("reviewedby.html", reviews=reviews, username=username)


@app.route("/api/<isbn>") 
def api(isbn):
    """ API route to return JSON response for ISBN """
    
    # Select details for book with ISBN matching these isbn parameter values     
    book = db.execute("SELECT book_title, book_author, book_year, book_isbn FROM books WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    
    # If query result is none, render error page indicating 404 error
    if book is None:
        return render_template("error.html", message="404 - not found.")
    
    # Query rating count and average
    r_count = db.execute("SELECT COUNT(*) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()
    r_avg = db.execute("SELECT AVG(review_rating) FROM reviews JOIN books USING (book_id) WHERE book_isbn = :isbn", {"isbn": isbn}).fetchone()   
    rev_count = r_count[0]
    if rev_count > 0:
        rev_avg = str(round(r_avg[0], 2))
    else:
        rev_avg = "n/a"
    
    # Return JSON object
    return jsonify({
        "title": book.book_title,
        "author": book.book_author,
        "year": book.book_year,
        "isbn": book.book_isbn,
        "review_count": rev_count,
        "average_score": rev_avg
        })