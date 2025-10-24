from itsdangerous import URLSafeTimedSerializer
from keys import secret_key,salt

def generate_token(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data, salt=salt)

def verify_token(data):
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.loads(data, salt=salt)