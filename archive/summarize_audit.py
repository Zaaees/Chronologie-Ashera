import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('full_rp_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

channels = data['channels']
sorted_ch = sorted(channels.items(), key=lambda x: x[1]['scene_count'], reverse=True)

print("=== STATISTIQUES GLOBALES ===")
print(f"Nombre total de salons RP : {data['total_channels']}")
print(f"Nombre total de scènes RP : {data['total_scenes']}")
print(f"Nombre total d'anomalies détectées : {data['total_anomalies']}")

print("\n=== DÉCOMPOSITION DES ANOMALIES DÉTECTÉES ===")
for cat, cnt in data['anomaly_counts'].items():
    print(f"  - {cat}: {cnt}")

print("\n=== TOP 20 SALONS RP PAR NOMBRE DE SCÈNES ET PARTICIPANTS ===")
for ch, info in sorted_ch[:20]:
    parts_str = ", ".join(info['participants'][:5])
    if len(info['participants']) > 5:
        parts_str += f" (+{len(info['participants'])-5} autres)"
    print(f"• Salon: {ch:<35} | Scènes: {info['scene_count']:<3} | Msgs: {info['total_messages']:<4} | Mots: {info['total_words']:<6} | Participants: {parts_str}")

print("\n=== SALONS DUPLIQUÉS / VARIANTES DE NOMS ===")
for inc in data['anomalies']:
    if inc['type'] == 'DUPLICATE_CHANNEL_VARIANTS':
        print(f"  - {inc['channel']} => {inc['details']}")

print("\n=== ANOMALIES CRITIQUES (1 à 2 messages) ===")
for inc in data['anomalies']:
    if inc['type'] == 'CRITICAL_LOW_MESSAGES':
        print(f"  - [{inc['scene_id']}] Salon: {inc['channel']} | Titre: '{inc['title']}' | {inc['msg_count']} msgs | Acteurs: {inc['actors']}")

print("\n=== ANOMALIES ACTEUR UNIQUE (Monologues / Scènes isolées) ===")
for inc in data['anomalies'][:10]:
    if inc['type'] == 'SINGLE_ACTOR':
        print(f"  - [{inc['scene_id']}] Salon: {inc['channel']} | Titre: '{inc['title']}' | {inc['msg_count']} msgs | Acteur: {inc['actors']}")

