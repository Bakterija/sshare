class CustomProxyFix(object):
    def __init__(self, app, app_root):
        self.app = app
        self.app_root = app_root
        Logger.warning('CustomProxyFix: init: %s' % (app_root))

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        environ['PATH_INFO'] = '/sss/'

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        environ['HTTP_X_FORWARDED_HOST'] = environ['PATH_INFO']
        Logger.info('Cproxy %s %s %s' % (
            app_globals.manager.uptime, environ['SCRIPT_NAME'],
            environ['PATH_INFO']))
        return self.app(environ, start_response)
