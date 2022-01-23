# Foorumi
A project for the course "Application for Databases" at University of Helsinki. This is a simple forum where users can create an account, select a specific topic, create a new thread for that topic and respond to threads created by other users.

# Users
Anyone can create a user account and log in to their account. There are three levels of account power: User, Moderator and Admin.

A user can create threads, respond to other threads, edit their own messages as well as delete them.

A moderator can do anything a user can do, but also create new topics including hidden ones where only specific users are allowed to access them and delete any message on any thread.

An admin can do everything a moderator can do, but also nominate other users to a moderator or an admin status, as well as edit any messages on the forum.

# Current status (as of 23.1.2022)
Right now users can create an account and also log in to said account. Admins can create new topics, moderators can see all topics, while regular users can only see public topics and topics that an admin has allowed them to see. Setting up an admin account can currently be done through psql with an account that has already been created. You can elevate yourself to an admin account with the following command:

`UPDATE users SET auth_level=2 WHERE username='your_username';`
