from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from os import access, getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

def newThreadForm(id):
    if common.notLoggedIn():
        return redirect("/")
    
    topic_name=db.session.execute("SELECT topic_name FROM topics WHERE id=:id", {"id":id}).fetchone()[0]
    
    return render_template("thread_editor.html",
        title=f"Luo uusi viestiketju aiheeseen {topic_name}",
        submit="Luo viestiketju",
        action=f"/topic/{id}/new")

def newThreadSubmit(id):
    if common.notLoggedIn():
        return redirect("/")
    
    messages=[]

    topic_name=db.session.execute("SELECT topic_name FROM topics WHERE id=:id", {"id":id}).fetchone()[0]
    thread_name=request.form["name"]
    thread_desc=request.form["desc"]

    if len(thread_name)==0:
        messages.append("Ole hyvä, ja anna viestiketjulle otsikko!")
    
    if len(messages)>0:
        return render_template("thread_editor.html",
        title=f"Luo uusi viestiketju aiheeseen {topic_name}",
        submit="Luo viestiketju",
        action=f"/topic/{id}/new",
        thread_name=thread_name,
        thread_desc=thread_desc)
    
    sql="INSERT INTO threads (poster_id, topic_id, thread_header, thread_desc, sent_at) VALUES (:user_id, :topic_id, :thread_name, :thread_desc, NOW())"
    db.session.execute(sql, {"user_id":common.getUserId(), "topic_id":id, "thread_name":thread_name, "thread_desc":thread_desc})
    db.session.commit()

    return redirect(f"/topic/{id}")

def showThread(id):
    if common.notLoggedIn():
        return redirect("/")

    check=common.checkTopicPerm(id)

    if check!=None:
        return check

    sql="SELECT Th.id, Th.thread_header, Th.thread_desc, Top.topic_name, Th.sent_at, Th.edited_at, U.username, U.auth_level FROM threads Th LEFT JOIN topics Top ON Th.topic_id=Top.id LEFT JOIN users U ON U.id=Th.poster_id WHERE Th.id=:id"
    thread_info=db.session.execute(sql, {"id":id}).fetchone()
    if not thread_info:
        abort(403, "Viestiketjua ei löytynyt!") #Thread not found
    
    sql="SELECT U.username, U.auth_level, R.id, R.message, R.sent_at, R.edited_at FROM replies R LEFT JOIN users U ON U.id=R.poster_id WHERE thread_id=:thread_id ORDER BY R.sent_at"
    replies=db.session.execute(sql, {"thread_id":id})
    
    return render_template("thread.html", thread_info=thread_info, logged_user=session["username"], user_auth_level=common.getAuthLevel(), replies=replies)


def confirmDeleteThread(id):
    if common.notLoggedIn():
        redirect("/")
    
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=common.checkTopicPerm(topic_id)

    if check!=None:
        return check

    sql="SELECT id, poster_id, thread_header FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()

    
    return render_template("delete_thread.html", thread=thread)


def deleteThread(id):
    if common.notLoggedIn():
        return redirect("/")
    
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=common.checkTopicPerm(topic_id)

    if check!=None:
        return check
    
    sql="SELECT id, poster_id, thread_header, topic_id FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()

    sql="DELETE FROM replies WHERE thread_id=:id"
    db.session.execute(sql, {"id":id})
    db.session.commit()

    sql="DELETE FROM threads WHERE id=:id"
    db.session.execute(sql, {"id":id})
    db.session.commit()

    return redirect(f"/topic/{thread['topic_id']}")


def editThreadForm(id):
    check=common.checkThreadEditPerm(id)

    if check!=None:
        return check

    sql="SELECT thread_header, thread_desc, poster_id FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()
    
    return render_template("thread_editor.html",
        title=f"Muokkaa viestiketjua {thread['thread_header']}",
        thread_name=thread["thread_header"],
        thread_desc=thread["thread_desc"],
        submit="Tallenna muutokset",
        action=f"/thread/{id}/edit")
    

def editThread(id):
    check=common.checkThreadEditPerm(id)
    
    if check!=None:
        return check

    sql="SELECT thread_header, thread_desc, poster_id FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()
    
    thread_header=request.form["name"]
    thread_desc=request.form["desc"]

    if len(thread_header)==0:
        return render_template("thread_editor.html",
        title=f"Muokkaa viestiketjua {thread['thread_header']}",
        submit="Tallenna muutokset",
        action=f"/thread/{id}/edit",
        thread_header=thread_header,
        thread_desc=thread_desc,
        messages=["Ole hyvä, ja anna viestiketjulle otsikko!"])
    
    sql="UPDATE threads SET thread_header=:thread_header, thread_desc=:thread_desc, edited_at=NOW() WHERE id=:id"
    db.session.execute(sql, {"thread_header":thread_header, "thread_desc":thread_desc, "id":id})
    db.session.commit()

    return redirect(f"/thread/{id}")


def newReplyForm(id):
    if common.notLoggedIn():
        return ("/")
     

    check=common.checkTopicPerm(id)

    if check!=None:
        return check

    #Get the name of the thread where the reply is being posted.
    thread=db.session.execute("SELECT thread_header FROM threads WHERE id=:id", {"id":id}).fetchone()[0] 

    return render_template("reply_editor.html", thread=thread, title="Vastaa viestiketjuun", submit="Vastaa")

def newReply(id):
    if common.notLoggedIn():
        return redirect("/")
    
    #Get the topic id and check if the user even has access to that topic.
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id LEFT JOIN replies ON replies.thread_id=threads.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=common.checkTopicPerm(topic_id)

    if check!=None:
        return check
    
    thread=db.session.execute("SELECT thread_header FROM threads WHERE id=:id", {"id":id}).fetchone()[0] 

    if request.form["reply"].strip()=="":
        return render_template("reply_editor.html", 
        thread=thread,
        title="Vastaa viestiketjuun",
        submit="Vastaa",
        messages=["Ole hyvä, ja anna vastaus!"])
    
    sql="INSERT INTO replies (poster_id, thread_id, message, sent_at) VALUES (:user_id, :thread_id, :message, NOW())"
    db.session.execute(sql, {"user_id":common.getUserId(), "thread_id":id, "message":request.form["reply"]})
    db.session.commit()

    return redirect(f"/thread/{id}")