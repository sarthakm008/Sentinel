import requests
import re

r = requests.get('http://localhost:5174/src/App.tsx', timeout=5)
print('App.tsx status:', r.status_code)
text = r.text
print('App.tsx length:', len(text))

# Check for routes
routes = re.findall(r'<Route[^>]*path=[\'"]([^\'"]*)[\'"]', text)
print('Routes found:', routes)

# Check for Evaluation route
if '/evaluation' in text:
    print('Evaluation route found in App.tsx')
else:
    print('Evaluation route NOT found in App.tsx')

# Check for Evaluation import
if 'Evaluation' in text:
    print('Evaluation import found')
else:
    print('Evaluation import NOT found')