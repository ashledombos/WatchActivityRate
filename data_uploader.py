import requests

def upload_to_sprunge(data):
    response = requests.post('http://sprunge.us', data={'sprunge': data})
    if response.status_code == 200:
        return response.text.strip()
    else:
        return None

# Exemple d'utilisation
if __name__ == "__main__":
    url = upload_to_sprunge("Vos données ici")
    if url:
        print(f"Les données ont été uploadées à {url}")
