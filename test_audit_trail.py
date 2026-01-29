from backend.parsers.xbrl_parser import XBRLParser
import json

parser = XBRLParser('data/apple_10k_xbrl.xml')
parser.load()

# Obtener un resultado con audit trail
aliases = parser._get_concept_aliases('Revenue')
available_tags = parser._get_available_tags()

result = parser.fuzzy_mapper.fuzzy_match_alias(
    concept='Revenue',
    available_tags=available_tags,
    aliases=aliases
)

if result:
    print("\n" + "="*70)
    print("AUDIT TRAIL - Revenue Match")
    print("="*70)
    print(json.dumps(result.to_dict(), indent=2))
    print("="*70)
