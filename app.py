from crypt import methods
from pyexpat.errors import messages
from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect
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
        return("Thread not found!")

    elif thread["poster_id"]!=getUserId() and getAuthLevel()==0:
        return ("You don't have permission to perform this action.")

def checkTopicPerm(thread_id):
    try:
        sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
        topic_id=db.session.execute(sql, {"id":thread_id}).fetchone()[0] 
    except:
        return "Viestiketjua ei löytynyt"

    is_hidden = db.session.execute("SELECT is_hidden FROM topics WHERE id=:id", {"id":topic_id}).fetchone()
    if not is_hidden: #Check if the topic even exists.
        return("Aihetta ei löytynyt. Yritä uudelleen!")
    
    if is_hidden[0]==True and getAuthLevel()==0:
        has_access=db.session.execute("SELECT topic_id FROM topicsAccess WHERE topic_id=:id AND user_id=:user_id", {"id":topic_id, "user_id":getUserId()}).fetchone()
        if not has_access: #If the topic is private, then check that the user has access to the topic.
            return ("Sinulla ei ole pääsyä tähän aiheeseen. Mene pois! >:(")


@app.route("/")
def mainpage():
    if notLoggedIn():
        return redirect("/login")

    user_id = getUserId()
    auth_level = getAuthLevel()

    if auth_level>=1: #Moderators and admins can see all topics
        sql="SELECT T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T ORDER BY T.id;"
    else:
        sql="SELECT T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN topicsAccess TA ON TA.topic_id=T.id  WHERE T.is_hidden=False OR TA.user_id=:user_id ORDER BY T.id;"
    
    topics=db.session.execute(sql, {"user_id":user_id}).fetchall()
    print(topics)




    return render_template("topics.html", topics=topics, auth_level=auth_level)

@app.route("/topic/<int:id>")
def threads(id):
    if notLoggedIn():
        return redirect("/")

    is_hidden = db.session.execute("SELECT is_hidden FROM topics WHERE id=:id", {"id":id}).fetchone()
    if not is_hidden: #Check if the topic even exists.
        return("Aihetta ei löytynyt. Yritä uudelleen!")
    
    if is_hidden[0]==True and getAuthLevel==0:
        has_access=db.session.execute("SELECT topic_id FROM topicsAccess WHERE topic_id=:id AND user_id=:user_id", {"id":id, "user_id":getUserId()}).fetchone()
        if not has_access: #If the topic is private, then check that the user has access to the topic.
            return ("Sinulla ei ole pääsyä tähän aiheeseen. Mene pois! >:(")
    
    sql="SELECT U.username, U.auth_level, T.thread_header, T.thread_desc, T.sent_at, T.edited_at, T.id FROM threads T LEFT JOIN users U ON U.id=T.poster_id WHERE T.topic_id=:topic_id ORDER BY T.sent_at DESC"
    threads=db.session.execute(sql, {"topic_id":id})
    return render_template("threads.html", threads=threads, auth_level=getAuthLevel(), topic_id=id)

@app.route("/topic/<int:id>/edit", methods=["GET"])
def editTopicForm(id):
    if notLoggedIn():
        return redirect("/")


    if getAuthLevel()<=1:
        return ("You don't have the necessary permissions to perform this task.")

    sql="SELECT topic_name, topic_desc, is_hidden FROM topics WHERE id=:id"
    topic=db.session.execute(sql, {"id":id}).fetchone()

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

@app.route("/topic/<int:id>/edit", methods=["POST"])
def editTopicSubmit(id):
    if notLoggedIn():
        return redirect("/")
    elif getAuthLevel()<2:
        return ("You don't have the rights to perform this task!")

    sql="SELECT topic_name FROM topics WHERE id=:id"
    topic=db.session.execute(sql, {"id":id}).fetchone()
    
    topic_name=request.form["name"]
    topic_desc=request.form["desc"]
    access=request.form["access"]

    messages=parseTopicForm(topic["topic_name"]!=topic_name)



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

