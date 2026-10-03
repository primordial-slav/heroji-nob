"""
Utility functions for generating and managing unique soldier IDs.

ID Format: BBBBNNNNNN (10 digits)
- BBBB = 4-digit brigade code (0001-9999)
- NNNNNN = 6-digit sequence number (000001-999999)
"""

import sys
import json
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Brigade code registry
BRIGADE_CODES = {
    1: "Prva Proleterska",
    2: "Prva Lička Proleterska",
    3: "Druga Lička Proleterska",
    4: "Ljubljanska (10. SNOUB)",
    5: "Treća Proleterska (Sandžačka)",
    6: '13. Proleterska "Rade Končar"',
    7: '2. Dalmatinska Proleterska',
    8: '4. Splitska Udarna',
    9: 'Prva Vojvođanska',
    10: '3. Krajiška Proleterska',
    11: '4. Krajiška',
    12: '5. Kozaračka Krajiška',
    13: '6. Krajiška',
    14: '8. Krajiška',
    15: '1. Šumadijska',
    16: '17. Slavonska Udarna',
    17: '18. Slavonska Udarna',
    18: '2. Vojvođanska',
    19: '25. Srpska Divizija',
    20: '4. Banijska',
    21: '4. Srpska',
    22: '7. Vojvođanska',
    23: '19. Birčanska',
    24: '2. Krajiška',
    25: 'Tuzlanski NOP odred',
    26: 'Užički NOP odred',
    27: '14. Srpska',
    28: '7. Crnogorska omladinska',
    29: '17. Majevička',
    30: '25. Brodska',
    31: '25. Srpska brigada',
    32: '21. Tuzlanska',
    33: '53. Srednjobosanska divizija',
    34: '21. Slavonska',
    35: '32. Zagorska divizija',
    36: '1. Dalmatinska',
    37: '16. Slavonska omladinska',
    38: '8. Crnogorska',
    39: 'Druga proleterska',
    40: '4. Proleterska',
    41: '5. Proleterska',
    42: '6. Istočnobosanska',
    43: '10. Hercegovačka',
    44: '7. Banijska',
    45: '8. Banijska',
    46: '3. Dalmatinska',
    47: '16. Banijska',
    48: '7. Krajiška',
    49: '15. Majevička',
    50: '12. Dalmatinska',
    51: '3. Makedonska',
    52: '18. Hrvatska istočnobosanska',
    53: '11. Dalmatinska',
    54: '12. Krajiška',
    55: '17. Srpska',
    56: '14. Srednjobosanska',
    57: '3. Vojvođanska',
    58: 'Kalnički odred',
    59: 'Posavsko-trebavski odred',
    60: '8. Kordunaška divizija',
    61: 'Cankarjeva',
    62: 'Gubčeva',
    63: 'Dvanajsta (XII. SNOUB)',
    64: 'Gradnikova',
    65: 'Zidanškova',
    66: 'Škofjeloški odred',
    67: 'Istrski odred',
    68: 'Zapadnodolenjski odred',
    69: 'Bračičeva',
    70: 'Tomšičeva',
    71: 'Prva slovenska artilerijska',
    72: 'Artilerija 9. korpusa',
    73: '19. Srpska',
    74: '22. Srpska kosmajska',
    75: '12. Vojvođanska',
    76: '4. Vojvođanska',
    77: '1. Kosovsko-metohijska',
    78: '8. Vojvođanska',
    79: '19. Sjevernodalmatinska divizija',
    80: '21. Srpska',
    81: '14. Hercegovačka',
    82: '5. Vojvođanska',
    83: '6. Vojvođanska',
    84: '13. Vojvođanska',
    85: '7. Srpska',
    86: '15. Srpska',
    87: '8. Srpska',
    88: '10. Srpska',
    89: '23. Srpska',
    90: '12. Srpska',
    91: '20. Srpska',
    92: '1. Konjička',
    93: 'Toplički NOP odred',
    94: 'Karlovačka udarna',
    95: '14. Primorsko-goranska',
    96: '22. divizija',
    97: '34. divizija',
    98: '4. Sandžačka',
    99: '3. Primorsko-goranska',
    100: '13. Hercegovačka',
    101: '12. Hercegovačka',
    102: '1. Bokeljska',
    103: '6. Dalmatinska',
    104: 'Osječka udarna',
    105: '1. Zagorska',
    106: '6. Crnogorska',
    107: '11. Krajiška',
    108: '3. Banijska',
    109: 'Mačvanski odred',
    # Add new brigades here with next available code
}

