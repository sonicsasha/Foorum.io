from crypt import methods
from email import message
from pyexpat.errors import messages
from queue import Empty
import re
from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

def notLoggedIn():
    try:
        if not session["username"]: #If the user is not signed in, redirect him to the login screen.
            return True
    except:
        return True

def getAuthLevel():
    return db.session.execute("SELECT auth_level FROM users WHERE username=:username", {"username": session["username"]}).fetchone()[0]


@app.route("/")
def mainpage():
    if notLoggedIn():
        return redirect("/login")


    sql= "SELECT id, topic_name, topic_desc, is_hidden FROM topics"
    topics=db.session.execute(sql).fetchall()
    print(topics)
    auth_level=db.session.execute("SELECT auth_level FROM users WHERE username=:username", {"username": session["username"]} ).fetchone()



    return render_template("topics.html", topics=topics, auth_level=auth_level[0])


@app.route("/topic/new", methods=["GET"])
def newTopic_form():
    try:
        if getAuthLevel()<=1:
            return ("You don't have the necessary permissions to perform this task.")
        
        return render_template("topic_editor.html")

    except:
        return redirect("/")

@app.route("/topic/new", methods=["POST"])
def create_new_topic():
    topic_name=request.form["name"]
    topic_desc=request.form["desc"]
    access=request.form["access"]

    messages=[]
    
    if request.form["privacy"]=="public":
        hidden=False
    else:
        hidden=True
    
    if topic_name=="":
        messages.append("Ole hyvä, ja syötä aihe!")
    if len(topic_name)>50:
        messages.append("Aiheen nimi on liian pitkä! (max. 50 merkkiä)")
    if topic_desc=="":
        messages.append("Ole hyvä, ja anna aiheelle kuvaus!")
    if len(topic_desc)>100:
        messages.append("Aiheen kuvaus on liian pitkä! (max. 100 merkkiä)")
    
    if len(messages)>0:
        return render_template("topic_editor.html", messages=messages, topic_name=topic_name, topic_desc=topic_desc, access=access)
    
    sql="INSERT INTO topics (topic_name, topic_desc, is_hidden) VALUES (:name, :desc, :hidden);"
    db.session.execute(sql, {"name":topic_name, "desc":topic_desc, "hidden":hidden})
    db.session.commit()
    return redirect("/")

@app.route("/login", methods=["GET"])
def login_form():
    return render_template("login_form.html")

@app.route("/login", methods=["POST"])
def login():
    sql = "SELECT username, password FROM users WHERE username=:username"
    user = db.session.execute(sql, {"username": request.form["username"]}).fetchone()

    #Fail to log in if the user inputs a wrong username or the wrong password. No distinction due to cyber security.
    if not user or check_password_hash(user.password, request.form["password"])==False: 
        return render_template("login_form.html", messages=["Käyttäjää ei löytynyt tai salasana on väärä. Yritä uudelleen!"])
    else:
        session["username"]=user.username
        return redirect("/")

    


@app.route("/signup", methods=["GET"])
def signup_form():
    return render_template("signup_form.html")

@app.route("/signup", methods=["POST"])
def signup():
    username=request.form["username"]
    password=request.form["password"]
    messages=[]

    if username=="":
        messages.append("Syötä oikea käyttäjätunnus!")
    
    if password=="":
        messages.append("Syötä oikea salasana!")
    
    elif password!=request.form["password_check"]: #Check that the user wrote the password two times and that they match.
        messages.append("Salasanat eivät täsmää!")

    if db.session.execute("SELECT * FROM users WHERE username=:username", {"username": username}).fetchone()!=None:
        messages.append("Tällä käyttäjätunnuksella on jo olemassa käyttäjä. Valitse jokin muu käyttäjätunnus!")

    
    if len(messages)>0: #Show error messages if there are errors
        return render_template("signup_form.html", messages=messages)
    else:
        password_hashed = generate_password_hash(password)
        sql_create_account="INSERT INTO users (username, password, auth_level) VALUES (:username, :password, 0)"
        db.session.execute(sql_create_account, {"username":username, "password":password_hashed}) #Create an account with the lowest levest of authorization.
        db.session.commit()
        session["username"] = username
        return redirect("/")

@app.route("/signout")
def signout():
    del session["username"]
    return redirect("/")