@app.route("/topic/<int:id>/new", methods=["GET"])
def newThreadForm(id):
    if notLoggedIn():
        return redirect("/")
    
    topic_name=db.session.execute("SELECT topic_name FROM topics WHERE id=:id", {"id":id}).fetchone()[0]
    
    return render_template("thread_editor.html",
        title=f"Luo uusi viestiketju aiheeseen {topic_name}",
        submit="Luo viestiketju",
        action=f"/topic/{id}/new")

@app.route("/topic/<int:id>/new", methods=["POST"])
def newThreadSubmit(id):
    if notLoggedIn():
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
    db.session.execute(sql, {"user_id":getUserId(), "topic_id":id, "thread_name":thread_name, "thread_desc":thread_desc})
    db.session.commit()

    return redirect(f"/topic/{id}")
    





@app.route("/topic/new", methods=["GET"])
def newTopic_form():
    if notLoggedIn():
        return redirect("/")


    if getAuthLevel()<=1:
        return ("You don't have the necessary permissions to perform this task.")
    
    return render_template("topic_editor.html", title="Luo uusi aihe", submit="Luo aihe", action="/topic/new")



@app.route("/topic/new", methods=["POST"])
def create_new_topic():
    if notLoggedIn():
        return redirect("/")

    if request.form["privacy"]=="public":
        hidden=False
    else:
        hidden=True

    messages=parseTopicForm(True)

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

@app.route("/upgradeToAdmin")
def upgradeToAdmin():
    if notLoggedIn():
        return redirect("/")
    
    if not db.session.execute("SELECT * FROM users WHERE auth_level=2").fetchone(): #If there are no admin users, then upgrade the current one to admin status. This is just for testing.
        db.session.execute("UPDATE users SET auth_level=2 WHERE id=:id", {"id":getUserId()})
        db.session.commit()
    
    return redirect("/")

@app.route("/thread/<int:id>")
def showThread(id):
    if notLoggedIn():
        return redirect("/")

    check=checkTopicPerm(id)

    if check!=None:
        return check

    sql="SELECT Th.id, Th.thread_header, Th.thread_desc, Top.topic_name, Th.sent_at, Th.edited_at, U.username, U.auth_level FROM threads Th LEFT JOIN topics Top ON Th.topic_id=Top.id LEFT JOIN users U ON U.id=Th.poster_id WHERE Th.id=:id"
    thread_info=db.session.execute(sql, {"id":id}).fetchone()
    if not thread_info:
        return ("Thread not found :(")
    
    sql="SELECT U.username, U.auth_level, R.id, R.message, R.sent_at, R.edited_at FROM replies R LEFT JOIN users U ON U.id=R.poster_id WHERE thread_id=:thread_id ORDER BY R.sent_at"
    replies=db.session.execute(sql, {"thread_id":id})
    
    return render_template("thread.html", thread_info=thread_info, logged_user=session["username"], user_auth_level=getAuthLevel(), replies=replies)

@app.route("/thread/<int:id>/delete", methods=["GET"])
def confirmDeleteThread(id):
    if notLoggedIn():
        redirect("/")
    
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=checkTopicPerm(topic_id)

    if check!=None:
        return check

    sql="SELECT id, poster_id, thread_header FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()

    
    return render_template("delete_thread.html", thread=thread)

@app.route("/thread/<int:id>/delete", methods=["POST"])
def deleteThread(id):
    if notLoggedIn():
        return redirect("/")
    
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=checkTopicPerm(topic_id)

    if check!=None:
        return check
    
    sql="SELECT id, poster_id, thread_header FROM threads WHERE id=:id"
    thread=db.session.execute(sql, {"id":id}).fetchone()

    #TODO: delete all replies in the thread

    sql="DELETE FROM threads WHERE id=:id"
    db.session.execute(sql, {"id":id})
    db.session.commit()

    return redirect(f"/topic/{thread['topic_id']}")

