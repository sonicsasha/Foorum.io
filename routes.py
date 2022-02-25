import topics
import msg_threads
import accounts
import replies
import search
import admin
from app import app

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
    return msg_threads.newThreadForm(id)

@app.route("/topic/<int:id>/new", methods=["POST"])
def newThreadSubmit(id):
    return msg_threads.newThreadSubmit(id)

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
    return msg_threads.showThread(id)

@app.route("/thread/<int:id>/delete", methods=["GET"])
def confirmDeleteThread(id):
    return msg_threads.confirmDeleteThread(id)

@app.route("/thread/<int:id>/delete", methods=["POST"])
def deleteThread(id):
    return msg_threads.deleteThread(id)

@app.route("/thread/<int:id>/edit", methods=["GET"])
def editThreadForm(id):
    return msg_threads.editThreadForm(id)
    
@app.route("/thread/<int:id>/edit", methods=["POST"])
def editThread(id):
    return msg_threads.editThread(id)

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

@app.route("/search", methods=["GET"])
def searchForm():
    return search.searchForm()

@app.route("/search", methods=["POST"])
def getSearchResults():
    return search.getSearchResults()

@app.route("/admin", methods=["GET"])
def adminForm():
    return admin.adminForm()

@app.route("/admin/nominate", methods=["GET"])
def nominateForm():
    return admin.nominateForm()

@app.route("/admin/nominate", methods=["POST"])
def nominate():
    return admin.nominate()

@app.route("/admin/ban", methods=["GET"])
def banForm():
    return admin.banForm()

@app.route("/admin/ban", methods=["POST"])
def banUser():
    return admin.banUser()

@app.route("/admin/unban", methods=["POST"])
def unbanUser():
    return admin.unbanUser()
