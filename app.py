import os
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS
from core.extensions import init_firebase

def create_app():
    load_dotenv(override=True)
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)

    app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET', 'super-secret-key')

    # Initialize Firebase (replaces SQLAlchemy)
    with app.app_context():
        init_firebase(app)

    from core.frontend_routes import frontend_bp
    from core.api_routes import api_bp
    
    app.register_blueprint(frontend_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
