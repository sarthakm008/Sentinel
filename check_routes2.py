import requests
import re

r = requests.get('http://localhost:5174/src/App.tsx')
text = r.text
print('App.tsx status:', r.status_code)

# Find the Routes section
routes_section = re.search(r'<Routes>.*?</Routes>', text, re.DOTALL)
if routes_section:
    print('Routes section found:')
    print(routes_section.group()[:3000])
else:
    print('No Routes section found')
    # Search for Route patterns
    routes = re.findall(r'Route[^>]*path=[\'"]([^\'"]*)[\'"]', text)
    print('Routes found:', routes)