# Reverse lookup
BRIGADE_NAMES = {v: k for k, v in BRIGADE_CODES.items()}


def generate_soldier_id(brigade_code: int, sequence: int) -> str:
    """
    Generate a unique 10-digit soldier ID.

    Args:
        brigade_code: Brigade identifier (1-9999)
        sequence: Soldier sequence within brigade (1-999999)

    Returns:
        10-digit string ID like "0002004521"
    """
    if not (1 <= brigade_code <= 9999):
        raise ValueError(f"Brigade code must be 1-9999, got {brigade_code}")
    if not (1 <= sequence <= 999999):
        raise ValueError(f"Sequence must be 1-999999, got {sequence}")

    return f"{brigade_code:04d}{sequence:06d}"


def parse_soldier_id(soldier_id: str) -> dict:
    """
    Parse a soldier ID into its components.

    Args:
        soldier_id: 10-digit soldier ID string

    Returns:
        Dict with brigade_code, sequence, brigade_name, full_id
    """
    if len(soldier_id) != 10 or not soldier_id.isdigit():
        raise ValueError(f"Invalid soldier ID format: {soldier_id}")

    brigade_code = int(soldier_id[:4])
    sequence = int(soldier_id[4:])

    return {
        'brigade_code': brigade_code,
        'brigade_name': BRIGADE_CODES.get(brigade_code, "Unknown"),
        'sequence': sequence,
        'full_id': soldier_id
    }


def get_brigade_code(brigade_name: str) -> int:
    """Get brigade code from name (partial match supported)."""
    name_lower = brigade_name.lower()

    for name, code in BRIGADE_NAMES.items():
        if name_lower in name.lower() or name.lower() in name_lower:
            return code

    raise ValueError(f"Unknown brigade: {brigade_name}")


def assign_ids_to_soldiers(soldiers: list, brigade_code: int, start_sequence: int = 1) -> list:
    """
    Assign unique IDs to a list of soldiers.

    Args:
        soldiers: List of soldier dicts
        brigade_code: Brigade identifier
        start_sequence: Starting sequence number (default 1)

    Returns:
        List of soldiers with 'soldier_id' field added
    """
    for i, soldier in enumerate(soldiers, start_sequence):
        soldier['soldier_id'] = generate_soldier_id(brigade_code, i)

    return soldiers


def add_ids_to_json_file(input_file: str, output_file: str, brigade_code: int):
    """
    Read a soldiers JSON file, add IDs, and save to new file.

    Args:
        input_file: Path to input JSON
        output_file: Path to output JSON
        brigade_code: Brigade identifier
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        soldiers = json.load(f)

    soldiers = assign_ids_to_soldiers(soldiers, brigade_code)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(soldiers, f, ensure_ascii=False, indent=2)

    print(f"Added IDs to {len(soldiers)} soldiers")
    print(f"ID range: {soldiers[0]['soldier_id']} - {soldiers[-1]['soldier_id']}")
    print(f"Saved to: {output_file}")


def validate_ids(soldiers: list) -> dict:
    """
    Validate that all soldiers have unique, properly formatted IDs.

    Returns:
        Dict with validation results
    """
    issues = []
    seen_ids = set()

    for i, soldier in enumerate(soldiers):
        sid = soldier.get('soldier_id', '')

        # Check format
        if len(sid) != 10 or not sid.isdigit():
            issues.append(f"Row {i}: Invalid ID format: {sid}")
            continue

        # Check duplicates
        if sid in seen_ids:
            issues.append(f"Row {i}: Duplicate ID: {sid}")
        else:
            seen_ids.add(sid)

    return {
        'valid': len(issues) == 0,
        'total_soldiers': len(soldiers),
        'unique_ids': len(seen_ids),
        'issues': issues
    }


# Example usage
if __name__ == "__main__":
    # Example: Generate some IDs
    print("Example IDs:")
    print(f"  Prva Proleterska #1:    {generate_soldier_id(1, 1)}")
    print(f"  Prva Lička #4521:       {generate_soldier_id(2, 4521)}")
    print(f"  Druga Lička #1509:      {generate_soldier_id(3, 1509)}")
    print(f"  Ljubljanska #3079:      {generate_soldier_id(4, 3079)}")

    print("\nParsing example:")
    parsed = parse_soldier_id("0002004521")
    print(f"  ID 0002004521 = {parsed}")

    print("\nBrigade codes:")
    for code, name in sorted(BRIGADE_CODES.items()):
        print(f"  {code:04d} = {name}")
