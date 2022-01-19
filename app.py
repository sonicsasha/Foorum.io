from urllib import request
from flask import Flask
from flask import render_template, request
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]=getenv("DATABASE_URL")
db = SQLAlchemy(app)

@app.route("/")
def login_form():
    return render_template("login_form.html")

@app.route("/login", methods=["POST"])
def login():
    return("Whoops, this isn't complete yet! :3")

