#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True
from gevent import pywsgi, monkey; monkey.patch_all()
import app_manager
from logs import Logger, GeventLoggerInfo, GeventLoggerError
from flask import Flask, Markup, Response, Blueprint, render_template, request
from flask import redirect, url_for, send_from_directory, flash, session
from flask import jsonify
from server_funcs import allowed_file, create_file_share_link, is_safe_url
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, login_user, current_user
from functools import wraps
from utils import dround
from time import time
import app_globals
import traceback
import flask_login
import flask
import os

app = Flask(__name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    user = manager.get_user(user_id)
    return user

@app.before_request
def before_request():
    manager.before_request()

@app.after_request
def after_request(response):
    return response

@app.route('/')
def index_page():
    uid = current_user.get_id()
    args = ''
    if flask.request.args.get('logged_out'):
        args = '?message=Logged out'

    if uid:
        if current_user.is_active and current_user.is_authenticated:
            return redirect(manager.url('/main'))
        else:
            return redirect(manager.url('/login%s' % (args)))
    else:
        return redirect(manager.url('/login%s' % (args)))

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = manager.url(flask.request.args.get('next'))
    message = ''
    message2 = flask.request.args.get('message')
    if message2:
        message = message2
    if 'user_id' in session:
        user = load_user(session['user_id'])
        if not user:
            session.clear()
            return redirect(manager.url('/'))

    if request.method == 'POST':
        if not next_url:
            next_url = manager.url('/main')

        user = load_user(request.form['username'])
        if user and user.passwd == request.form['password']:
            user.is_active = True
            user.is_authenticated = True

            result = login_user(user)

            if not is_safe_url(next_url):
                return flask.abort(400)

            return redirect(next_url)
        else:
            message = 'Incorrect user name or password'
            return render_template('login.htm', message=message)
    else:
        if next_url:
            message = 'Not logged in yet'
            if len(next_url) > 7 and '/log_out' == next_url[-8:]:
                return redirect(manager.url('/'))
        return render_template('login.htm', message=message)

@app.route('/log_out')
@login_required
def log_out():
    flask_login.logout_user()
    return redirect(manager.url('?logged_out=1'))

@app.route('/main')
@login_required
def user_main():
    return render_template('user_main.htm')

@app.route('/upload', methods=['GET', 'POST'])
@app.route('/upload/<err>', methods=['GET', 'POST'])
@login_required
def upload_file(err=""):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return manager.url('/upload/1')
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return manager.url('/upload/2')
        if file:
            allowed = True
            if manager.upload_extensions and not allowed_file(file.filename):
                allowed = False
            if allowed:
                filename = secure_filename(file.filename)
                fid = manager.get_unique_file_id()
                file.save(os.path.join(manager.dir_file_share, fid))
                flink = manager.url('/file/%s' % (fid))
                manager.add_file(
                    fid, '%s/%s' % (manager.dir_file_share, fid),
                    filename)
                return flink
            else:
                return manager.url('/upload/3')

    if err:
        if err == '1':
            err = 'No file part'
        elif err == '2':
            err = 'No selected file'
        elif err == '3':
            err = 'File extension not allowed'
    return render_template('upload.htm', err=err)

@app.route('/remove_file/<file_id>')
@login_required
def remove_file(file_id):
    ret = manager.remove_file(file_id)
    if ret:
        return redirect(manager.url('/file_list'))
    else:
        return render_template(
            'error.htm', error="Could not remove file with id %s" % (file_id))

@app.route('/add_private_file/<file_name>')
@login_required
def add_private_file(file_name):
    fpath = '%s/%s' % (manager.dir_file_share, file_name)
    f = manager.get_file_by_path(fpath)
    if f:
        return render_template('error.htm', error='File is added already')
    else:
        manager.add_local_file(fpath, file_name)
        return redirect(manager.url('/file_list'))

@app.route('/file/<file_hash>')
def get_file(file_hash):
    ulfile = manager.uploaded_files.get(file_hash, None)
    if ulfile:
        return render_template('file.htm', ulfile=ulfile)
    else:
        return render_template('error.htm', error="No file with this id")

@app.route('/download_file/<file_hash>')
def download_file(file_hash):
    ulfile = manager.get_file(file_hash, ignore_temporary=True)
    if ulfile:
        udir, uname = os.path.split(ulfile['path'])
        return send_from_directory(udir, uname)
    else:
        return render_template('error.htm', error="No file with this id")

@app.route('/file_list')
@login_required
def get_files():
    all_files = manager.uploaded_files_all
    for x in all_files:
        if all_files[x]['uploaded']:
            all_files[x]['class'] = 'w3-text-black'
        else:
            all_files[x]['class'] = 'w3-text-red'
    ret = render_template(
        'file_list.htm', files=all_files.items())
    return ret

@app.route('/administrate')
@login_required
def administrate():
    return render_template('administrate.htm')

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    j = request.get_json()
    manager.add_user(j['name'], j['password'])
    return jsonify({})

@app.route('/remove_user', methods=['GET', 'POST'])
@login_required
def remove_user():
    j = request.get_json()
    manager.remove_user(j['uid'])
    return jsonify({})

def start():
    global manager, app, login_manager
    manager = app_manager.AppManager(app, login_manager)
    login_manager.init_app(app)
    app.jinja_env.globals['manager'] = manager

    server = pywsgi.WSGIServer(
        ('0.0.0.0', 7114), app,
        # log=GeventLoggerInfo(), error_log=GeventLoggerError()
        log=None
        )
    Logger.info('Server: %s init' % (round(time() - app_manager.TIME0, 2)))
    server.serve_forever()

if __name__ == "__main__":
    start()
