# Quiz App

A quiz web app which converts the text images into questions which are uploaded to quizlet

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

What things you need to install the software and how to install them:
```
python3/pip (https://www.python.org/downloads/)
virtualenv (https://virtualenv.pypa.io/en/stable/installation/)
git (https://git-scm.com/)
gsutils
docker
gcloud
```

### Installing

A step by step series of examples that tell you how to get a development env running

1. Clone the repo locally

```
git clone https://github.com/matthewwong525/quiz-app
```

2. Setup virtualenv and install dependencies

```
cd quiz-app
virtualenv quiz_app_env
source quiz_app_env/bin/activate
pip3 install -r requirements.txt (or pip install -r requirements.txt)
```

3. Downloading credentials file from the google cloud bucket

Download the entire `credentials` directory from (https://console.cloud.google.com/storage/browser/myquizpal.appspot.com/?project=myquizpal) into the `quiz-app` folder or run the following commands below in your `quiz-app` folder

```
gsutil cp -r gs://myquizpal.appspot.com/credentials .
```

Note: you need permissions to do this

4. Test if everything works!

Run script below to see if everything works! A local server should start and you should be able to develop locally

```
python3 main.py (or python main.py)
```


## File Structure

### main.py

Everything starts off from `main.py` this is where the flask web servers are hosted. The server calls from the lib folder to interpret the images and call online libraries, servers html from the frontend folder, and calls upon static files in the static folder from the frontend.

### lib

The lib folder contains all the python classes and scripts used to interpret the images

### static

The static folder contains all the static files that are usually accessed by the frontend

### frontend

Contains the html templates used in the frontend

## Image --> Question Conversion Workflow

1. Image is uploaded from the website into the `/upload POST` endpoint
2. Image is loaded into Google Vision API and the full text annotation is captured (lib/vision.py)
3. Full text annotation is loaded into the Pargraph helper which produces a list of words (lib/Paragraph.py)
4. Paragraph List is created from the list of words fromt he `get_paragraph_list()` function (lib/Paragraph.py)
5. Document is intialized and tree structure is created for the document (lib/Document.py)
6. Questions are created from the `create_questions()` function and uploaded to quizlet (lib/Document.py)
7. Quizlet URL is returned from the endpoint and frontend is updated

