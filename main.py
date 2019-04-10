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
from lib.Vision import Vision
from lib.Document import Document
from lib.Paragraph import ParagraphHelper
from lib.Quizlet import Quizlet

from flask import Flask, render_template, request, flash, redirect, Response, jsonify

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
    num_files = request.form['num_files']

    if not str.isdigit(num_files) or int(num_files) > 5:
        return "No more than 5 files", 400

    if file.filename == '':
        return "No selected file" , 400

    if not file or not allowed_file(file.filename):
        return "File extension not allowed", 400

    vis = Vision(file)
    if not hasattr(vis, 'word_list'):
        return '%s.%s' % (vis.file_name, vis.file_ext) + ' has Bad Image Data', 400
    p = vis.get_paragraph_helper()
    paragraph_list = p.get_paragraph_list()
    d = Document(paragraph_list, p.avg_symbol_width, p.avg_symbol_height)
    terms, definitions = d.create_questions()

    if not (terms and definitions):
        return 'No questions extracted from ' + '%s.%s' % (vis.file_name, vis.file_ext), 400

    return jsonify({'terms': terms, 'definitions': definitions})


@app.route('/question_set', methods=['POST'])
def get_question_set():
    body = request.get_json()
    terms = body['terms']
    definitions = body['definitions']

    quizlet_client = Quizlet(terms, definitions)
    resp = quizlet_client.create_set(body['filename'] + " Question Set")
    
    # logs document structure and question response from quizlet
    if not resp or resp.status_code >= 400:
        return 'Failed to create question set', 400
    return jsonify(resp.json()), 200

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
