import requests
import secrets
import webbrowser
import socketserver
import http.server
import threading
import json
import os
import time
import pickle

MAL_AUTH_URL = "https://myanimelist.net/v1/oauth2/authorize"
MAL_TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"
MAL_API_URL = "https://api.myanimelist.net/v2"
ONE_PIECE_ID = 21
VERBOSE = False

vprint = print if VERBOSE else lambda *a, **k: None

with open('mal_auth.json', 'r') as f:
    data = json.load(f)
    MAL_CLIENT_ID = data['client_id']
    MAL_CLIENT_SECRET = data['client_secret']

def get_new_code_verifier() -> str:
    token = secrets.token_urlsafe(100)
    return token[:128]

def get_auth_url(code_challenge) -> str:
    body = {
        "response_type": "code",
        "client_id": MAL_CLIENT_ID,
        "code_challenge": code_challenge,
        "code_challenge_method": "plain",
        "state": "random_state",
    }

    return requests.Request("GET", MAL_AUTH_URL, params=body).prepare().url

def listen_for_code() -> str:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            nonlocal code
            code = self.path.split("=")[1].split("&")[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Code received. You may now close this window.")
            threading.Thread(target=self.server.shutdown).start()
            self.server.server_close()

    code = ""
    with socketserver.TCPServer(("localhost", 8000), Handler) as httpd:
        vprint("Listening for code on port 8000")
        httpd.serve_forever()
    return code
                                 
def fetch_token() -> dict:
    code_verifier = get_new_code_verifier()
    code_challenge = code_verifier
    auth_url = get_auth_url(code_challenge)
    webbrowser.open(auth_url)
    code = listen_for_code()
    body = {
        "client_id": MAL_CLIENT_ID,
        "client_secret": MAL_CLIENT_SECRET,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(MAL_TOKEN_URL, data=body, headers=headers)
    return response.json()

def update_token(refresh_token: str) -> dict:
    body = {
        "client_id": MAL_CLIENT_ID,
        "client_secret": MAL_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(MAL_TOKEN_URL, data=body, headers=headers)
    return response.json()
    
def get_token():
    if os.path.exists('mal_token.pkl'):
        with open('mal_token.pkl', 'rb') as f:
            token = pickle.load(f)
            if token['valid_until'] > time.time():
                vprint('Token still valid')
                return token
            else:
                vprint('Refreshing token')
                token = update_token(token['refresh_token'])
    else:   
        vprint('Fetching new token')
        token = fetch_token()
        
    token['valid_until'] = time.time() + token['expires_in']
    token['name'] = get_name(token['access_token'])
    with open('mal_token.pkl', 'wb') as f:
        pickle.dump(token, f)
    return token

def get_name(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get('https://api.myanimelist.net/v2/users/@me', headers=headers)
    response.raise_for_status()
    return response.json()['name']

def get_user_anime_list(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    params = {
        'limit': 1000
    }
    response = requests.get(f'{MAL_API_URL}/users/@me/animelist', headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def update_one_piece_episode(token, episode):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    body = {
        'status': 'watching',
        'num_watched_episodes': episode
    }
    response = requests.put(f'{MAL_API_URL}/anime/{ONE_PIECE_ID}/my_list_status', headers=headers, data=body)
    response.raise_for_status()
    vprint(f'Updated episode to {episode}')
