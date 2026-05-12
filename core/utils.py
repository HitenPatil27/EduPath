import jwt
from functools import wraps
from flask import request, jsonify, current_app
from core.models import get_user_by_id, get_user_interests, get_user_hobbies, get_qa_history


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = token.split(" ")[1] if " " in token else token
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = get_user_by_id(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Invalid user token!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def _get_user_profile(user):
    """Build the profile dict used by the AI prompts.
    
    `user` is a plain dict coming from Firestore (has an 'id' key).
    """
    return {
        "educationLevel": user.get('educationLevel'),
        "fieldOfStudy": user.get('fieldOfStudy'),
        "institution": user.get('institution'),
        "graduationYear": user.get('graduationYear'),
        "nextStep": user.get('nextStep'),
        "interests": get_user_interests(user['id']),
        "hobbies": get_user_hobbies(user['id']),
    }


def _get_qa_history_list(session_id):
    """Return QA pairs as a list of dicts for the AI prompt."""
    qa_docs = get_qa_history(session_id)
    return [{"question": qa['question'], "answer": qa['answer']} for qa in qa_docs]
