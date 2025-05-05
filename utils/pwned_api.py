import requests
import hashlib

def check_pwned_password(password):
    """Verifica senhas vazadas via HIBP API"""
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]
    
    response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
    return suffix in response.text

def check_email_breach(email):
    """Verifica e-mails vazados"""
    response = requests.get(
        f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
        headers={"User-Agent": "DataGuardian"}
    )
    return response.json() if response.status_code == 200 else []