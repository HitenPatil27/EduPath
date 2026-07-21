"""
Firestore data-access helpers.

Replaces the old SQLAlchemy ORM models with thin wrappers around the
Firestore Python client.  Every public function accepts / returns plain
dicts so the rest of the application never needs to import firestore
directly.

Firestore collection layout
────────────────────────────
  users/{uid}                        — user document
  users/{uid}/interests/{auto}       — sub-collection
  users/{uid}/hobbies/{auto}         — sub-collection
  sessions/{sid}                     — session document
  sessions/{sid}/qa_history/{auto}   — sub-collection
  sessions/{sid}/recommendations/{auto}
"""

from core.extensions import get_db

def _db():
    client = get_db()
    if client is None:
        raise RuntimeError("Firebase is not initialized. Please set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS environment variable.")
    return client


# ─────────────────────────── helpers ──────────────────────────────────

def _now():
    return datetime.now(timezone.utc).isoformat()


def _doc_to_dict(doc):
    """Convert a Firestore DocumentSnapshot to a dict that includes 'id'."""
    if not doc.exists:
        return None
    d = doc.to_dict()
    d['id'] = doc.id
    return d


# ─────────────────────────── Users ────────────────────────────────────

def create_user(name, email, password_hash):
    """Create a new user document. Returns the new user dict."""
    user_ref = _db().collection('users').document()
    user_data = {
        'name': name,
        'email': email,
        'passwordHash': password_hash,
        'educationLevel': None,
        'fieldOfStudy': None,
        'institution': None,
        'graduationYear': None,
        'nextStep': None,
        'profileComplete': False,
        'createdAt': _now(),
    }
    user_ref.set(user_data)
    user_data['id'] = user_ref.id
    return user_data


def get_user_by_email(email):
    """Return user dict or None."""
    docs = _db().collection('users').where('email', '==', email).limit(1).stream()
    for doc in docs:
        return _doc_to_dict(doc)
    return None


def get_user_by_id(user_id):
    """Return user dict or None."""
    doc = _db().collection('users').document(user_id).get()
    return _doc_to_dict(doc)


def update_user(user_id, data: dict):
    """Merge-update fields on a user document."""
    _db().collection('users').document(user_id).update(data)


# ─────────────────────── Interests / Hobbies ──────────────────────────

def set_user_interests(user_id, interests: list):
    """Replace all interests for a user."""
    col = _db().collection('users').document(user_id).collection('interests')
    # delete existing
    for doc in col.stream():
        doc.reference.delete()
    # add new
    for interest in interests:
        col.add({'interest': interest})


def get_user_interests(user_id) -> list:
    col = _db().collection('users').document(user_id).collection('interests')
    return [d.to_dict()['interest'] for d in col.stream()]


def set_user_hobbies(user_id, hobbies: list):
    """Replace all hobbies for a user."""
    col = _db().collection('users').document(user_id).collection('hobbies')
    for doc in col.stream():
        doc.reference.delete()
    for hobby in hobbies:
        col.add({'hobby': hobby})


def get_user_hobbies(user_id) -> list:
    col = _db().collection('users').document(user_id).collection('hobbies')
    return [d.to_dict()['hobby'] for d in col.stream()]


# ─────────────────────────── Sessions ─────────────────────────────────

def create_session(user_id):
    """Create a new counseling session. Returns session dict."""
    ref = _db().collection('sessions').document()
    data = {
        'userId': user_id,
        'createdAt': _now(),
        'status': 'in-progress',
    }
    ref.set(data)
    data['id'] = ref.id
    return data


def get_session(session_id, user_id=None):
    """Return session dict or None.  Optionally verify ownership."""
    doc = _db().collection('sessions').document(session_id).get()
    s = _doc_to_dict(doc)
    if s and user_id and s.get('userId') != user_id:
        return None
    return s


def update_session(session_id, data: dict):
    _db().collection('sessions').document(session_id).update(data)


def get_sessions_for_user(user_id):
    """Return list of session dicts for a user, newest first."""
    docs = (_db().collection('sessions')
              .where('userId', '==', user_id)
              .stream())
    results = [_doc_to_dict(d) for d in docs]
    # Sort in Python to avoid requiring a Firestore composite index
    results.sort(key=lambda s: s.get('createdAt', ''), reverse=True)
    return results


# ─────────────────────────── QA History ───────────────────────────────

def add_qa(session_id, question, answer, qa_type='text'):
    ref = _db().collection('sessions').document(session_id).collection('qa_history').document()
    data = {
        'question': question,
        'answer': answer,
        'type': qa_type,
        'createdAt': _now(),
    }
    ref.set(data)
    data['id'] = ref.id
    return data


def get_qa_history(session_id) -> list:
    docs = (_db().collection('sessions')
              .document(session_id)
              .collection('qa_history')
              .order_by('createdAt')
              .stream())
    return [_doc_to_dict(d) for d in docs]


def delete_last_qa(session_id):
    """Delete the most recent QA entry. Returns True if something was deleted."""
    docs = list(
        _db().collection('sessions')
          .document(session_id)
          .collection('qa_history')
          .order_by('createdAt', direction='DESCENDING')
          .limit(1)
          .stream()
    )
    if docs:
        docs[0].reference.delete()
        return True
    return False


# ─────────────────────── Recommendations ──────────────────────────────

def set_recommendations(session_id, recs: list):
    """Replace all recommendations for a session."""
    col = _db().collection('sessions').document(session_id).collection('recommendations')
    # delete existing
    for doc in col.stream():
        doc.reference.delete()
    # add new
    for rec in recs:
        col.add(rec)


def get_recommendations(session_id) -> list:
    docs = (_db().collection('sessions')
              .document(session_id)
              .collection('recommendations')
              .order_by('rank')
              .stream())
    return [_doc_to_dict(d) for d in docs]
