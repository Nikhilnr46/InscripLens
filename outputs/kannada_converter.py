"""Roman transliteration to Kannada script converter for InscripLens.
Converts IAST / Epigraphia Carnatica transliteration into Unicode NFC Kannada text.
Display-only: never modifies stored transliteration or model weights.
"""

import unicodedata
from typing import Optional, Tuple, Dict

# Consonant definitions (ordered by longest match first)
CONSONANTS = [
    # Multi-character aspirated/special consonants
    ('kh', '\u0c96'),      # ಖ
    ('gh', '\u0c98'),      # ಘ
    ('ch', '\u0c9b'),      # ಛ
    ('jh', '\u0c9d'),      # ಝ
    ('\u1e6dh', '\u0ca0'),  # ಠ (ṭh)
    ('\u1e0dh', '\u0ca2'),  # ಢ (ḍh)
    ('th', '\u0ca5'),      # ಥ
    ('dh', '\u0ca7'),      # ಧ
    ('ph', '\u0cab'),      # ಫ
    ('bh', '\u0cad'),      # ಭ
    ('l\u0324', '\u0cde'),  # ೞ (archaic l̤ / ḻ)
    
    # Single-character consonants
    ('k', '\u0c95'),       # ಕ
    ('g', '\u0c97'),       # ಗ
    ('\u1e45', '\u0c99'),  # ಙ (ṅ)
    ('c', '\u0c9a'),       # ಚ
    ('j', '\u0c9c'),       # ಜ
    ('\xf1', '\u0c9e'),    # ಞ (ñ)
    ('\u1e6d', '\u0c9f'),  # ಟ (ṭ)
    ('\u1e0d', '\u0ca1'),  # ಡ (ḍ)
    ('\u1e47', '\u0ca3'),  # ಣ (ṇ)
    ('t', '\u0ca4'),       # ತ
    ('d', '\u0ca6'),       # ದ
    ('n', '\u0ca8'),       # ನ
    ('p', '\u0caa'),       # ಪ
    ('b', '\u0cac'),       # ಬ
    ('m', '\u0cae'),       # ಮ
    ('y', '\u0caf'),       # ಯ
    ('r', '\u0cb0'),       # ರ
    ('\u1e5f', '\u0c91'),  # ಱ (ṟ - archaic r)
    ('l', '\u0cb2'),       # ಲ
    ('\u1e37', '\u0cb3'),  # ಳ (ḷ)
    ('\u1e3b', '\u0cde'),  # ೞ (ḻ - archaic l)
    ('v', '\u0cb5'),       # ವ
    ('\u015b', '\u0cb6'),  # ಶ (ś)
    ('\u1e63', '\u0cb7'),  # ಷ (ṣ)
    ('s', '\u0cb8'),       # ಸ
    ('h', '\u0cb9'),       # ಹ
]

# Independent vowels
INDEPENDENT_VOWELS = [
    ('ai', '\u0c90'),      # ಐ
    ('au', '\u0c94'),      # ಔ
    ('a', '\u0c85'),       # ಅ
    ('\u0101', '\u0c86'),  # ಆ (ā)
    ('i', '\u0c87'),       # ಇ
    ('\u012b', '\u0c88'),  # ಈ (ī)
    ('u', '\u0c89'),       # ಉ
    ('\u016b', '\u0c8a'),  # ಊ (ū)
    ('\u1e5b', '\u0c8b'),  # ಋ (ṛ)
    ('\u0115', '\u0c8e'),  # ಎ (ĕ - short e)
    ('e', '\u0c8f'),       # ಏ (e - long e)
    ('\u0113', '\u0c8f'),  # ಏ (ē - long e)
    ('\u014f', '\u0c92'),  # ಒ (ŏ - short o)
    ('o', '\u0c93'),       # ಓ (o - long o)
    ('\u014d', '\u0c93'),  # ಓ (ō - long o)
]

# Dependent vowel signs (matras attached to consonants)
# Note: 'a' has no dependent sign (inherent in consonant)
VOWEL_SIGNS = [
    ('ai', '\u0cc8'),      # ೈ
    ('au', '\u0ccc'),      # ೌ
    ('\u0101', '\u0cbe'),  # ಾ (ā)
    ('i', '\u0cbf'),       # ಿ
    ('\u012b', '\u0cc0'),  # ೀ (ī)
    ('u', '\u0cc1'),       # ು
    ('\u016b', '\u0cc2'),  # ೂ (ū)
    ('\u1e5b', '\u0cc3'),  # ೃ (ṛ)
    ('\u0115', '\u0cc6'),  # ೆ (ĕ - short e)
    ('e', '\u0cc7'),       # ೇ (e - long e)
    ('\u0113', '\u0cc7'),  # ೇ (ē - long e)
    ('\u014f', '\u0cca'),  # ೊ (ŏ - short o)
    ('o', '\u0ccb'),       # ೋ (o - long o)
    ('\u014d', '\u0ccb'),  # ೋ (ō - long o)
    ('a', ''),             # inherent vowel
]

# Modifiers
MODIFIERS = [
    ('\u1e43', '\u0c82'),  # ಂ (ṃ - anusvara)
    ('\u1e25', '\u0c83'),  # ಃ (ḥ - visarga)
]

