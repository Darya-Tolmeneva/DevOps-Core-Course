import os
import socket
import platform
import logging
from datetime import datetime, timezone
from threading import Lock

from flask import Flask, jsonify, request

logging.basicConfig(
	level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

START_TIME = datetime.now(timezone.utc)

DATA_DIR = os.getenv("DATA_DIR", "/data")
VISITS_FILE = os.path.join(DATA_DIR, "visits")
visits_lock = Lock()


def ensure_data_dir():
	os.makedirs(DATA_DIR, exist_ok=True)


def load_visits():
	ensure_data_dir()
	if not os.path.exists(VISITS_FILE):
		with open(VISITS_FILE, "w", encoding="utf-8") as f:
			f.write("0")
		return 0

	try:
		with open(VISITS_FILE, "r", encoding="utf-8") as f:
			content = f.read().strip()
			return int(content) if content else 0
	except (ValueError, OSError) as e:
		logger.warning(f"Failed to load visits counter: {e}")
		return 0


def save_visits(count):
	ensure_data_dir()
	temp_file = f"{VISITS_FILE}.tmp"
	with open(temp_file, "w", encoding="utf-8") as f:
		f.write(str(count))
	os.replace(temp_file, VISITS_FILE)


def increment_visits():
	with visits_lock:
		current = load_visits()
		current += 1
		save_visits(current)
		return current


def get_current_visits():
	with visits_lock:
		return load_visits()


def get_uptime():
	delta = datetime.now(timezone.utc) - START_TIME
	seconds = int(delta.total_seconds())
	hours = seconds // 3600
	minutes = (seconds % 3600) // 60
	return {"seconds": seconds, "human": f"{hours} hours, {minutes} minutes"}


def get_system_info():
	return {
		"hostname": socket.gethostname(),
		"platform": platform.system(),
		"platform_version": platform.version(),
		"architecture": platform.machine(),
		"cpu_count": os.cpu_count(),
		"python_version": platform.python_version(),
	}


@app.route("/", methods=["GET"])
def index():
	logger.info(f"Request: {request.method} {request.path}")
	uptime = get_uptime()
	visit_count = increment_visits()

	response = {
		"service": {
			"name": "devops-info-service",
			"version": "1.0.0",
			"description": "DevOps course info service",
			"framework": "Flask",
		},
		"system": get_system_info(),
		"runtime": {
			"uptime_seconds": uptime["seconds"],
			"uptime_human": uptime["human"],
			"current_time": datetime.now(timezone.utc).isoformat(),
			"timezone": "UTC",
		},
		"request": {
			"client_ip": request.remote_addr,
			"user_agent": request.headers.get("User-Agent"),
			"method": request.method,
			"path": request.path,
		},
		"visits": {
			"count": visit_count,
			"file": VISITS_FILE,
		},
		"endpoints": [
			{"path": "/", "method": "GET", "description": "Service information + increment visits"},
			{"path": "/health", "method": "GET", "description": "Health check"},
			{"path": "/visits", "method": "GET", "description": "Current visits count"},
		],
	}

	return jsonify(response)


@app.route("/visits", methods=["GET"])
def visits():
	return jsonify(
		{
			"visits": get_current_visits(),
			"file": VISITS_FILE,
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}
	)


@app.route("/health", methods=["GET"])
def health():
	uptime = get_uptime()
	return jsonify(
		{
			"status": "healthy",
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"uptime_seconds": uptime["seconds"],
		}
	)


@app.errorhandler(404)
def not_found(error):
	return jsonify({"error": "Not Found", "message": "Endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
	return (
		jsonify(
			{
				"error": "Internal Server Error",
				"message": "An unexpected error occurred",
			}
		),
		500,
	)


if __name__ == "__main__":
	logger.info("Application starting...")
	ensure_data_dir()
	save_visits(load_visits())
	app.run(host=HOST, port=PORT, debug=DEBUG)
