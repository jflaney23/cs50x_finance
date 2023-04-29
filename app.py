import os

from dotenv import load_dotenv
load_dotenv()

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    user_stocks = db.execute("SELECT symbol, shares FROM portfolio WHERE user_id = ?", user_id)
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?",user_id)[0]["cash"]
    # creating dictionary to send all of this data in one piece to the HTML page
    portfolio = []
    # lookup symbol and pass it to the html page
    for i in user_stocks:
        stock_info = lookup(i["symbol"])
        total_value = i["shares"] * stock_info["price"]
        portfolio.append({"symbol": i["symbol"], "shares": i["shares"], "price": stock_info["price"], "total_value": total_value})


    return render_template("index.html", portfolio=portfolio, user_cash = user_cash)
    # need a table that contains: which stocks user owns, the number of shares owned, the current price of the stock, total value of each holding

    # table only needs to contain the number of shares per stock i own. rest can be used with API to call and then calculate
    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not lookup(symbol) or symbol == "":
            return apology("Input is blank or symbol does not exist")

        symbol_info = lookup(symbol)
        price = symbol_info["price"]

        if not shares:
            return apology("Please enter the number of shares to buy")

        totalCost=price*shares

        #Get the current user's username
        user_id = session["user_id"]
        user_row = db.execute("SELECT username, cash FROM users WHERE id = ?", user_id)
        username = user_row[0]['username']
        usermoney = user_row[0]['cash']

        # If usermoney < totalCost:
        if usermoney < totalCost:
            return apology("Cannot afford the number of shares at the current price")

        # remove totalCost FROM usermoney
        new_cash_amount = usermoney - totalCost
        db.execute("UPDATE users SET cash = ? WHERE username = ?", new_cash_amount, username)
        db.execute("INSERT INTO portfolio (user_id, symbol, shares) VALUES (?, ?, ?)", user_id, symbol, shares)
        return render_template("buy.html", shares=shares, symbol=symbol, price=price)

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        # search API for "symbol"
        symbolDict = lookup(symbol)
        # if found:
        if symbolDict:
            return render_template("quoted.html", symbolDict=symbolDict)
            # display the symbol

            # render_template ("quoted.html")
        else:
            return apology("Invalid symbol")

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # get the user's username from the register.html file
        username=request.form.get("username")
            # if username already in database OR username is blank:
        result=db.execute("SELECT * FROM users WHERE username = ?", username)
        if result or username == "":
                # return apology("Username already exists")
            return render_template("apology.html")
        # get the user's password from the register.html file
        password=request.form.get("password")
        # get the user's confirmation password from the register.html file
        confirmation=request.form.get("confirmation")
        # if password is "" OR password and confirmation don't match:
        if password!=confirmation or password=="" or confirmation=="":
            # return apology("pass doesn't match or blank")
            return render_template("pass doesn't match or blank")
        # INSERT new user into "users". Store hash of user's password. Hash the user's password with "generate_password_hash".
        hashed_password=generate_password_hash(password)
        db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", username, hashed_password)
        print("successfully imported new user")
        return render_template("register.html")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":

        user_id = session["user_id"]

        # take user input "symbol" and "shares"
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        user_row = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", user_id, symbol)

        # if user doesn't own symbol or no symbol selected, error
        if not user_row or not lookup(symbol):
            return apology("Stock not correct or you don't own it")

        # if user does own symbol but doesn't own enough shares or not positive integer, error
        if not user_row[0]["shares"] or not shares > 0 or shares > user_row[0]["shares"]:
            return apology("Don't own enough shares or not positive integer")
        newShares = user_row[0]["shares"] - shares

        # get user cash amount and update it
        row = db.execute("SELECT username, cash FROM users WHERE id = ?", user_id)
        username = row[0]['username']
        usermoney = row[0]['cash']

        totalCost = lookup(symbol)["price"] * shares

        new_cash_amount = usermoney - totalCost

        db.execute("UPDATE users SET cash = ? WHERE username = ?", new_cash_amount, username)
        if newShares > 0:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?", newShares, user_id, symbol)
        else:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?", user_id, symbol)

        return redirect("/")

    return render_template("sell.html")