@app.route("/thread/<int:id>/edit", methods=["GET"])
def editThreadForm(id):
    check=checkThreadEditPerm(id)

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
    
@app.route("/thread/<int:id>/edit", methods=["POST"])
def editThread(id):
    check=checkThreadEditPerm(id)
    
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

@app.route("/thread/<int:id>/new", methods=["GET"])
def newReplyForm(id):
    if notLoggedIn():
        return ("/")
     

    check=checkTopicPerm(id)

    if check!=None:
        return check

    #Get the name of the thread where the reply is being posted.
    thread=db.session.execute("SELECT thread_header FROM threads WHERE id=:id", {"id":id}).fetchone()[0] 

    return render_template("reply_editor.html", thread=thread, title="Vastaa viestiketjuun", submit="Vastaa")

@app.route("/thread/<int:id>/new", methods=["POST"])
def newReply(id):
    if notLoggedIn():
        return redirect("/")
    
    #Get the topic id and check if the user even has access to that topic.
    sql="SELECT topics.id FROM topics LEFT JOIN threads ON threads.topic_id=topics.id LEFT JOIN replies ON replies.thread_id=threads.id WHERE threads.id=:id"
    topic_id=db.session.execute(sql, {"id":id}).fetchone()[0] 

    check=checkTopicPerm(topic_id)

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
    db.session.execute(sql, {"user_id":getUserId(), "thread_id":id, "message":request.form["reply"]})
    db.session.commit()

    return redirect(f"/thread/{id}")

@app.route("/replies/<int:id>/delete", methods=["GET"])
def deleteReplyConfirm(id):
    if notLoggedIn():
        return redirect("/")

    if getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()

        if getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")

    sql="SELECT U.username, U.auth_level, R.id, R.message, R.sent_at, R.edited_at, R.thread_id FROM replies R LEFT JOIN users U ON U.id=R.poster_id WHERE R.id=:id"
    reply=db.session.execute(sql, {"id":id}).fetchone()

    if not reply:
        return ("Vastausta jota halusit muokata ei löydy.")

    return render_template("reply_delete.html", reply=reply)

@app.route("/replies/<int:id>/delete", methods=["POST"])
def deleteReply(id):
    if notLoggedIn():
        return redirect("/")
    

    if getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")
    
    thread_id=db.session.execute("SELECT thread_id FROM replies WHERE id=:id", {"id":id}).fetchone()
    if not thread_id:
        return ("Vastausta jota halusit muokata ei löydy")

    sql="DELETE FROM replies WHERE id=:id"
    db.session.execute(sql, {"id":id})
    db.session.commit()

    return redirect(f"/thread/{thread_id[0]}")

@app.route("/replies/<int:id>/edit", methods=["GET"])
def replyEditForm(id):
    if notLoggedIn():
        return redirect("/")
    
    if getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if getUserId()!=poster_id[0]:
            return ("Sinulla ei ole tarvittavia oikeuksia tähän operaatioon.")
    
    sql="SELECT T.thread_header, R.message FROM replies R LEFT JOIN threads T ON R.thread_id = T.id WHERE R.id = :id"
    reply=db.session.execute(sql, {"id":id}).fetchone()

    return render_template("reply_editor.html", 
        title=f"Muokkaa viestiä",
        thread = reply["thread_header"],
        reply=reply["message"],
        submit="Tallenna muutokset"
    )

@app.route("/replies/<int:id>/edit", methods=["POST"])
def editReply(id):
    if notLoggedIn():
        return redirect("/")
    
    if getAuthLevel()==0: #Check if the user can delete the reply
        sql="SELECT poster_id FROM replies WHERE id=:reply_id"
        poster_id=db.session.execute(sql, {"reply_id":id}).fetchone()
        if not poster_id:
            return ("Vastausta jota halusit muokata ei löydy.")

        if getUserId()!=poster_id[0]:
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
    

