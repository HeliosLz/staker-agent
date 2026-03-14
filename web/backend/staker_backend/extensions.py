"""Flask extensions used by the backend."""
from flask_cors import CORS
from flask_socketio import SocketIO

cors = CORS()
socketio = SocketIO(logger=False, engineio_logger=False)
