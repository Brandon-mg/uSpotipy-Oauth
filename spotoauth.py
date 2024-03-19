import random
import hashlib
import ubinascii
import secrets
import urequests as requests
import network
import time
import ujson

code_verifier = None
code = None
redirect_uri="https://localhost:8888/callback"


def network_connect(ssid, psk):

    # Number of attempts to make before timeout
    max_wait = 5

    # Sets the Wireless LED pulsing and attempts to connect to your local network.
    print("connecting...")
    wlan.config(pm=0xa11140)  # Turn WiFi power saving off for some slow APs
    wlan.connect(ssid, psk)

    while max_wait:
        if max_wait==0:
            wlan.connect(ssid, psk)
        if wlan.status==3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    # Handle connection error. Switches the Warn LED on.
    if wlan.status() != 3:
        print("Unable to connect. Attempting connection again")

    
def gen_code_verifier():
    char_set ='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    tok="".join([random.choice(char_set) for i in range(128)])
    return tok

def gen_code_challenge(token):
    data = token.encode()
    digest = hashlib.sha256(data).digest()
    encoded = ubinascii.b2a_base64(digest)
    challenge = ubinascii.b2a_base64(encoded).decode('ascii').replace("+","-").replace("/","_")[:-2]
    return challenge

def auth_code_flow():
    verifier = gen_code_verifier()
    challenge = gen_code_challenge(verifier)
    params="client_id="+secrets.SPOT_ID+"&response_type=code&redirect_uri="+redirect_uri+"&scope=user-read-private+user-read-email&code_challenge_method=S256&code_challenge="+challenge
    url = "http://accounts.spotify.com/authorize?"
    return url+params, verifier

def get_access_token(code, code_verifier):
    params=ujson.dumps({"client_id":secrets.SPOT_ID,
            "grant_type":"authorization_code",
            "code":code,
            "redirect_uri":redirect_uri,
            "code_verifier":code_verifier})
    header = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "https://accounts.spotify.com/api/token"
    print(params)
    return requests.post(url, headers = header, data = params).json()

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
print("turning on wifi")
auth, code_verifier = auth_code_flow()
while wlan.status() != 3:
    try:
        network_connect(secrets.SSID, secrets.PSK)
        time.sleep(10)

    except OSError:
        print("Retrying")
res = requests.get(auth)
access_token = get_access_token(code_verifier)
