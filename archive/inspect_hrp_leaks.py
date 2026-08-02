import json
import re

with open('scenes_fixed_simulated.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

HRP_PATTERNS = [
    r'navr[eé].*(retard|impr[eé]vu|attente|temps)',
    r'd[eé]sol[eé].*(retard|impr[eé]vu|attente|temps)',
    r'\(?\s*hrp\s*:.*?\)?',
    r'<@&?\d+>',
    r'@\S+',
    r'^\s*\|\|.*\|\|\s*$'
]
HRP_REGEX = re.compile('|'.join(HRP_PATTERNS), re.IGNORECASE)

samples = []
for s in data.get('scenes', []):
    for m in s.get('messages', []):
        c = m.get('content', '')
        match = HRP_REGEX.search(c)
        if match:
            samples.append((s['channel_clean'], match.group(0), c))

print(f"Total HRP matches: {len(samples)}")
print("Sample 10 remaining HRP matches:")
for ch, match_str, content in samples[:10]:
    print(f"  [{ch}] Matched: {repr(match_str)}")
    print(f"    Full content snippet: {repr(content[:150])}\n")
