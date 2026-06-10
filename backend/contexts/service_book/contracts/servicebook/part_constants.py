from typing import Dict, List

SB_COLLECTION_LIST: List[str] = [
    "service_book_part_i",
    "service_book_part_ii_a",
    "service_book_part_ii_b",
    "service_book_part_iii",
    "service_book_part_iv",
    "service_book_part_v",
    "service_book_part_vi",
    "service_book_part_vii",
    "service_book_part_viii",
]

SB_COLLECTION_MAP: Dict[str, str] = {
    "PART_I": "service_book_part_i",
    "PART_II_A": "service_book_part_ii_a",
    "PART_II_B": "service_book_part_ii_b",
    "PART_III": "service_book_part_iii",
    "PART_IV": "service_book_part_iv",
    "PART_V": "service_book_part_v",
    "PART_VI": "service_book_part_vi",
    "PART_VII": "service_book_part_vii",
    "PART_VIII": "service_book_part_viii",
}

SB_PART_KEY_MAP: Dict[str, str] = {
    "I": "service_book_part_i",
    "II-A": "service_book_part_ii_a",
    "II-B": "service_book_part_ii_b",
    "III": "service_book_part_iii",
    "IV": "service_book_part_iv",
    "V": "service_book_part_v",
    "VI": "service_book_part_vi",
    "VII": "service_book_part_vii",
    "VIII": "service_book_part_viii",
}

SB_LEDGER_PART_KEY_BY_ROMAN: Dict[str, str] = {
    "I": "SB_PART_I",
    "II-A": "SB_PART_II_A",
    "II-B": "SB_PART_II_B",
    "III": "SB_PART_III",
    "IV": "SB_PART_IV",
    "V": "SB_PART_V",
    "VI": "SB_PART_VI",
    "VII": "SB_PART_VII",
    "VIII": "SB_PART_VIII",
}

SERVICE_BOOK_MUTABLE_PART_KEYS = {
    SB_LEDGER_PART_KEY_BY_ROMAN["I"],
    SB_LEDGER_PART_KEY_BY_ROMAN["II-A"],
    SB_LEDGER_PART_KEY_BY_ROMAN["II-B"],
    SB_LEDGER_PART_KEY_BY_ROMAN["III"],
    SB_LEDGER_PART_KEY_BY_ROMAN["V"],
    SB_LEDGER_PART_KEY_BY_ROMAN["VII"],
    SB_LEDGER_PART_KEY_BY_ROMAN["VIII"],
}

SERVICE_EVENTS_OWNED_PART_KEYS = {
    SB_LEDGER_PART_KEY_BY_ROMAN["IV"],
}

LEAVE_OWNED_PART_KEYS = {
    SB_LEDGER_PART_KEY_BY_ROMAN["VI"],
}