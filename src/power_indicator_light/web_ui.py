import threading
import logging
from flask import Flask, jsonify, render_template
from werkzeug.serving import make_server
from .control_status import get_status

class WebServer(threading.Thread):
    def __init__(self, port: int = 5001, restart_callback=None):
        super().__init__(name="WebServerThread", daemon=True) # daemon=True ensures it exits when main exits
        self.port = port
        self.restart_callback = restart_callback
        self.app = Flask(__name__)

        # Mute noisy logs
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        self._setup_routes()
        
        self.server = make_server("0.0.0.0", self.port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def _setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/status")
        def status():
            return jsonify(get_status())

        @self.app.route('/restart', methods=['POST'])
        def handle_restart():
            if self.restart_callback:
                # Trigger the restart in a background thread so the 
                # HTTP response can be sent before the workers stop.
                threading.Thread(target=self.restart_callback).start()
                return jsonify({"status": "restarting", "message": "System is rebooting..."}), 200
            return jsonify({"status": "error", "message": "No restart callback defined"}), 500

    def run(self):
        print(f"Webserver startet auf Port {self.port}...")
        self.server.serve_forever()

    def shutdown(self):
        print("Webserver wird beendet...")
        self.server.shutdown()