VIRAMA = '\u0ccd'          # ್ (halant / virama)

# Archaic to modern letter mappings
ARCHAIC_TO_MODERN = {
    '\u0c91': '\u0cb0',    # ಱ -> ರ
    '\u0cde': '\u0cb3',    # ೞ -> ಳ
}

# Explicit special words / numbers
SPECIAL_MAPPINGS = {
    'siddha\u1e43': '\u0cb8\u0cbf\u0ca6\u0ccd\u0ca7\u0c82', # ಸಿದ್ಧಂ
    '\u1e43': '\u0c82',     # ಂ
    '\u0c84': '\u0c84',     # ಄
    '\u0ce6': '\u0ce6',     # ೦
    '0': '\u0ce6',          # ೦
    '1': '\u0ce7',          # ೧
    '2': '\u0ce8',          # ೨
    '3': '\u0ce9',          # ೩
    '4': '\u0cea',          # ೪
    '5': '\u0ceb',          # ೫
    '6': '\u0cec',          # ೬
    '7': '\u0ced',          # ೭
    '8': '\u0cee',          # ೮
    '9': '\u0cef',          # ೯
}


def to_kannada(text: str) -> Optional[str]:
    """Convert a Roman transliterated character or syllable to Kannada Unicode NFC.
    
    Returns NFC Kannada string if conversion is certain, or None if unmapped/ambiguous.
    """
    if not text or not isinstance(text, str):
        return None
    
    text = unicodedata.normalize('NFC', text.strip())
    if not text:
        return None
        
    # Check special mappings table
    if text in SPECIAL_MAPPINGS:
        return unicodedata.normalize('NFC', SPECIAL_MAPPINGS[text])
        
    # Check if string starts with leading anusvara (e.g. ṃda -> ಂದ)
    prefix = ''
    s = text
    if s.startswith('\u1e43'):
        prefix = '\u0c82'
        s = s[1:]
        
    # Strip trailing anusvara or visarga
    mod = ''
    for m_rom, m_kan in MODIFIERS:
        if s.endswith(m_rom):
            mod = m_kan
            s = s[:-len(m_rom)]
            break
            
    # Check independent vowel
    for v_rom, v_kan in INDEPENDENT_VOWELS:
        if s == v_rom:
            return unicodedata.normalize('NFC', prefix + v_kan + mod)
            
    # Check consonant cluster + vowel sign
    for v_rom, v_matra in VOWEL_SIGNS:
        if s.endswith(v_rom):
            rem_cons = s[:-len(v_rom)]
            if not rem_cons:
                continue
                
            idx = 0
            cons_list = []
            valid = True
            while idx < len(rem_cons):
                matched = False
                for c_rom, c_kan in CONSONANTS:
                    if rem_cons.startswith(c_rom, idx):
                        cons_list.append(c_kan)
                        idx += len(c_rom)
                        matched = True
                        break
                if not matched:
                    valid = False
                    break
                    
            if valid and cons_list:
                res = ''
                for i, c in enumerate(cons_list):
                    if i > 0:
                        res += VIRAMA
                    res += c
                res += v_matra + mod
                return unicodedata.normalize('NFC', prefix + res)
                
    return None


def to_modern_kannada(kannada_text: str) -> Tuple[str, bool]:
    """Replace archaic Kannada letters (ಱ, ೞ) with modern equivalents (ರ, ಳ).
    
    Returns (modified_text, is_lossy).
    """
    if not kannada_text:
        return kannada_text, False
        
    is_lossy = False
    result = []
    for ch in kannada_text:
        if ch in ARCHAIC_TO_MODERN:
            result.append(ARCHAIC_TO_MODERN[ch])
            is_lossy = True
        else:
            result.append(ch)
            
    return unicodedata.normalize('NFC', ''.join(result)), is_lossy


def format_display_label(
    roman_label: str,
    script_mode: str = 'kannada',
    modern_letters: bool = False
) -> Dict[str, any]:
    """Format label for UI display according to active script switch.
    
    Returns a dict with:
      - primary: large text to display
      - secondary: small text underneath (or None if script_mode == 'roman')
      - is_lossy: boolean if archaic letters were replaced with modern equivalents
      - is_unmapped: boolean if Roman transliteration could not be converted
      - roman: original unaltered Roman transliteration
      - kannada: converted Kannada text (or None)
    """
    kannada = to_kannada(roman_label)
    
    if kannada is None:
        # Unmapped: show Roman with small marker
        return {
            'primary': roman_label,
            'secondary': None,
            'is_lossy': False,
            'is_unmapped': True,
            'roman': roman_label,
            'kannada': None
        }
        
    is_lossy = False
    display_kannada = kannada
    if modern_letters:
        display_kannada, is_lossy = to_modern_kannada(kannada)
        
    if script_mode == 'roman':
        return {
            'primary': roman_label,
            'secondary': None,
            'is_lossy': False,
            'is_unmapped': False,
            'roman': roman_label,
            'kannada': display_kannada
        }
        
    # script_mode == 'kannada'
    return {
        'primary': display_kannada,
        'secondary': roman_label,
        'is_lossy': is_lossy,
        'is_unmapped': False,
        'roman': roman_label,
        'kannada': display_kannada
    }

