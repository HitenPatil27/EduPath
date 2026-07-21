import os
import json
from datetime import datetime, timedelta, timezone
import jwt
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from huggingface_hub import InferenceClient

from core.models import (
    create_user, get_user_by_email, get_user_by_id, update_user,
    set_user_interests, set_user_hobbies,
    create_session, get_session, update_session, get_sessions_for_user,
    add_qa, get_qa_history, delete_last_qa,
    set_recommendations, get_recommendations,
)
from core.utils import token_required, _get_user_profile, _get_qa_history_list

api_bp = Blueprint('api', __name__)

def get_hf_client():
    HF_API_KEY = os.environ.get('HF_API_KEY')
    HF_BASE_URL = os.environ.get('HF_BASE_URL', 'https://api.groq.com/openai/v1')
    if not HF_API_KEY:
        return None
    if HF_BASE_URL:
        return InferenceClient(base_url=HF_BASE_URL, api_key=HF_API_KEY)
    return InferenceClient(api_key=HF_API_KEY)

def get_hf_model():
    return os.environ.get('HF_MODEL', 'llama-3.3-70b-versatile')

@api_bp.route('/firebase-config', methods=['GET'])
def firebase_config():
    """Serve Firebase web config to the frontend (public, non-sensitive keys)."""
    return jsonify({
        'apiKey': os.environ.get('FIREBASE_API_KEY', ''),
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', 'edupath-564dc.firebaseapp.com'),
        'projectId': os.environ.get('FIREBASE_PROJECT_ID', 'edupath-564dc'),
    })

@api_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    if get_user_by_email(data.get('email')):
        return jsonify({'message': 'User already exists'}), 400
    
    user = create_user(
        name=data.get('name'),
        email=data.get('email'),
        password_hash=generate_password_hash(data.get('password'))
    )
    
    token = jwt.encode(
        {'user_id': user['id'], 'exp': datetime.now(timezone.utc) + timedelta(days=7)},
        current_app.config['SECRET_KEY'], algorithm="HS256"
    )
    return jsonify({
        'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
    })

@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    user = get_user_by_email(data.get('email'))
    if user and check_password_hash(user['passwordHash'], data.get('password')):
        token = jwt.encode(
            {'user_id': user['id'], 'exp': datetime.now(timezone.utc) + timedelta(days=7)},
            current_app.config['SECRET_KEY'], algorithm="HS256"
        )
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'profileComplete': user.get('profileComplete', False)
            }
        })
    return jsonify({'message': 'Invalid credentials'}), 401

@api_bp.route('/auth/google', methods=['POST'])
def google_login():
    """Authenticate with a Google ID token from Firebase Auth on the client."""
    from firebase_admin import auth as firebase_auth

    data = request.json
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({'message': 'ID token is required'}), 400

    try:
        # Verify the Firebase ID token
        decoded = firebase_auth.verify_id_token(id_token)
        email = decoded.get('email')
        name = decoded.get('name', decoded.get('email', 'User'))
        google_uid = decoded.get('uid')

        if not email:
            return jsonify({'message': 'Email not found in token'}), 400

        # Find or create user in Firestore
        user = get_user_by_email(email)
        if not user:
            user = create_user(
                name=name,
                email=email,
                password_hash='__google_oauth__'  # No password for Google users
            )
            update_user(user['id'], {'googleUid': google_uid, 'authProvider': 'google'})
        else:
            # Link Google UID if not already linked
            if not user.get('googleUid'):
                update_user(user['id'], {'googleUid': google_uid, 'authProvider': 'google'})

        # Issue our own JWT
        token = jwt.encode(
            {'user_id': user['id'], 'exp': datetime.now(timezone.utc) + timedelta(days=7)},
            current_app.config['SECRET_KEY'], algorithm="HS256"
        )
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'name': user.get('name', name),
                'email': user.get('email', email),
                'profileComplete': user.get('profileComplete', False)
            }
        })
    except firebase_auth.InvalidIdTokenError:
        return jsonify({'message': 'Invalid Google token'}), 401
    except firebase_auth.ExpiredIdTokenError:
        return jsonify({'message': 'Token has expired. Please sign in again.'}), 401
    except Exception as e:
        current_app.logger.error(f"Google auth error: {str(e)}")
        return jsonify({'message': 'Authentication failed', 'error': str(e)}), 500

