import platform
import string
import os

manager = None
app = None

DIR_HOME = os.path.expanduser("~")
if platform.system() == 'Linux':
    DIR_CONF = '%s/.config/github_bakterija/ss_share' % (DIR_HOME)
else:
    DIR_CONF = '%s/github_bakterija/ss_share' % (DIR_HOME)
CONF_PATH = '%s/config.json' % (DIR_CONF)

DEFAULT_CONFIG = {
    'AppManager': {
        'app_name': 'ss_share',
        'app_title': 'Simple file share',
        "login_background_image": "",
        "login_background_color": [100, 100, 100],
        'root': '',
        'web_url': '',
        'dir_file_share': '%s/files' % (DIR_CONF),
        'default_user': ('admin', '111'),
        'users': {},
        'uploaded_files': {},
        'secret_key': 'lkajdghdadkglajkgah',
        'upload_extensions': (
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ogg', 'mp3', 'm4a',
            'mp4', 'wav', 'mkv', 'avi', 'sh'
            )
        }
}
