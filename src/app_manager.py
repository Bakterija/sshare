from flask_login import UserMixin
from flask import redirect
from threading import Thread
from hashlib import sha512
from time import time
import app_globals
TIME0 = time()
from utils import dround
from logs import Logger
from copy import copy
import traceback
import platform
import shutil
import random
import utils
import json
import os


class AppManager(object):
    class _AppManager(object):
        DEFAULTS = app_globals.DEFAULT_CONFIG['AppManager']
        app = None
        app_name = DEFAULTS['app_name']
        app_title = DEFAULTS['app_title']
        dir_file_share = DEFAULTS['dir_file_share']
        upload_extensions = copy(DEFAULTS['upload_extensions'])
        root = DEFAULTS['root']
        web_url = DEFAULTS['root']
        login_background_image = DEFAULTS['login_background_image']
        login_background_color = DEFAULTS['login_background_color']
        uploaded_files = {}
        uploaded_file_paths = {}
        temp_files = {}
        users = {}
        requests_per_second = 0
        requests_total = 0
        max_file_share = 0
        proxy_fix_hostname = ''
        using_default_user = False

        def __init__(self, app, login_manager):
            self.app = app
            self.login_manager = login_manager
            if not os.path.exists(app_globals.DIR_CONF):
                os.makedirs(x)
            self.load_config()
            app_globals.manager = self
            app_globals.app = app
            app.config['SECRET_KEY'] = self.secret_key

        def add_user(self, name, password, save_config=True):
            Logger.info('AppManager: %s adding user' % (dround(self.uptime)))
            if not name in self.users:
                self.users[name] = User(name, password)
                if save_config:
                    self.save_config()
                return True

        def remove_user(self, name, save_config=True):
            Logger.info('AppManager: %s removing user' % (dround(self.uptime)))
            if name in self.users:
                del self.users[name]
                if save_config:
                    self.save_config()
                return True

        def get_unique_file_id(self):
            while True:
                random_string = utils.get_random_string(24)
                if random_string not in self.temp_files:
                    if random_string not in self.uploaded_files:
                        self.temp_files[random_string] = None
                        return random_string

        def get_file(self, file_id, ignore_temporary=False):
            f = self.uploaded_files.get(file_id, None)
            if not f and not ignore_temporary:
                f = self.temp_files.get(file_id, None)
            return f

        def get_file_by_path(self, fpath):
            fid = self.uploaded_file_paths.get(fpath, None)
            if fid:
                f = self.get_file(fid)
                return f

        def add_local_file(self, fpath, fname, use_name=None):
            fid = utils.get_random_string(24)
            if not use_name:
                use_name = fname
            self.add_file(fid, fpath, use_name, remove_temp=False)

        def add_file(self, fid, fpath, fname, remove_temp=True,
                     size=None, save_config=True):
            if remove_temp:
                del self.temp_files[fid]
            if not size:
                size = os.stat(fpath).st_size
            self.uploaded_file_paths[fpath] = fid
            self.uploaded_files[fid] = {
                'id': fid, 'path': fpath, 'name': fname, 'size': size}
            if save_config:
                self.save_config()

        def remove_file(self, fid):
            f = self.uploaded_files.get(fid, None)
            if f:
                os.remove(f['path'])
                del self.uploaded_files[fid]
                self.save_config()
                return True
            else:
                cpath = ''.join((self.dir_file_share, '/', fid))
                if os.path.exists(cpath):
                    os.remove(cpath)
                    return True

        def get_user(self, id):
            return self.users.get(id, None)

        @property
        def login_background_color_string(self):
            if self.login_background_color:
                return str(self.login_background_color)[1:-1]
            return ''

        @property
        def uploaded_files_all(self):
            fdict = copy(self.uploaded_files)
            for x in fdict:
                fdict[x]['uploaded'] = True
            dirfiles = os.listdir(self.dir_file_share)
            for x in dirfiles:
                fpath = '%s/%s' % (self.dir_file_share, x)
                if fpath not in self.uploaded_file_paths:
                    fdict[x] = {
                        'id': 'N/a (Local file)', 'name': x,
                        'size': os.stat(fpath).st_size,
                        'path': '%s/%s' % (self.dir_file_share, x),
                        'uploaded': False}
            return fdict

        @property
        def app_title(self):
            self.app.jinja_env.globals['TITLE'] = 'Simple Server'

        @app_title.setter
        def app_title(self, value):
            self.app.jinja_env.globals['TITLE'] = value

        @property
        def uploaded_file_count(self):
            cnt = len(os.listdir(self.dir_file_share))
            return str(cnt)

        @property
        def free_space(self):
            s = shutil.disk_usage(self.dir_file_share)
            if self.max_file_share:
                free = min(s[2] / 1000000, self.max_file_share)
            else:
                free = s[2] / 1000000
            return round(free)

        @property
        def uptime(self):
            return round(time() - TIME0, 2)

        @property
        def uptime_minutes(self):
            return round((time() - TIME0) / 60.0, 2)

        def load_config(self):
            _ignored = ('default_user', 'users')
            conf = self._read_config_file().get('AppManager', None)
            if conf:
                # Add missing cofigs from defaults
                save_config = False
                for x in self.DEFAULTS:
                    if x not in conf:
                        save_config = True
                        conf[x] = self.DEFAULTS[x]

                # Set manager attributes from config items
                for k, v in conf.items():
                    if k not in _ignored:
                        setattr(self, k, v)
                self.login_manager.login_view = self.url('/login')

                self.app.config['APPLICATION_ROOT'] = self.root
                if save_config:
                    self.save_config()

                # Remove missing files from uploaded_files dict
                fdel_list = []
                for x in self.uploaded_files:
                    x_path = self.uploaded_files[x]['path']
                    if os.path.exists(x_path):
                        x_id = self.uploaded_files[x]['id']
                        self.uploaded_file_paths[x_path] = x_id
                    else:
                        fdel_list.append(x)
                for x in fdel_list:
                    del self.uploaded_files[x]
                    Logger.info((
                        'AppManager: removed file with nonexistent path: '
                        ' %s' % (x)))

                # Initialise user objects from config
                if conf['users']:
                    cnt = 0
                    for k, v in conf['users'].items():
                        self.add_user(v['id'], v['password'], save_config=False)
                        cnt += 1

                if self.users:
                    Logger.info('AppManager: loaded %s users' % (cnt))

                else:
                    usr = conf['default_user']
                    self.add_user(usr[0], usr[1], save_config=False)
                    Logger.info((
                        'AppManager: No users in config, added '
                        'default user "%s" with password "%s"'
                        ) % (usr[0], usr[1]))
            else:
                Logger.info('AppManager: No config, using defaults')
                self.using_default_user = True

            udef = self.DEFAULTS['default_user']
            if udef[0] in self.users:
                if self.users[udef[0]].passwd == udef[1]:
                    self.using_default_user = True
                    Logger.info('AppManager: Using default user')

        def _read_config_file(self):
            try:
                if os.path.exists(app_globals.CONF_PATH):
                    try:
                        Logger.info('AppManager: %s Loading config' % (
                            dround(self.uptime)))
                        with open(app_globals.CONF_PATH, 'r') as f:
                            conf = json.load(f)
                        return conf
                    except json.JSONDecodeError:
                        self._write_default_config_json()
                else:
                    self._write_default_config_json()
                if not os.path.exists(self.dir_file_share):
                    os.makedirs(self.dir_file_share)
            except:
                Logger.critical('AppManager: Failed to load config')
                raise

        def _write_default_config_json(self):
            with open(app_globals.CONF_PATH, 'w') as f:
                json.dump(app_globals.DEFAULT_CONFIG, f, indent=4)
                Logger.info('AppManager: wrote default config to file')

        def save_config(self):
            Logger.info('AppManager: %s save_config' % (dround(self.uptime)))
            with open(app_globals.CONF_PATH, 'w') as f:
                sdict = copy(app_globals.DEFAULT_CONFIG)
                users = {}
                for k, v in self.users.items():
                    users[k] = {
                        'id': v.id, 'name': v.name, 'password': v.passwd}
                appm = [
                    ('app_name', self.app_name), ('root', self.root),
                    ('dir_file_share', self.dir_file_share),
                    ('upload_extensions', self.upload_extensions),
                    ('uploaded_files', self.uploaded_files),
                    ('users', users)
                ]
                for a, b in appm:
                    sdict['AppManager'][a] = b
                json.dump(sdict, f, indent=4)

        def before_request(self):
            self.requests_total += 1
            self.requests_per_second = round(self.requests_total / self.uptime, 2)

        def url(self, page):
            if page:
                page = ''.join((self.root, page))
            return page

    instance = None
    def __init__(self, *args):
        if not AppManager.instance:
            AppManager.instance = AppManager._AppManager(*args)
    def __getattr__(self, name):
        return getattr(self.instance, name)


class User(UserMixin):
    is_authenticated = False
    is_active = False
    is_anonymous = True
    passwd = None
    id = None

    def __init__(self, id, passwd):
        self.is_anonymous = False
        self.passwd = passwd
        self.id = id

    @property
    def name(self):
        return self.id

    def properties(self):
        return {
            'is_authenticated': self.is_authenticated,
            'id': self.name, 'passwd': self.passwd,
            'is_active': self.is_active}

    def get_id(self):
        return str(self.id)
