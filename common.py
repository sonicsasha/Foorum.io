from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from os import access, getenv
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

def getUserId():
    return db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]

def parseTopicForm(has_name_changed):
    topic_name=request.form["name"]
    topic_desc=request.form["desc"]
    access=request.form["access"]

    messages=[]

    
    if topic_name=="":
        messages.append("Ole hyvä, ja syötä aihe!")
    if len(topic_name)>50:
        messages.append("Aiheen nimi on liian pitkä! (max. 50 merkkiä)")
    if topic_desc=="":
        messages.append("Ole hyvä, ja anna aiheelle kuvaus!")
    if len(topic_desc)>100:
        messages.append("Aiheen kuvaus on liian pitkä! (max. 100 merkkiä)")
    if has_name_changed:
        if db.session.execute("SELECT id FROM topics WHERE topic_name=:name", {"name":topic_name}).fetchone():
            messages.append("Ole hyvä, ja valitse aiheelle jokin muu nimi!")

    access_names=access.replace(" ","").split(",") #Check if every user who is supposed to see the topic actually exists.
    if access_names[0]!='':
        for name in access_names:
            id=db.session.execute("SELECT id FROM users WHERE username=:name", {"name":name}).fetchone()
            if not id:
                messages.append(f"Käyttäjää {name} ei löytynyt!")
    
    return messages

def checkThreadEditPerm(id):
    if notLoggedIn():
        return redirect("/")
        
    sql="SELECT thread_header, thread_desc, poster_id FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()
    if not thread:
        abort(404, "Viestiketjua ei löytynyt!")

    elif thread["poster_id"]!=getUserId() and getAuthLevel()==0:
        abort(403, "Sinulla ei ole tarvittavia oikeuksia tähän!")

def checkTopicPerm(thread_id):
    try:
        sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
        topic_id=db.session.execute(sql, {"id":thread_id}).fetchone()[0] 
    except:
        abort(404, "Aihetta ei löytynyt!")

    is_hidden = db.session.execute("SELECT is_hidden FROM topics WHERE id=:id", {"id":topic_id}).fetchone()
    if not is_hidden: #Check if the topic even exists.
        abort(404, "Aihetta ei löytynyt!")
    
    if is_hidden[0]==True and getAuthLevel()==0:
        has_access=db.session.execute("SELECT topic_id FROM topicsAccess WHERE topic_id=:id AND user_id=:user_id", {"id":topic_id, "user_id":getUserId()}).fetchone()
        if not has_access: #If the topic is private, then check that the user has access to the topic.
            abort(403, "Sinulla ei ole oikeuksia tähän toimintoon!")

def CSRFCheck():
    if session["csrf_token"] != request.form["csrf_token"]:
        abort(403)
