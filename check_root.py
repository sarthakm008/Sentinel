import requests

r = requests.get('http://localhost:5174/', timeout=5)
print('Root page status:', r.status_code)
print('Length:', len(r.text))
print('Has root div:', 'id="root"' in r.text)
print('Has React:', 'react' in r.text.lower())
print('Has app:', 'Sentinel' in r.text)