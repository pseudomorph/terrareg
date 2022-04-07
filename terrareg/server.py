
import os

from werkzeug.utils import secure_filename
from flask import Flask, request


class ModuleFactory(object):
    pass


class Server(object):
    """Manage web server and route requests"""

    ALLOWED_EXTENSIONS = {'zip'}

    def __init__(self):
        """Create flask app and store member variables"""
        self._app = Flask(__name__)
        self.host = '127.0.0.1'
        self.port = 5000
        self.debug = True

        if not os.path.isdir(self._get_data_directory()):
            os.mkdir(self._get_data_directory())
        if not os.path.isdir(self._get_upload_directory()):
            os.mkdir(self._get_upload_directory())

        self._app.config['UPLOAD_FOLDER'] = self._get_upload_directory()

        self._register_routes()

    def _get_data_directory(self):
        return os.path.join(os.environ.get('DATA_DIRECTORY', '.'), 'data')

    def _get_upload_directory(self):
        return os.path.join(self._get_data_directory(), 'upload')

    def _register_routes(self):
        """Register routes with flask."""

        # Upload module
        self._app.route('/v1/<string:namespace>/<string:name>/<string:provider>/<string:version>/upload', methods=['POST'])(self._upload_module_version)

        # Terraform registry routes
        self._app.route('/v1/<string:namespace>/<string:name>/<string:provider>/versions')(self._module_versions)
        self._app.route('/v1/<string:namespace>/<string:name>/<string:provider>/<string:version>/download')(self._module_version_download)

    def run(self):
        """Run flask server."""
        self._app.run(host=self.host, port=self.port, debug=self.debug)

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS


    def _upload_module_version(self, namespace, name, provider, version):
        if len(request.files) != 1:
            return 'One file can be uploaded'

        file = request.files[[f for f in request.files.keys()][0]]

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return 'No selected file'
        if file and self.allowed_file(file.filename):
            self._handle_file_upload(file)
            return 'Upload sucessful'

        return 'Error occurred'

    def _handle_file_upload(self, namespace, name, provider, version, file):
        """Handle file upload."""
        pass

    def _module_versions(self, namespace, name, provider):
        """Return list of version."""
        return 'blah'

    def _module_version_download(self, namespace, name, provider, version):
        return ''