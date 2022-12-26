# Foorum.io
A project for the course "Application for Databases" at University of Helsinki. This is a simple forum where users can create an account, select a specific topic, create a new thread for that topic and respond to threads created by other users.

## How to run
Clone this repository to your computer. Go to the project directory in the terminal and run
```bash
pip install -r requirements.txt
```
to install the dependencies required by the program.

After that create a .env file. Add a SECRET_KEY parameter and set it to whatever you want. After that add a DATABASE_URL parameter with a link to a PostgreSQL server. For example, the contents of the .env file could be
```.env
SECRET_KEY=secretysecret
DATABASE_URL=postgres://
```

Finally, to start the application, execute the command
```bash
flask run
```
in the project directory. After this, the website should be running at https://localhost:5000

## Users
Anyone can create a user account and log in to their account. There are three levels of account power: User, Moderator and Admin.

A user can create threads, respond to other threads, edit their own messages as well as delete them.

A moderator can do anything a user can do, but also create new topics including hidden ones where only specific users are allowed to access them and delete any message on any thread.

An admin can do everything a moderator can do, but also nominate other users to a moderator or an admin status, as well as edit any messages on the forum.

## Current status (as of 17.2.2022)
- Users can create an account and log in into said account (unless they are banned)
- Admins can create new topics and also edit said topics
- Admins can create either public or private topics. If the topic is private, then an admin can edit who can see said topic.
- Users can create new threads and also edit or delete their own threads (admins and moderators can edit and delete any thread)
- Users can reply to threads and also edit or delete their own replies (admins and moderators can edit and delete any reply)
- Users can search for topics, threads and replies using keywords.
- Admins can access a special admin page, where they can nominate users to an admin or a moderator role, and also ban and unban users.

# Heroku
You can test the app yourself over at https://foorum-io.herokuapp.com/
