from flask import Flask
import os

import init_db

def create_app():
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    app.secret_key = "supersecretkey"

    from .routes import main
    app.register_blueprint(main)

    # ✅ VERY IMPORTANT (THIS FIXES YOUR ERROR)
    from .routes import init_db
   

    return app