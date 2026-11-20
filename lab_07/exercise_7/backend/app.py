from flask import Flask
from flask_cors import CORS

from database import test_connection

from routes.threats import threats_bp
from routes.search import search_bp
from routes.analytics import analytics_bp


# ==========================================
# Create Flask application
# ==========================================

app = Flask(__name__)

# Allow frontend to communicate with Flask
CORS(app)


# ==========================================
# Register API routes
# ==========================================

app.register_blueprint(
    threats_bp,
    url_prefix="/api/threats"
)

app.register_blueprint(
    search_bp,
    url_prefix="/api/search"
)

app.register_blueprint(
    analytics_bp,
    url_prefix="/api/analytics"
)


# ==========================================
# Home / API status
# ==========================================

@app.route("/")
def home():

    return {
        "application": "Cyber Threat Intelligence Platform",
        "status": "running",
        "version": "1.0"
    }


@app.route("/api/health")
def health():

    try:

        test_connection()

        return {
            "status": "healthy",
            "mongodb": "connected"
        }

    except Exception as e:

        return {
            "status": "error",
            "mongodb": "disconnected",
            "message": str(e)
        }, 500


# ==========================================
# Run application
# ==========================================

if __name__ == "__main__":

    print("=" * 60)
    print("CYBER THREAT INTELLIGENCE PLATFORM")
    print("=" * 60)

    print("Starting Flask server...")
    print("Backend: http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )