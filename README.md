<h4 align="center">
  <img alt="project 1" src="logo.png">
</h4>

***Book worms!*** Stuck scrolling through shelves of books before you *remember the favourite books you read last month*?

---

What if you were able to search for books, leave reviews for individual books, and see the reviews made by other people from Goodreads?

Your very own online *bookshelf* for keeping track of your favourites and finding new ones.

## Project 1: Books

*Objectives*.

> In this project, you’ll build a book review website. Users will be able to register for your website and then log in using their username and password. 
> Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people. 
> You’ll also use the a third-party API by Goodreads, another book review website, to pull in ratings from a broader audience. 
> Finally, users will be able to query for book details and book reviews programmatically via your website’s API.

Here's what I used to create Would You Read It?:

- [`PostgreSQL`](https://www.postgresql.org/)
- [`Python`](https://www.python.org/)
- [`Flask`](http://flask.palletsprojects.com/en/1.1.x/)
- [`Heroku`](https://heroku.com)
- [`Goodreads API`](https://www.goodreads.com/)
- [`Bulma Framework`](https://bulma.io/)

 <img alt="project 1" src="screenshot.png">

## Usage

Clone repo

    $ git clone

Create a virtualenv (optional)

    $ python3 -m venv myvirtualenv

Install all dependencies

    $ pip install -r requirements.txt

ENV Variables

    $ export FLASK_APP = application.py #flask run
    $ export DATABASE_URL = Heroku Database URI
    $ export GOODREADS_KEY = Goodreads API Key 

## Requirements

- Registration: Users should be able to register for your website, providing (at minimum) a username and password.
- Login: Users, once registered, should be able to log in to your website with their username and password.
- Logout: Logged in users should be able to log out of the site.
- Import: Provided for you in this project is a file called books.csv, which is a spreadsheet in CSV format of 5000 different books. Each one has an ISBN number, a title, an author, 
and a publication year. In a Python file called import.py separate from your web application, write a program that will take the books and import them into your PostgreSQL database. 
- Search: Once a user has logged in, they should be taken to a page where they can search for a book. Users should be able to type in the ISBN number of a book, the title of a book, or the author of a book. 
After performing the search, your website should display a list of possible matching results, or some sort of message if there were no matches. 
If the user typed in only part of a title, ISBN, or author name, your search page should find matches for those as well!
- Book Page: When users click on a book from the results of the search page, they should be taken to a book page, with details about the book: its title, author, publication year, ISBN number, 
and any reviews that users have left for the book on your website.
- Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. 
Users should not be able to submit multiple reviews for the same book.
- Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads.
- API Access: If users make a GET request to your website’s /api/<isbn> route, where <isbn> is an ISBN number, 
your website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON should follow the format:

{
    "title": "Memory",
    "author": "Doug Lloyd",
    "year": 2015,
    "isbn": "1632168146",
    "review_count": 28,
    "average_score": 5.0
}

If the requested ISBN number isn’t in your database, your website should return a 404 error.


## Acknowledgements

13.09.19 Submission for [`Harvard CS50W`](https://www.harvard.com)!


