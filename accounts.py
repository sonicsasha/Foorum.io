from flask import Flask
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import access, getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common
import secrets

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

def loginForm():
    session["csrf_token"] = secrets.token_hex(16) #Generate the CSRF-token when the login screen is rendered, since this step cannot be skipped.
    return render_template("login_form.html")

def login():
    sql = "SELECT username, password FROM users WHERE username=:username"
    user = db.session.execute(sql, {"username": request.form["username"]}).fetchone()

    common.CSRFCheck()

    #Fail to log in if the user inputs a wrong username or the wrong password. No distinction due to cyber security.
    if not user or check_password_hash(user.password, request.form["password"])==False: 
        return render_template("login_form.html", messages=["Käyttäjää ei löytynyt tai salasana on väärä. Yritä uudelleen!"])
    else:
        session["username"]=user.username

        ban_check=db.session.execute("SELECT reason FROM bans WHERE user_id=:user_id", {"user_id": common.getUserId()}).fetchone()
        if ban_check:
            del session["username"]
            return render_template("login_form.html", messages=[f"Tämä käyttäjä on asetettu kieltoon seuraavasta syystä: {ban_check[0]}"])

        return redirect("/")


def signupForm():
    return render_template("signup_form.html")


def signup():
    common.CSRFCheck()


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

def signout():
    del session["username"]
    return redirect("/")

def upgradeToAdmin():
    if common.notLoggedIn():
        return redirect("/")
    
    if not db.session.execute("SELECT * FROM users WHERE auth_level=2").fetchone(): #If there are no admin users, then upgrade the current one to admin status. This is just for testing.
        db.session.execute("UPDATE users SET auth_level=2 WHERE id=:id", {"id":common.getUserId()})
        db.session.commit()
    
    return redirect("/")