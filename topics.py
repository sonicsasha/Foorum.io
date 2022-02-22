from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

def mainPage():
    if common.notLoggedIn():
        return redirect("/login")

    user_id = common.getUserId()
    auth_level = common.getAuthLevel()

    if auth_level>=1: #Moderators and admins can see all topics
        sql="SELECT COUNT(threads.id), T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN threads ON threads.topic_id=T.id GROUP BY T.id ORDER BY T.id;"
    else:
        sql="SELECT COUNT(threads.id), T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN topicsAccess TA ON TA.topic_id=T.id LEFT JOIN threads ON threads.topic_id=T.id WHERE T.is_hidden=False OR TA.user_id=:user_id GROUP BY T.id ORDER BY T.id;"
    
    topics=db.session.execute(sql, {"user_id":user_id}).fetchall()
    print(topics)




    return render_template("topics.html", topics=topics, auth_level=auth_level)

def threads(id):
    if common.notLoggedIn():
        return redirect("/")

    is_hidden = db.session.execute("SELECT is_hidden FROM topics WHERE id=:id", {"id":id}).fetchone()
    if not is_hidden: #Check if the topic even exists.
        abort(404,"Aihetta ei löytynyt. Yritä uudelleen!")
    
    if is_hidden[0]==True and common.getAuthLevel()==0:
        has_access=db.session.execute("SELECT topic_id FROM topicsAccess WHERE topic_id=:id AND user_id=:user_id", {"id":id, "user_id":common.getUserId()}).fetchone()
        if not has_access: #If the topic is private, then check that the user has access to the topic.
            abort(403,"Sinulla ei ole pääsyä tähän aiheeseen. Mene pois! >:(")
    
    sql="SELECT T.id, U.username, U.auth_level, T.thread_header, T.thread_desc, T.sent_at, T.edited_at, MAX(R.sent_at), COUNT(R.sent_at) FROM threads T LEFT JOIN users U ON U.id=T.poster_id LEFT JOIN replies R ON R.thread_id=T.id WHERE T.topic_id=:topic_id GROUP BY T.id, U.username, U.auth_level ORDER BY T.sent_at DESC"
    threads=db.session.execute(sql, {"topic_id":id})
    return render_template("threads.html", threads=threads, auth_level=common.getAuthLevel(), topic_id=id)

def editTopicForm(id):
    if common.notLoggedIn():
        return redirect("/")


    if common.getAuthLevel()<=1:
        abort(403,"Sinulla ei ole tarvittavia oikeuksia.")

    sql="SELECT topic_name, topic_desc, is_hidden FROM topics WHERE id=:id"
    topic=db.session.execute(sql, {"id":id}).fetchone()

    if not topic:
        abort(404,"Aihetta ei löytynyt!")

    access=""
    sql="SELECT U.username FROM users U LEFT JOIN topicsAccess TA ON U.id=TA.user_id WHERE TA.topic_id=:id"
    for user in db.session.execute(sql, {"id":id}).fetchall(): #Get the usernames that have access to the topic.
        access+=f"{user[0]}, "

    return render_template(
        "topic_editor.html",
        title="Muokkaa aihetta",
        submit="Tallenna muutokset",
        action=f"/topic/{id}/edit",
        topic_name=topic["topic_name"],
        topic_desc=topic["topic_desc"],
        is_hidden=topic["is_hidden"],
        access=access[:-2],
    )

def editTopicSubmit(id):
    if common.notLoggedIn():
        return redirect("/")
    elif common.getAuthLevel()<2:
        abort(403,"Sinulla ei ole tarvittavia oikeuksia tätä varten!")
    
    common.CSRFCheck()

    sql="SELECT topic_name FROM topics WHERE id=:id"
    topic=db.session.execute(sql, {"id":id}).fetchone()
    
    topic_name=request.form["name"]
    topic_desc=request.form["desc"]
    access=request.form["access"]

    messages=common.parseTopicForm(topic["topic_name"]!=topic_name)



    if request.form["privacy"]=="public":
        hidden=False
    else:
        hidden=True

    if len(messages)>0:
        return render_template("topic_editor.html",
        action=f"/topic/{id}/edit",
        messages=messages,
        topic_name=topic_name,
        topic_desc=topic_desc,
        access=access,
        is_hidden=hidden,
        title="Muokkaa aihetta",
        submit="Tallenna muutokset")
    
    sql="UPDATE topics SET topic_name=:topic_name, topic_desc=:topic_desc, is_hidden=:hidden WHERE id=:id"
    db.session.execute(sql, {"topic_name":topic_name, "topic_desc":topic_desc, "hidden":hidden, "id":id})

    db.session.execute("DELETE FROM topicsAccess WHERE topic_id=:id", {"id":id})
    db.session.commit()

    access_names=access.replace(" ","").split(",")

    if access_names!=['']:
        for name in access_names:
            user_id=db.session.execute("SELECT id FROM users WHERE username=:name", {"name":name}).fetchone()[0]
            db.session.execute("INSERT INTO topicsAccess (user_id, topic_id) VALUES (:user_id, :topic_id)", {"user_id":user_id, "topic_id":id})
            db.session.commit()
    
    return redirect("/")

def newTopicForm():
    if common.notLoggedIn():
        return redirect("/")


    if common.getAuthLevel()<=1:
        abort(403,"Sinulla ei ole tarvittavia oikeuksia tätä varten.")
    
    return render_template("topic_editor.html", title="Luo uusi aihe", submit="Luo aihe", action="/topic/new")

def createNewTopic():
    if common.notLoggedIn():
        return redirect("/")
    
    common.CSRFCheck()

    if request.form["privacy"]=="public":
        hidden=False
    else:
        hidden=True

    messages=common.parseTopicForm(True)

    topic_name=request.form["name"]
    topic_desc=request.form["desc"]
    access=request.form["access"]

    if len(messages)>0:
        return render_template("topic_editor.html",
        title="Luo uusi aihe",
        submit="Luo aihe",
        messages=messages,
        topic_name=topic_name,
        topic_desc=topic_desc,
        access=access,
        is_hidden=hidden,
        action="/topic/new")
    

    
    sql="INSERT INTO topics (topic_name, topic_desc, is_hidden) VALUES (:name, :desc, :hidden);"
    db.session.execute(sql, {"name":topic_name, "desc":topic_desc, "hidden":hidden})
    db.session.commit()

    topic_id=db.session.execute("SELECT id FROM topics WHERE topic_name=:name", {"name":request.form["name"]}).fetchone()[0]

    access_names=access.replace(" ","").split(",")

    if access_names!=['']:
        for name in access_names:
            id=db.session.execute("SELECT id FROM users WHERE username=:name", {"name":name}).fetchone()[0]
            db.session.execute("INSERT INTO topicsAccess (user_id, topic_id) VALUES (:user_id, :topic_id)", {"user_id":id, "topic_id":topic_id})
            db.session.commit()

    return redirect("/")