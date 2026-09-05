import requests

r = requests.get('http://localhost:5174/evaluation', timeout=5)
print('Status:', r.status_code)
print('Body length:', len(r.text))
print('Has root div:', 'id="root"' in r.text)
print('Has React:', 'react' in r.text.lower())
print('Has app:', 'Sentinel' in r.text)

# Also check the console for JS errors by checking the built JS
import requests
r2 = requests.get('http://localhost:5174/src/pages/Evaluation.tsx')
print('\\nEval.tsx status:', r2.status_code)
print('Eval.tsx length:', len(r2.text))
print('First 2000 chars:', r2.text[:2000])