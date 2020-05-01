import os,requests

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

log={"login":False,"username":None,"comment":False,"isbn":None}

@app.route("/",methods=["GET","POST"])
def index():
    return render_template("homepage.html",message="Welcome!",log=log)

@app.route("/signup")
def signup():
    return render_template("signup.html",log=log)

@app.route("/create",methods=["POST","GET"])
def create():
    name=request.form.get("name")
    email=request.form.get("email")
    username=request.form.get("username")
    password=request.form.get("password")
    password2=request.form.get("password2")
    for x in name,username,password,password2:
        if not x:
            return render_template("signup.html",message="Please fill in the details",log=log)
    if password != password2:
        return render_template("signup.html",message="Type same password in both the fields",log=log)
    try:
        engine.execute("INSERT INTO users(name,email,username,password)VALUES(%s,%s,%s,%s)",(name,email,username,password))
        return render_template("login.html",message="Account successfully created! Login to continue.",log=log)
    except Exception:
        return render_template("signup.html",message="Username not availabe. Try a different one",log=log)

@app.route("/login")
def login():
    return render_template("login.html",log=log)

@app.route("/auth",methods=["POST"])
def auth():
    global log
    user=request.form.get("username")
    word=request.form.get("password")
    for x in user,word:
        if not x:
            return render_template("login.html",message="Please fill in the details",log=log)
    infos=db.execute("SELECT username,password FROM users WHERE username=:username",{"username":user}).fetchall()
    if not infos:
        return render_template("login.html",message="Username not found! Please create account first!",log=log)
    try:
        for info in infos:
            if info.password==word:
                log["login"]=True
                log["username"]=info.username
                return render_template("homepage.html",message="Welcome! You are successfully logged in!",log=log,name=info.username)
            else:
                return render_template("login.html",message="Incorrect Password. Try again!",log=log)
    except ValueError:
        return render_template("login.html",message="Unknown error!",log=log)

@app.route("/logout")
def logout():
    global log
    log["login"]=False
    log["username"]=None
    return render_template("homepage.html",log=log,message="You are logged out!")

@app.route("/books/<isbn>",methods=["GET","POST"])
def book(isbn):
    try:
        all=db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
        for one in all:
            title=one.title
            author=one.author
            year=one.year
            global log
            log["isbn"]=isbn
        reviews=db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn})
        res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "oyzxgaURlHMiE6jbIqjEg", "isbns": isbn})
        data=res.json()
        messages=data['books']
        for mess in messages:
            avgrate=mess["average_rating"]
            countrate=mess["work_ratings_count"]
        return render_template("books.html",isbn=isbn,title=title,author=author,year=year,log=log,reviews=reviews,avgrate=avgrate,countrate=countrate)
    except TypeError:
        return render_template("homepage.html",message="book not available",log=log)

@app.route("/books/review",methods=["POST","GET"])
def review():
    global log
    if log["login"]==True:
        rating=request.form.get('rating')
        comment=request.form.get('comment')
        name=log["username"]
        isbn=log["isbn"]
        check=db.execute("SELECT * FROM reviews WHERE isbn=:isbn AND username=:username",{"isbn":isbn,"username":name}).fetchall()

        if not check:
            engine.execute("INSERT INTO reviews(comment,rating,isbn,username)VALUES(%s,%s,%s,%s)",(comment,rating,isbn,name))
            message="The review has been added to the site."
        else:
            message="You have already provided review for this book"

        all=db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
        for one in all:
            title=one.title
            author=one.author
            year=one.year
        reviews=db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
        res=requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "oyzxgaURlHMiE6jbIqjEg", "isbns": isbn})
        data=res.json()
        messages=data['books']
        for mess in messages:
            avgrate=mess["average_rating"]
            countrate=mess["work_ratings_count"]
        return render_template("books.html",isbn=isbn,title=title,author=author,year=year,log=log,reviews=reviews,message=message,avgrate=avgrate,countrate=countrate)

    else:
        return render_template("login.html",message="You need to log in first",log=log)

@app.route("/error")
def error():
    global log
    return render_template("error.html",log=log)

@app.route("/search",methods=["GET","POST"])
def search():
    try:
        seek=request.form.get('seek')
        seek='%'+seek+'%'
        items=db.execute("SELECT * FROM books WHERE isbn LIKE :seek OR title LIKE :seek OR author LIKE :seek OR year LIKE :seek LIMIT 50",{"seek":seek})
        return render_template("search.html",log=log,items=items)
    except Exception:
        return render_template("error.html",log=log,message="unknown error")

@app.route("/api/<isbn>",methods=["GET","POST"])
def api(isbn):
    books=db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
    for book in books:
        title=book.title
        isbn=book.isbn
        year=book.year
        author=book.author
    reviews=db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).fetchall()
    if not books:
        return jsonify({"error": "Invalid flight_id"}), 422
    elif not reviews:
        count=None
        average=None
    else:
        count=0
        rating=0
        for review in reviews:
            count+=1
            rating+=review.rating
        average=rating/count
        average=str(round(average,2))
        count=str(count)
    return jsonify({
        "title":title,
        "author":author,
        "year":year,
        "isbn":isbn,
        "review_count":count,
        "average_score":average
    })
