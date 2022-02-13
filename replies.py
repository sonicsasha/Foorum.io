from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import access, getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)


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

def deleteReplyConfirm(id):
    if common.notLoggedIn():
        return redirect("/")

    if common.getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()

        if common.getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")

    sql="SELECT U.username, U.auth_level, R.id, R.message, R.sent_at, R.edited_at, R.thread_id FROM replies R LEFT JOIN users U ON U.id=R.poster_id WHERE R.id=:id"
    reply=db.session.execute(sql, {"id":id}).fetchone()

    if not reply:
        return ("Vastausta jota halusit muokata ei löydy.")

    return render_template("reply_delete.html", reply=reply)

def deleteReply(id):
    if common.notLoggedIn():
        return redirect("/")
    

    if common.getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if common.getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")
    
    thread_id=db.session.execute("SELECT thread_id FROM replies WHERE id=:id", {"id":id}).fetchone()
    if not thread_id:
        return ("Vastausta jota halusit muokata ei löydy")

    sql="DELETE FROM replies WHERE id=:id"
    db.session.execute(sql, {"id":id})
    db.session.commit()

    return redirect(f"/thread/{thread_id[0]}")

def replyEditForm(id):
    if common.notLoggedIn():
        return redirect("/")
    
    if common.getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if common.getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")
    
    sql="SELECT T.thread_header, R.message FROM replies R LEFT JOIN threads T ON R.thread_id = T.id WHERE R.id = :id"
    reply=db.session.execute(sql, {"id":id}).fetchone()

    return render_template("reply_editor.html", 
        title=f"Muokkaa viestiä",
        thread = reply["thread_header"],
        reply=reply["message"],
        submit="Tallenna muutokset"
    )

def editReply(id):
    if common.notLoggedIn():
        return redirect("/")
    
    if common.getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if common.getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")
    
    sql="SELECT R.thread_id, T.thread_header, R.message FROM replies R LEFT JOIN threads T ON R.thread_id = T.id WHERE R.id = :id"
    reply=db.session.execute(sql, {"id":id}).fetchone()

    if request.form["reply"].strip()=="":
        return render_template("reply_editor.html",
            title="Muokkaa viestiä",
            thread = reply["thread_header"],
            reply=request.form["reply"],
            submit="Tallenna muutokset",
            messages=["Ole hyvä, ja anna vastaus!"]
            )
    
    db.session.execute("UPDATE replies SET message=:message, edited_at=NOW() WHERE id=:id", {"message":request.form["reply"], "id":id})
    db.session.commit()

    return redirect(f"/thread/{reply['thread_id']}")
    
