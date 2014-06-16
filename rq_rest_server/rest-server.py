#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask.ext.httpauth import HTTPBasicAuth
import shell as sh
import json
import sys
app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()
url = "mobiledevices@b1.dev.g8teway.com"
@auth.get_password
def get_password(username):
    if username == 'hoang':
        return 'mdipass'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify( { 'error': 'Unauthorized access' } ), 403)
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

def jsonify_queues(queues):
    return json.dumps(queues)

@app.route('/rq/api/v1.0/queues', methods = ['GET'])
@auth.login_required
def get_queues():
    return jsonify_queues(sh.get_queues_all_size(url))

@app.route('/rq/api/v1.0/queues/<int:queue_size>', methods = ['GET'])
@auth.login_required
def get_queue(queue_size):
    return jsonify_queues(sh.get_queues_with_size(url, queue_size))

if __name__ == '__main__':
    app.run(debug = True)
