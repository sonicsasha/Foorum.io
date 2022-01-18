from urllib import request
from flask import Flask
from flask import render_template, request

app = Flask(__name__)

@app.route("/")
def login_form():
    return render_template("login_form.html")

@app.route("/login", methods=["POST"])
def login():
    return("Whoops, this isn't complete yet! :3")

