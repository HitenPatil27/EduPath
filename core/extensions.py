import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore

_firebase_app = None
db = None  # Firestore client, initialized in init_firebase()


def init_firebase(app=None):
    """Initialize Firebase Admin SDK and Firestore client safely.
    
    Credentials are loaded from:
      1. FIREBASE_CREDENTIALS_JSON env var (raw JSON string or base64-encoded)
      2. FIREBASE_CREDENTIALS env var (file path to service account JSON)
      3. Default fallback file in project root
    """
    global _firebase_app, db

    if _firebase_app is not None:
        db = firestore.client()
        return db

    try:
        # Option 1: Credentials as JSON string in env var (for Vercel / serverless cloud deployment)
        cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
        if cred_json:
            try:
                cred_dict = json.loads(cred_json)
            except json.JSONDecodeError:
                cred_dict = json.loads(base64.b64decode(cred_json).decode('utf-8'))
            cred = credentials.Certificate(cred_dict)
        else:
            # Option 2: Credentials as file path
            cred_path = os.environ.get(
                'FIREBASE_CREDENTIALS',
                os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             'edupath-564dc-firebase-adminsdk-fbsvc-02812604f0.json')
            )
            if not os.path.exists(cred_path):
                print(f"WARNING: Firebase credentials file not found at {cred_path}")
                return None
            cred = credentials.Certificate(cred_path)

        _firebase_app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        return db
    except Exception as e:
        print(f"WARNING: Firebase init failed: {e}")
        return None

def get_db():
    global db
    if db is None:
        init_firebase()
    return db
