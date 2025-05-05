import requests
import hashlib

def check_pwned_password(password):
    sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]
    response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
    return suffix in response.text

def check_email_breach(email):
    """
    Verifica se um e-mail foi exposto em vazamentos conhecidos via Have I Been Pwned.
    """
    try:
        response = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={"User-Agent": "DataGuardian"}
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Erro ao verificar e-mail: {e}")
        return []