#!/usr/bin/env python3
"""
Generate comprehensive planetary entity list from all attribution data.
Consolidates entities from cultural attribution, bot owners, etc.
"""
import json
from collections import defaultdict

# Load cultural attribution
with open('bot_cultural_attribution.json', 'r') as f:
    cultural_data = json.load(f)

# Extract all unique entities
entities = {}
entity_stats = defaultdict(lambda: {'bots': [], 'total_volume': 0, 'confidence_sum': 0, 'count': 0})

for symbol, bots in cultural_data.items():
    for bot in bots:
        owner = bot.get('owner_entity')
        if owner and owner != 'UNKNOWN':
            entity_stats[owner]['bots'].append(bot['bot_id'])
            entity_stats[owner]['confidence_sum'] += bot.get('confidence', 0)
            entity_stats[owner]['count'] += 1
            
            if owner not in entities:
                entities[owner] = {
                    'entity_name': owner,
                    'type': bot.get('owner_type', 'unknown'),
                    'country': bot.get('owner_country', 'unknown'),
                    'bots_controlled': [],
                    'avg_confidence': 0,
                    'symbols': set()
                }
            
            entities[owner]['bots_controlled'].append(bot['bot_id'])
            entities[owner]['symbols'].add(symbol)

# Compute averages and clean up
for owner, data in entities.items():
    stats = entity_stats[owner]
    data['avg_confidence'] = stats['confidence_sum'] / stats['count'] if stats['count'] > 0 else 0
    data['total_bots'] = len(set(data['bots_controlled']))
    data['symbols'] = list(data['symbols'])

# Convert to list
entity_list = list(entities.values())

# Save
with open('consolidated_entity_list.json', 'w') as f:
    json.dump(entity_list, f, indent=2)

print(f"✅ Consolidated {len(entity_list)} unique entities")
for entity in sorted(entity_list, key=lambda x: x['total_bots'], reverse=True):
    print(f"  - {entity['entity_name']}: {entity['total_bots']} bots, {entity['avg_confidence']*100:.0f}% confidence")
