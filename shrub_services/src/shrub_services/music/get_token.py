import jwt
import time
import shrub_util.core.logging as logging


def apple_get_dev_token(team_id: str, key_id: str, key_path: str):
    with open(key_path, 'r') as f:
        private_key = f.read()
    
    headers = {
        'alg': 'ES256',
        'kid': key_id
    }
    payload = {
        'iss': team_id,
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600 * 24 * 180  # 6 months
    }
    token = jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    print(token)
    return token