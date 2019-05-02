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
import json
from lib.Vision import Vision
from lib.Document import Document
from lib.Paragraph import ParagraphHelper
from lib.Quizlet import Quizlet
from lib.scripts import text_summarize
import nltk
import base64

from flask import Flask, render_template, request, flash, redirect, Response, jsonify
from google.cloud import bigquery
from datetime import datetime
from anytree.exporter import DictExporter

template_dir = './frontend'
app = Flask(__name__, template_folder=template_dir)

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])

WORD_EMBEDDINGS = None

@app.before_first_request
def init_server():
    # intialize model for extractive summary
    global WORD_EMBEDDINGS
    WORD_EMBEDDINGS = text_summarize.extract_word_vec()

    print('initialized server')

def log_upload_req(json_rows):
    bq_client = bigquery.Client()
    dataset_id = 'logs'
    table_id = 'upload_post_requests'
    table_ref = bq_client.dataset(dataset_id).table(table_id)
    table = bq_client.get_table(table_ref)

    errors = bq_client.insert_rows_json(table, json_rows, ignore_unknown_values=True)

    if errors:
        print("Big Query Error: %s" % errors)

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
    d = Document(paragraph_list, p.avg_symbol_width, p.avg_symbol_height, WORD_EMBEDDINGS)
    terms, definitions = d.create_questions()

    if not (terms and definitions):
        return 'No questions extracted from ' + '%s.%s' % (vis.file_name, vis.file_ext), 400

    bq_row_obj = {
        'filename': file.filename,
        'ext': file.filename.rsplit('.', 1)[1].lower(),
        'paragraph_list': [paragraph['text'] for paragraph in paragraph_list],
        'doc_struct': json.dumps(DictExporter(attriter=lambda attrs: [(k, v) for k, v in attrs if k == "text"]).export(d.root_node)),
        'doc_border': {
            'top_left': { 'x': float(vis.doc_border[0][0]), 'y': float(vis.doc_border[0][1]) },
            'top_right': { 'x': float(vis.doc_border[1][0]), 'y': float(vis.doc_border[1][1]) },
            'bot_left': { 'x': float(vis.doc_border[3][0]), 'y': float(vis.doc_border[3][1]) },
            'bot_right': { 'x': float(vis.doc_border[2][0]), 'y': float(vis.doc_border[2][1]) }
        } if vis.doc_border is not None else None,
        'img_scale': vis.image_scale,
        'corrected_perspective': vis.is_corrected_perspective,
        'terms': terms,
        'definitions': definitions,
        'time_received': datetime.timestamp(datetime.now()),
        'orig_img_bytes': base64.b64encode(vis.orig_img_bytes).decode("utf-8"),
        'processed_img_bytes': base64.b64encode(vis.process_img_bytes).decode("utf-8"),
        'ip_address': request.environ['REMOTE_ADDR']
    }

    log_upload_req([bq_row_obj])

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
