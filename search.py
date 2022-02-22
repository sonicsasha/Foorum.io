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



def searchForm():
    if common.notLoggedIn():
        return redirect("/")

    return render_template("search.html")

def getSearchResults():
    if common.notLoggedIn():
        return redirect("/")
    
    common.CSRFCheck()
    
    messages=[]

    query=request.form["query"]

    if query.strip()=="":
        messages.append("Ole hyvä, ja anna hakusana!")

    try:
        request.form["search_type"]
    except:
        messages.append("Ole hyvä, ja valitse hakukohde!")


    if len(messages)>0:
        return render_template("search.html", query=query, messages=messages)

    if request.form["search_type"]=="topic":
        user_id = common.getUserId()
        auth_level = common.getAuthLevel()

        if auth_level>=1: #Moderators and admins can see all topics
            sql="SELECT COUNT(threads.id), T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN threads ON threads.topic_id=T.id WHERE T.topic_name LIKE :query OR T.topic_desc LIKE :query GROUP BY T.id ORDER BY T.id;"
        else:
            sql="SELECT COUNT(threads.id), T.id, T.topic_name, T.topic_desc, T.is_hidden FROM topics T LEFT JOIN topicsAccess TA ON TA.topic_id=T.id LEFT JOIN threads ON threads.topic_id=T.id WHERE (T.is_hidden=False OR TA.user_id=:user_id) AND (T.topic_name LIKE :query OR T.topic_desc LIKE :query) GROUP BY T.id ORDER BY T.id;"
        
        results=db.session.execute(sql, {"user_id":user_id, "query":"%"+query+"%"}).fetchall()
        result_type="topic"
    
    
    elif request.form["search_type"]=="thread":
        if common.getAuthLevel()>=1:
            sql="SELECT T.id, U.username, U.auth_level, T.thread_header, T.thread_desc, T.sent_at, T.edited_at, topics.topic_name, MAX(R.sent_at), COUNT(R.sent_at) FROM threads T LEFT JOIN users U ON U.id=T.poster_id LEFT JOIN replies R ON R.thread_id=T.id LEFT JOIN topics ON T.topic_id = topics.id WHERE T.thread_header LIKE :query OR T.thread_desc LIKE :query GROUP BY T.id, U.username, U.auth_level, topics.topic_name ORDER BY T.sent_at DESC"
        else:
            sql="SELECT T.id, U.username, U.auth_level, T.thread_header, T.thread_desc, T.sent_at, T.edited_at, MAX(R.sent_at), COUNT(R.sent_at), topics.topic_name FROM threads T LEFT JOIN users U ON U.id=T.poster_id LEFT JOIN replies R ON R.thread_id=T.id LEFT JOIN topics ON T.topic_id = topics.id LEFT JOIN topicsAccess TA ON TA.topic_id=topics.id WHERE (topics.is_hidden = False OR TA.user_id=:user_id) AND (T.thread_header LIKE :query OR T.thread_desc LIKE :query) GROUP BY T.id, U.username, U.auth_level, topics.topic_name ORDER BY T.sent_at DESC"
        
        results=db.session.execute(sql, {"query":"%"+query+"%", "user_id":common.getUserId()}).fetchall()
        result_type="thread"

    
    elif request.form["search_type"]=="reply":
        if common.getAuthLevel()>=1:
            sql="SELECT U.username, U.auth_level, R.message, R.sent_at, R.edited_at, T.thread_header, T.id FROM replies R LEFT JOIN users U ON U.id=R.poster_id LEFT JOIN threads T ON R.thread_id = T.id WHERE R.message LIKE :query ORDER BY R.sent_at"
        else:
            sql="SELECT U.username, U.auth_level, R.message, R.sent_at, R.edited_at, T.thread_header, T.id FROM replies R LEFT JOIN users U ON U.id=R.poster_id LEFT JOIN threads T ON R.thread_id = T.id LEFT JOIN topics ON T.topic_id = topics.id LEFT JOIN topicsAccess TA ON TA.topic_id=topics.id WHERE (topics.is_hidden=False OR TA.user_id = :user_id) AND (R.message LIKE :query) ORDER BY R.sent_at"
        
        results=db.session.execute(sql, {"query":"%"+query+"%", "user_id":common.getUserId()}).fetchall()
        result_type="reply"


    if not results:
        return render_template("search.html", query=query, messages=["Ei hakutuloksia!"])
        
    return render_template("search.html", results=results, result_type=result_type, query=query)