@api_bp.route('/auth/me', methods=['GET'])
@token_required
def get_me(current_user):
    return jsonify({
        'id': current_user['id'],
        'name': current_user['name'],
        'email': current_user['email'],
        'profileComplete': current_user.get('profileComplete', False),
        'profile': _get_user_profile(current_user)
    })

@api_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.json
    uid = current_user['id']
    
    update_fields = {}
    if 'educationLevel' in data:
        update_fields['educationLevel'] = data['educationLevel']
    if 'fieldOfStudy' in data:
        update_fields['fieldOfStudy'] = data['fieldOfStudy']
    if 'institution' in data:
        update_fields['institution'] = data['institution']
    if 'graduationYear' in data and data['graduationYear'] is not None:
        update_fields['graduationYear'] = str(data['graduationYear'])
    if 'nextStep' in data:
        update_fields['nextStep'] = data['nextStep']
    update_fields['profileComplete'] = True
    
    update_user(uid, update_fields)
    
    if 'interests' in data:
        set_user_interests(uid, data['interests'])
    if 'hobbies' in data:
        set_user_hobbies(uid, data['hobbies'])
            
    return jsonify({'message': 'Profile updated successfully'})

@api_bp.route('/session/start', methods=['POST'])
@token_required
def start_session(current_user):
    session = create_session(current_user['id'])
    return _ask_next_question(current_user, session)

@api_bp.route('/session/answer', methods=['POST'])
@token_required
def answer_question(current_user):
    data = request.json
    session = get_session(data.get('sessionId'), user_id=current_user['id'])
    if not session or session.get('status') != 'in-progress':
        return jsonify({'message': 'Active session not found'}), 404
        
    add_qa(
        session_id=session['id'],
        question=data.get('question'),
        answer=data.get('answer'),
        qa_type=data.get('type', 'text')
    )
    
    return _ask_next_question(current_user, session)

@api_bp.route('/session/undo_last', methods=['POST'])
@token_required
def undo_last(current_user):
    data = request.json
    session = get_session(data.get('sessionId'), user_id=current_user['id'])
    if not session or session.get('status') != 'in-progress':
        return jsonify({'message': 'Active session not found'}), 404
        
    delete_last_qa(session['id'])
    return jsonify({'message': 'Undo successful'})

