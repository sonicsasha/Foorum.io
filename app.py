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


@app.route("/")
def mainpage():
    if notLoggedIn():
        return redirect("/login")

    user_id = getUserId()
    auth_level = getAuthLevel()

    if auth_level>=1: #Moderators and admins can see all topics
        sql="SELECT T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T;"
    else:
        sql="SELECT T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN topicsAccess TA ON TA.topic_id=T.id  WHERE T.is_hidden=False OR TA.user_id=:user_id;"
    
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
    
    if is_hidden[0]==True:
        has_access=db.session.execute("SELECT topic_id FROM topicsAccess WHERE topic_id=:id AND user_id=:user_id", {"id":id, "user_id":getUserId()}).fetchone()
        if not has_access: #If the topic is private, then check that the user has access to the topic.
            return ("Sinulla ei ole pääsyä tähän aiheeseen. Mene pois! >:(")
    
    sql="SELECT U.username, T.thread_header, T.thread_desc, T.sent_at, T.edited_at FROM threads T LEFT JOIN users U ON U.id=T.poster_id WHERE T.topic_id=:topic_id"
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
    sql="SELECT U.username FROM users U LEFT JOIN topicsAccess TA ON TA.topic_id=:id AND U.id=TA.user_id"
    for user in db.session.execute(sql, {"id":id}).fetchall(): #Get the usernames that have access to the topic.
        access+=f"{user[0]}, "

    return render_template(
        "topic_editor.html",
        title="Muokkaa aihetta",
        submit="Tallenna muutokset",
        action=f"/topic/{int}/edit",
        topic=topic,
        access=access)




@app.route("/topic/new", methods=["GET"])
def newTopic_form():
    if notLoggedIn():
        return redirect("/")

    try:
        if getAuthLevel()<=1:
            return ("You don't have the necessary permissions to perform this task.")
        
        return render_template("topic_editor.html", title="Luo uusi aihe", submit="Luo aihe", action="/topic/new")

    except:
        return redirect("/")

@app.route("/topic/new", methods=["POST"])
def create_new_topic():
    if notLoggedIn():
        return redirect("/")

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
    if db.session.execute("SELECT id FROM topics WHERE topic_name=:name", {"name":topic_name}).fetchone():
        messages.append("Ole hyvä, ja valitse aiheelle jokin muu nimi!")

    access_names=request.form["access"].replace(" ","").split(",") #Check if every user who is supposed to see the topic actually exists.
    if access_names[0]!='':
        for name in access_names:
            id=db.session.execute("SELECT id FROM users WHERE username=:name", {"name":name}).fetchone()
            if not id:
                messages.append(f"Käyttäjää {name} ei löytynyt!")
    
    if len(messages)>0:
        print(topic_name)
        return render_template("topic_editor.html", messages=messages, topic_name=topic_name, topic_desc=topic_desc, access=access)
    

    
    sql="INSERT INTO topics (topic_name, topic_desc, is_hidden) VALUES (:name, :desc, :hidden);"
    db.session.execute(sql, {"name":topic_name, "desc":topic_desc, "hidden":hidden})
    db.session.commit()

    topic_id=db.session.execute("SELECT id FROM topics WHERE topic_name=:name", {"name":request.form["name"]}).fetchone()[0]

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


