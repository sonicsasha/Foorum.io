from http.client import InvalidURL
from urllib import request, response
from xml.dom import NotFoundErr
from flask import Flask
from flask import render_template, request, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_api import status
from os import access, getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

def adminForm():
    if common.notLoggedIn(): 
        abort(404)
    
    if common.getAuthLevel()<2: #Return an InvalidURL error so that the user doesn't know that an admin page exists ;)
        abort(404)
    
    return render_template("admin.html")

def nominateForm():
    if common.notLoggedIn():
        abort(404)
    
    if common.getAuthLevel()<2:
        abort(404)
    
    users=db.session.execute("SELECT username FROM users WHERE auth_level<2").fetchall()

    return render_template("admin_nominate.html", users=users)

def nominate():
    if common.notLoggedIn():
        abort(404)
    
    if common.getAuthLevel()<2:
        abort(404)
    
    if request.form["nominate_type"]=="moderator":
        db.session.execute("UPDATE users SET auth_level=1 WHERE username=:username", {"username":request.form["user"]})
        db.session.commit()
        print("Upgraded to mod")
    
    if request.form["nominate_type"]=="admin":
        db.session.execute("UPDATE users SET auth_level=2 WHERE username=:username", {"username":request.form["user"]})
        db.session.commit()
    
    return redirect("/admin/nominate")
    

