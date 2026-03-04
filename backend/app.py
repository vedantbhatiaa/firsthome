"""
FirstHome — Flask Application Entry Point
Run with: python app.py (dev) or gunicorn app:app (prod)
"""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.api import api


def create_app(config=None) -> Flask:
    """Application factory pattern."""
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )

    # ── Configuration ──
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "firsthome-dev-key-change-in-prod"),
        DEBUG=os.environ.get("FLASK_DEBUG", "True") == "True",
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=True,
    )
    if config:
        app.config.update(config)

    # ── CORS — allow frontend origin ──
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",      # dev
                "http://127.0.0.1:5500",      # Live Server
                "https://yourusername.github.io",  # GitHub Pages — update this
            ]
        }
    })

    # ── Register blueprints ──
    app.register_blueprint(api)

    # ── Serve frontend for all non-API routes ──
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    # ── Error handlers ──
    @app.errorhandler(404)
    def not_found(e):
        return {"success": False, "error": "Endpoint not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"success": False, "error": "Method not allowed"}, 405

    @app.errorhandler(500)
    def server_error(e):
        return {"success": False, "error": "Internal server error"}, 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🏠 FirstHome API running → http://localhost:{port}")
    print(f"   Health check: http://localhost:{port}/api/health\n")
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
