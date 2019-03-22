# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_flex_quickstart]
import logging
import os
from lib import vision
from lib.Document import Document
from lib.Paragraph import ParagraphHelper

from flask import Flask, render_template, request, flash, redirect

template_dir = './frontend'
app = Flask(__name__, template_folder=template_dir)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template('index.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    """POST request to upload file

    TODO:
        * Reject files that are too large
    """
    # check if the post request has the file part
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    if not file or not allowed_file(file.filename):
        return "File extension not allowed", 400

    doc = vision.load_document(file)
    if not doc:
        return 'Bad Image Data', 400
    p = ParagraphHelper(doc=doc)
    paragraph_list = p.get_paragraph_list()
    questions = Document(paragraph_list, p.avg_symbol_width, p.avg_symbol_height).create_questions()

    return questions.json()['url'], 200


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_flex_quickstart]
