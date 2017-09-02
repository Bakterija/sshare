from urllib.parse import urlparse, urljoin
from flask import Flask, Markup, Response, render_template, request
from flask import redirect, url_for, send_from_directory, flash
from logs import Logger, GeventLoggerInfo, GeventLoggerError
from functools import wraps
import app_globals as gvars
import utils


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    user = gvars.manager.get_user(username)
    if user:
        return user.id == username and password == user.passwd

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in gvars.manager.upload_extensions

def create_file_share_link():
    new_link = gvars.manager.url('/file/%s' % (utils.get_random_string(24)))
    return new_link

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc
