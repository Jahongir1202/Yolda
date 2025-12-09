UZBEK_KEYWORDS = [
    "uzbekistan", "uzbekiston", "uzb", "uz",
    "tashkent", "toshkent",
    "andijan", "andijon",
    "fergana", "farg'ona", "fargona",
    "namangan",
    "samarkand", "samarqand",
    "bukhara", "buxoro",
    "navoi", "navoiy",
    "khorezm", "xorazm",
    "karakalpakstan", "qoraqalpog'iston",
    "termiz", "surxondaryo"
]


def is_uzbek_related(text: str) -> bool:
    text = text.lower()
    for word in UZBEK_KEYWORDS:
        if word in text:
            return True
    return False
