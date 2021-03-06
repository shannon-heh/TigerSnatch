-------------------------------------------------------
Deploying the PennyFlaskCasHeroku Application to Heroku
-------------------------------------------------------

This document provides a minimal set of instructions that you can
perform to deploy the PennyFlaskCasHeroku application to Heroku.

An upcoming lecture will describe a more graphical (and more realistic)
approach that involves first pushing your application to a GitHub
repository, and then pulling your application from the GitHub
repository to Heroku.

(1) Install and configure git, as described in the optonal "Version Control Systems" lecture.

(2) Create a directory named PennyFlaskCasHeroku.  Place all files
that define the application in that directory.

(3) Create a file named Procfile in PennyFlaskCasHeroku.  The contents
tell Heroku the application's process type (web application), and tell
Heroku the command that it should use to run the application.

(4) Create a file named runtime.txt in PennyFlaskCasHeroku.  The
contents tell Heroku which version of Python to use.

(5) Create a file named requirements.txt in PennyFlaskCasHeroku.  The
contents tell Heroku what additional modules the application uses.

(6) Get a Heroku account.  To do that, browse to:

   https://signup.heroku.com/dc
   
Choose Python as the primary development language.  Enter the email
address.  Choose a password.

(7) Install the Heroku Command Line Interface (CLI).  To do that,
browse to:

  https://devcenter.heroku.com/articles/heroku-cli
  
and follow the instructions.

(8) Log into Heroku.  To do that, issue this command:

   heroku login

(9) Create a Git repository on Heroku.  To do that, issue this command:

   heroku create
   
Heroku responded with the name of the application, which is also the
name of the Git repository.  The application name was
morning-savannah-98758.

(10) Create a local Git repository.  To do that, while
PennyFlaskCasHeroku is the working directory issue these commands:

   git init
   git add .
   git commit -m "initial load"

(11) Specify the Heroku Git repository as the remote of the local Git
repository.  To do that, while PennyFlaskCasHeroku is the working
directory issue this command:

   heroku git:remote -a morning-savannah-98758

(12) Optionally, confirm that the remote repository is set properly
by issuing this command:

   git remote -v
   
(13) Deploy the application to Heroku.  To do that, while
PennyFlaskCasHeroku is the working directory issue this command:
   
   git push heroku master
   
Git uploads the application to the Heroku repository.  Then Heroku
automatically builds and deploys the application.

(14) Run the Heroku application.  To do that, browse to:

   https://morning-savannah-98758.herokuapp.com


   
