from flask import Blueprint, render_template

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def route_index():
    return render_template('index.html')

@frontend_bp.route('/register')
def route_register():
    return render_template('register.html')

@frontend_bp.route('/login')
def route_login():
    return render_template('login.html')

@frontend_bp.route('/onboarding')
def route_onboarding():
    return render_template('onboarding.html')

@frontend_bp.route('/questionnaire')
def route_questionnaire():
    return render_template('questionnaire.html')

@frontend_bp.route('/loading')
def route_loading():
    return render_template('loading.html')

@frontend_bp.route('/results')
def route_results():
    return render_template('results.html')

@frontend_bp.route('/history')
def route_history():
    return render_template('history.html')

@frontend_bp.route('/dashboard')
def route_dashboard():
    return render_template('dashboard.html')

@frontend_bp.route('/chat')
def route_chat():
    return render_template('chat.html')
