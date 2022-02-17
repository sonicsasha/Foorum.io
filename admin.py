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
    
    if request.form["nominate_type"]=="admin":
        db.session.execute("UPDATE users SET auth_level=2 WHERE username=:username", {"username":request.form["user"]})
        db.session.commit()
    
    return redirect("/admin/nominate")
    
def banForm():
    if common.notLoggedIn():
        abort(404)
    
    if common.getAuthLevel()<2:
        abort(404)
    
    sql="SELECT U.username FROM users U LEFT JOIN bans B ON B.user_id=U.id WHERE B.user_id IS NULL"
    users=db.session.execute(sql).fetchall()

    sql="SELECT U.username FROM users U LEFT JOIN bans B ON B.user_id=U.id WHERE B.user_id=U.id"
    banned_users=db.session.execute(sql).fetchall()

    return render_template("admin_ban.html", users=users, banned_users=banned_users)

def banUser():

    if common.notLoggedIn():
        abort(404)
    
    if common.getAuthLevel()<2:
        abort(404)
    
    sql="SELECT id FROM users WHERE username=:username"
    user_id=db.session.execute(sql, {"username":request.form["ban_user"]}).fetchone()
    reason=request.form["ban_reason"]

    if not user_id:
        return render_template("admin_ban.html", messages=["Käyttäjää ei löytynyt. Yritä uudelleen!"])

    try:
        db.session.execute("INSERT INTO bans VALUES (:user_id, :reason)", {"user_id":user_id[0], "reason":reason})
        db.session.commit()
    except:
        return render_template("admin_ban.html", messages=["Käyttäjälle on jo asetettu käyttökielto!"])

    return redirect("/admin/ban")

def unbanUser():

    if common.notLoggedIn():
        abort(404)
    
    if common.getAuthLevel()<2:
        abort(404)
    
    sql="SELECT id FROM users WHERE username=:username"
    user_id=db.session.execute(sql, {"username":request.form["unban_user"]}).fetchone()

    if not user_id:
        return render_template("admin_ban.html", unban_messages=["Käyttäjää ei löytynyt. Yritä uudelleen!"])
    
    db.session.execute("DELETE FROM bans WHERE user_id=:user_id", {"user_id":user_id[0]})
    db.session.commit()

    return redirect ("/admin/ban")
