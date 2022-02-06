# Foorumi
A project for the course "Application for Databases" at University of Helsinki. This is a simple forum where users can create an account, select a specific topic, create a new thread for that topic and respond to threads created by other users.

# Users
Anyone can create a user account and log in to their account. There are three levels of account power: User, Moderator and Admin.

A user can create threads, respond to other threads, edit their own messages as well as delete them.

A moderator can do anything a user can do, but also create new topics including hidden ones where only specific users are allowed to access them and delete any message on any thread.

An admin can do everything a moderator can do, but also nominate other users to a moderator or an admin status, as well as edit any messages on the forum.

# Current status (as of 6.2.2022)
- Users can create an account and log in into said account
- Admins can create new topics and also edit said topics
- Admins can create either public or private topics. If the topic is private, then admin can edit who can see said topic.
- Users can create new threads and also edit or delete their own threads (admins and moderators can edit and delete any thread)
- Users can reply to threads

# TODO
- Editing and deleting replies to threads.
- Search functionality.
- Fix CSS when selecting a thread or a topic.
- An admin page, where admins can nominate other users to either admin status or moderator status. (Right now if there are no admin accounts, the user can go to /upgradeToAdmin to upgrade their own account to admin status.)
- Deleting topics?

