from concurrent.futures import thread
from urllib import request
from flask import Flask
from flask import render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from os import access, getenv
from werkzeug.security import check_password_hash, generate_password_hash
import common
import topics
import threads
import accounts
import replies

app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)




@app.route("/")
def mainpage():
    return topics.mainPage()

@app.route("/topic/<int:id>")
def threads(id):
    return topics.threads(id)

@app.route("/topic/<int:id>/edit", methods=["GET"])
def editTopicForm(id):
    return topics.editTopicForm(id)

@app.route("/topic/<int:id>/edit", methods=["POST"])
def editTopicSubmit(id):
    return topics.editTopicSubmit(id)

@app.route("/topic/<int:id>/new", methods=["GET"])
def newThreadForm(id):
    return threads.newThreadForm(id)

@app.route("/topic/<int:id>/new", methods=["POST"])
def newThreadSubmit(id):
    return threads.newThreadSubmit(id)
    





@app.route("/topic/new", methods=["GET"])
def newTopicForm():
    return topics.newTopicForm()


@app.route("/topic/new", methods=["POST"])
def createNewTopic():
    return topics.createNewTopic()

@app.route("/login", methods=["GET"])
def loginForm():
    return accounts.loginForm()

@app.route("/login", methods=["POST"])
def login():
    return accounts.login()

    

@app.route("/signup", methods=["GET"])
def signupForm():
    return accounts.signupForm()

@app.route("/signup", methods=["POST"])
def signup():
    return accounts.signup()

@app.route("/signout")
def signout():
    return accounts.signout()

@app.route("/upgradeToAdmin")
def upgradeToAdmin():
    return accounts.upgradeToAdmin()

@app.route("/thread/<int:id>")
def showThread(id):
    return threads.showThread(id)

@app.route("/thread/<int:id>/delete", methods=["GET"])
def confirmDeleteThread(id):
    return threads.confirmDeleteThread(id)

@app.route("/thread/<int:id>/delete", methods=["POST"])
def deleteThread(id):
    return threads.deleteThread(id)

@app.route("/thread/<int:id>/edit", methods=["GET"])
def editThreadForm(id):
    return threads.editThreadForm(id)
    
@app.route("/thread/<int:id>/edit", methods=["POST"])
def editThread(id):
    return threads.editThread(id)

@app.route("/thread/<int:id>/new", methods=["GET"])
def newReplyForm(id):
    return replies.newReplyForm(id)

@app.route("/thread/<int:id>/new", methods=["POST"])
def newReply(id):
    return replies.newReply(id)

@app.route("/replies/<int:id>/delete", methods=["GET"])
def deleteReplyConfirm(id):
    return replies.deleteReplyConfirm(id)

@app.route("/replies/<int:id>/delete", methods=["POST"])
def deleteReply(id):
    return replies.deleteReply(id)

@app.route("/replies/<int:id>/edit", methods=["GET"])
def replyEditForm(id):
    return replies.replyEditForm(id)

@app.route("/replies/<int:id>/edit", methods=["POST"])
def editReply(id):
    return replies.editReply(id)
    