def _ask_next_question(user, session):
    hf_client = get_hf_client()
    if not hf_client:
        return jsonify({'message': 'HuggingFace client not configured'}), 500
        
    profile = _get_user_profile(user)
    qa_history = _get_qa_history_list(session['id'])
    
    next_step = profile.get('nextStep', '')
    edu_level = profile.get('educationLevel', '')
    
    # Path-specific counseling strategy for questions
    if next_step == 'Further Studies':
        strategy = f"The user is looking for Further Studies. Current level: {edu_level}. "
        if '10' in edu_level:
            strategy += "Focus on identifying their aptitude for specific streams like Science, Commerce, or Arts. Ask about subjects they find easy or interesting."
        elif '12' in edu_level or 'High School' in edu_level:
            strategy += "Focus on identifying a preference between professional degrees, vocational diplomas, or academic paths. Ask about long-term academic goals."
        else:
            strategy += "Focus on specialized postgraduate programs, certifications, or research opportunities that build on their current field."
    elif next_step == 'Job Hunting':
        strategy = "The user is Job Hunting. Focus on technical skills, project experience, industry preferences, and geographic flexibility. Ask about their ideal work environment."
    elif next_step == 'Switching Careers':
        strategy = "The user is Switching Careers. Focus on transferable skills from their current field and their motivation for the new path. Ask about what specifically attracts them to the new industry."
    else:
        strategy = "The user is Exploring Options. Act as a broad diagnostic guide. Ask questions that reveal hidden passions or personality traits that align with diverse career clusters."

    system_prompt = f"""You are an expert career counselor AI. Ask ONE adaptive question at a time based on the user's profile and all previous answers.
    
COUNSELING STRATEGY:
{strategy}

Respond ONLY in JSON:
- If more questions needed (aim for 6-10 questions total):
  {{ "question": "...", "context": "why you're asking", "type": "single-select|multi-select|slider|text", "options": [...] }}
- If enough data collected (after 6-10 questions):
  {{ "done": true }}"""

    user_prompt = f"User Profile: {json.dumps(profile)}\nQ&A History: {json.dumps(qa_history)}\nGenerate next response in JSON mode."
    
    try:
        response = hf_client.chat.completions.create(
            model=get_hf_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        msg = response.choices[0].message.content
        result = json.loads(msg)
        result['sessionId'] = session['id']
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error calling HuggingFace: {str(e)}")
        return jsonify({'message': 'Error generating question', 'error': str(e)}), 500

@api_bp.route('/session/finish', methods=['POST'])
@token_required
def finish_session(current_user):
    data = request.json
    session = get_session(data.get('sessionId'), user_id=current_user['id'])
    if not session:
        return jsonify({'message': 'Session not found'}), 404
        
    update_session(session['id'], {'status': 'completed'})
    
    hf_client = get_hf_client()
    if not hf_client:
        return jsonify({'message': 'HuggingFace client not configured'}), 500
        
    profile = _get_user_profile(current_user)
    qa_history = _get_qa_history_list(session['id'])
    
    next_step = profile.get('nextStep', '')
    edu_level = profile.get('educationLevel', '')
    
    if next_step == 'Further Studies':
        if '10' in edu_level:
            focus_instruction = "The user is a 10th grade student. Recommend specific STREAMS (Science, Commerce, Arts) or foundation courses. Explain why the stream fits their interests."
            title_instruction = "Academic Stream or Foundation Course"
        elif '12' in edu_level or 'High School' in edu_level:
            focus_instruction = "The user is a 12th grade student. Recommend Degrees, Diplomas, or Professional Entrance paths. Be specific about the type of institution."
            title_instruction = "Degree or Diploma Program"
        else:
            focus_instruction = "The user is looking for Higher Education. Suggest Master's programs, PhDs, or specialized global certifications. Focus on specialization."
            title_instruction = "Postgraduate Degree or Certification"
        focus_instruction += " DO NOT show salary or growth outlook (set salaryRange strictly to 'N/A' and growthOutlook strictly to 'N/A')."
        
    elif next_step == 'Job Hunting':
        focus_instruction = "The user is Job Hunting. Provide specific JOB TITLES. Include starting salary and estimated salary after 3 years in Indian Rupee (INR) (e.g. '₹5LPA (Start) - ₹12LPA (3 yrs)')."
        title_instruction = "Specific Job Title"
        
    elif next_step == 'Switching Careers':
        focus_instruction = "The user is Switching Careers. Suggest realistic career pivots where their current skills are applicable. Explain the 'Transferable Skills' clearly."
        title_instruction = "Target Career/Job Title"
        
    else:
        focus_instruction = "The user is Exploring Options. Provide a diverse range of high-potential careers matching their personality and background."
        title_instruction = "Specific Job Title"
        
    system_prompt = f"""You are a career recommendation engine. Based on the user profile and Q&A session, return TOP 10 recommendations as a JSON wrapper.

SPECIALIZED GOAL:
{focus_instruction}

Respond ONLY in JSON matching exactly this wrapper structure:
{{
  "recommendations": [
    {{
      "rank": 1,
      "title": "{title_instruction}",
      "matchScore": 94,
      "description": "...",
      "whyItFitsYou": "...",
      "skills": ["Skill1", "Skill2"],
      "salaryRange": "...",
      "growthOutlook": "High|Medium|Low"
    }}
  ]
}}"""
    
    user_prompt = f"User Profile: {json.dumps(profile)}\nFull Q&A Session: {json.dumps(qa_history)}\nGenerate top 10 recommendations in JSON mode."

    try:
        response = hf_client.chat.completions.create(
            model=get_hf_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        result = json.loads(response.choices[0].message.content)
        recs = result.get('recommendations', [])
        
        # Prepare recommendations for Firestore
        rec_docs = []
        for idx, rec in enumerate(recs):
            rec_docs.append({
                'rank': rec.get('rank', idx + 1),
                'title': rec.get('title', 'Unknown'),
                'matchScore': rec.get('matchScore', 0),
                'description': rec.get('description', ''),
                'whyItFitsYou': rec.get('whyItFitsYou', ''),
                'skills': rec.get('skills', []),
                'salaryRange': rec.get('salaryRange', ''),
                'growthOutlook': rec.get('growthOutlook', 'Medium'),
            })
        
        set_recommendations(session['id'], rec_docs)
        return jsonify({'message': 'Ranking complete', 'sessionId': session['id']})
    except Exception as e:
        current_app.logger.error(f"Error calling HuggingFace: {str(e)}")
        return jsonify({'message': 'Error generating recommendations', 'error': str(e)}), 500

@api_bp.route('/session/<session_id>', methods=['GET'])
@token_required
def get_session_route(current_user, session_id):
    session = get_session(session_id, user_id=current_user['id'])
    if not session:
        return jsonify({'message': 'Session not found'}), 404
        
    recs = get_recommendations(session['id'])
    results = []
    for r in recs:
        skills = r.get('skills', [])
        # Handle legacy skillsJson field if present
        if isinstance(skills, str):
            skills = json.loads(skills)
        results.append({
            'rank': r.get('rank'),
            'title': r.get('title'),
            'matchScore': r.get('matchScore'),
            'description': r.get('description'),
            'whyItFitsYou': r.get('whyItFitsYou'),
            'skills': skills,
            'salaryRange': r.get('salaryRange'),
            'growthOutlook': r.get('growthOutlook'),
        })
        
    return jsonify({
        'id': session['id'],
        'createdAt': session.get('createdAt'),
        'status': session.get('status'),
        'qaHistory': _get_qa_history_list(session['id']),
        'recommendations': results
    })

@api_bp.route('/sessions', methods=['GET'])
@token_required
def get_sessions(current_user):
    sessions = get_sessions_for_user(current_user['id'])
    out = []
    for s in sessions:
        out.append({
            'id': s['id'],
            'createdAt': s.get('createdAt'),
            'status': s.get('status')
        })
    return jsonify(out)

@api_bp.route('/chat', methods=['POST'])
@token_required
def chat_eduagent(current_user):
    data = request.json
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'message': 'No messages provided'}), 400

    profile = _get_user_profile(current_user)
    
    # Get latest completed session and recommendations
    all_sessions = get_sessions_for_user(current_user['id'])
    latest_session = None
    for s in all_sessions:
        if s.get('status') == 'completed':
            latest_session = s
            break
    
    context_str = f"User Profile: {json.dumps(profile)}\n"
    
    if latest_session:
        recs = get_recommendations(latest_session['id'])
        rec_list = []
        for r in recs:
            rec_list.append({
                "rank": r.get('rank'),
                "title": r.get('title'),
                "matchScore": r.get('matchScore'),
                "whyItFitsYou": r.get('whyItFitsYou')
            })
        context_str += f"Latest Assessment Results: {json.dumps(rec_list)}\n"
    else:
        context_str += "Latest Assessment Results: None available yet.\n"

    system_prompt = f"""You are EduAgent, a friendly, intelligent, and supportive career counselor chatbot for the EduPath platform.
Your goal is to answer the user's questions regarding their career, studies, and the results of their latest AI assessment.
Be concise, practical, and highly personalized based on their profile and assessment context below.
Do not use markdown heavily, keep it readable as a chat message.

CRITICAL RULES:
1. DO NOT output any internal thinking or reasoning.
2. DO NOT use XML tags like <think> or <reasoning>.
3. Output ONLY the direct response to the user.
4. Speak naturally, as a human expert.

{context_str}"""

    hf_client = get_hf_client()
    if not hf_client:
        return jsonify({'message': 'HuggingFace client not configured'}), 500

    # Build messages array for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        # frontend sends { role: 'user' | 'assistant', content: '...' }
        llm_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    try:
        response = hf_client.chat.completions.create(
            model=get_hf_model(),
            messages=llm_messages,
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content
        
        import re
        reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
        
        return jsonify({'reply': reply})
    except Exception as e:
        current_app.logger.error(f"Error calling HuggingFace for chat: {str(e)}")
        return jsonify({'message': 'Error generating response', 'error': str(e)}), 500
