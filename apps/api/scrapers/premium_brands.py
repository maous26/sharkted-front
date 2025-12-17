"""
Liste des marques premium/attractives pour le filtrage textile.
Seuls les produits de ces marques seront conservés lors du scraping.
Les marques distributeur (ASOS, Bonobo, Kiabi, etc.) sont exclues.
"""

# === MARQUES PREMIUM/LUXE ACCESSIBLE ===
LUXURY_ACCESSIBLE = {
    "ralph lauren", "polo ralph lauren",
    "lacoste",
    "tommy hilfiger",
    "hugo boss", "boss",
    "calvin klein", "ck",
    "armani", "armani exchange", "emporio armani", "ea7",
    "diesel",
    "kenzo",
    "sandro", "maje",
    "the kooples",
    "ami", "ami paris",
    "a.p.c.", "apc",
    "acne studios",
    "isabel marant",
    "zadig & voltaire", "zadig et voltaire",
    "ba&sh",
    "claudie pierlot",
}

# === MARQUES STREETWEAR/HYPE ===
STREETWEAR_BRANDS = {
    # Nike ecosystem
    "nike", "jordan", "nike acg", "nike sb",
    # Adidas ecosystem
    "adidas", "adidas originals", "y-3",
    # Premium streetwear
    "supreme",
    "off-white",
    "palm angels",
    "stone island",
    "cp company", "c.p. company",
    "moncler",
    "canada goose",
    "fear of god", "essentials", "fog essentials",
    "rhude",
    "amiri",
    "represent",
    "gallery dept",
    "vetements",
    # Streetwear classique
    "stussy", "stüssy",
    "carhartt", "carhartt wip",
    "dickies",
    "champion",
    "the north face", "tnf",
    "patagonia",
    "arc'teryx", "arcteryx",
    "salomon",
    "hoka",
    # Japonais
    "comme des garçons", "comme des garcons", "cdg",
    "bape", "a bathing ape",
    "human made",
    "undercover",
    "neighborhood",
    "wtaps",
    "sacai",
    "visvim",
    # Skatewear
    "palace",
    "dime",
    "polar skate co",
    # Nouveaux
    "aimé leon dore", "aime leon dore", "ald",
    "new balance", "nb",
    "asics",
    "kith",
    "noah",
    "awake ny",
    "sporty & rich",
    "museum of peace and quiet", "mopq",
    "pas normal studios",
    "satisfy running",
    "district vision",
}

# === MARQUES SPORT PREMIUM ===
SPORT_PREMIUM = {
    "puma",
    "reebok",
    "fila",
    "diadora",
    "le coq sportif",
    "umbro",
    "kappa",
    "sergio tacchini",
    "ellesse",
    "fred perry",
    "ben sherman",
    "lyle & scott",
    "barbour",
    "belstaff",
    "woolrich",
}

# === MARQUES OUTDOOR/TECHNIQUE ===
OUTDOOR_BRANDS = {
    "the north face",
    "patagonia",
    "arc'teryx", "arcteryx",
    "columbia",
    "helly hansen",
    "napapijri",
    "k-way",
    "fjallraven",
    "timberland",
    "vans",
    "converse",
}

# === MARQUES DENIM/HERITAGE ===
DENIM_HERITAGE = {
    "levi's", "levis",
    "wrangler",
    "lee",
    "g-star", "g-star raw",
    "nudie jeans",
    "edwin",
    "naked & famous",
    "rag & bone",
    "citizens of humanity",
    "7 for all mankind",
    "true religion",
    "replay",
    "pepe jeans",
    "scotch & soda",
}

# === MARQUES LUXE (si trouvées en solde) ===
LUXURY_BRANDS = {
    "gucci",
    "prada",
    "balenciaga",
    "burberry",
    "versace",
    "givenchy",
    "fendi",
    "valentino",
    "bottega veneta",
    "loewe",
    "celine",
    "saint laurent", "ysl",
    "alexander mcqueen",
    "maison margiela", "margiela",
    "rick owens",
    "jil sander",
    "jacquemus",
    "loro piana",
    "brunello cucinelli",
    "zegna", "ermenegildo zegna",
    "tod's", "tods",
    "golden goose",
    "common projects",
}

# === MARQUES A EXCLURE (distributeurs, fast fashion, MDD) ===
EXCLUDED_BRANDS = {
    # Fast fashion
    "asos", "asos design", "asos 4505",
    "h&m", "hm",
    "zara",
    "pull & bear", "pull and bear",
    "bershka",
    "stradivarius",
    "mango",
    "primark",
    "shein",
    "boohoo",
    "prettylittlething",
    "missguided",
    "plt",
    "fashion nova",
    # Distributeurs français
    "la redoute collections", "la redoute création",
    "kiabi",
    "gémo", "gemo",
    "c&a", "c and a",
    "celio",
    "jules",
    "brice",
    "promod",
    "camaieu",
    "pimkie",
    "jennyfer",
    "cache cache",
    "bonobo", "bonobo jeans",
    "bizzbee",
    "grain de malice",
    # Autres MDD
    "monoprix",
    "vertbaudet",
    "blancheporte",
    "3 suisses",
    "damart",
    "daxon",
    "bonprix",
    "venca",
    "simply be",
    "yours clothing",
    "evans",
    "jacamo",
    # Marques génériques
    "noname", "no name",
    "sans marque",
    "generique", "générique",
    "marque inconnue",
}

# === ENSEMBLE COMPLET DES MARQUES ATTRACTIVES ===
ATTRACTIVE_BRANDS = (
    LUXURY_ACCESSIBLE |
    STREETWEAR_BRANDS |
    SPORT_PREMIUM |
    OUTDOOR_BRANDS |
    DENIM_HERITAGE |
    LUXURY_BRANDS
)


def is_attractive_brand(brand: str) -> bool:
    """
    Vérifie si une marque est attractive pour la revente.

    Args:
        brand: Nom de la marque à vérifier

    Returns:
        True si la marque est attractive, False sinon
    """
    if not brand:
        return False

    brand_lower = brand.lower().strip()

    # D'abord vérifier si c'est exclu
    if brand_lower in EXCLUDED_BRANDS:
        return False

    # Ensuite vérifier si c'est dans les marques attractives
    if brand_lower in ATTRACTIVE_BRANDS:
        return True

    # Vérification partielle pour les variantes
    for attractive in ATTRACTIVE_BRANDS:
        if attractive in brand_lower or brand_lower in attractive:
            return True

    return False


def get_brand_tier(brand: str) -> str:
    """
    Retourne le tier de la marque (S, A, B, C ou X pour exclu).

    Args:
        brand: Nom de la marque

    Returns:
        Tier de la marque
    """
    if not brand:
        return "X"

    brand_lower = brand.lower().strip()

    if brand_lower in EXCLUDED_BRANDS:
        return "X"

    if brand_lower in LUXURY_BRANDS:
        return "S"

    if brand_lower in STREETWEAR_BRANDS:
        # Distinguer les tiers dans streetwear
        top_streetwear = {"nike", "jordan", "adidas", "supreme", "off-white", "stone island",
                         "moncler", "canada goose", "the north face", "fear of god", "essentials"}
        if brand_lower in top_streetwear:
            return "S"
        return "A"

    if brand_lower in LUXURY_ACCESSIBLE:
        return "A"

    if brand_lower in SPORT_PREMIUM or brand_lower in OUTDOOR_BRANDS:
        return "B"

    if brand_lower in DENIM_HERITAGE:
        return "B"

    return "C"


def normalize_brand_name(brand: str) -> str:
    """
    Normalise le nom de la marque pour l'affichage.

    Args:
        brand: Nom brut de la marque

    Returns:
        Nom normalisé
    """
    if not brand:
        return ""

    brand_lower = brand.lower().strip()

    # Map de normalisation
    normalization_map = {
        "polo ralph lauren": "Ralph Lauren",
        "nike acg": "Nike ACG",
        "nike sb": "Nike SB",
        "adidas originals": "Adidas Originals",
        "the north face": "The North Face",
        "tnf": "The North Face",
        "fog essentials": "Fear of God Essentials",
        "cdg": "Comme des Garçons",
        "comme des garcons": "Comme des Garçons",
        "ald": "Aimé Leon Dore",
        "aime leon dore": "Aimé Leon Dore",
        "nb": "New Balance",
        "ck": "Calvin Klein",
        "ysl": "Saint Laurent",
        "saint laurent": "Saint Laurent",
        "levis": "Levi's",
        "levi's": "Levi's",
        "g-star raw": "G-Star RAW",
        "g-star": "G-Star RAW",
        "cp company": "C.P. Company",
        "c.p. company": "C.P. Company",
        "arc'teryx": "Arc'teryx",
        "arcteryx": "Arc'teryx",
        "stüssy": "Stüssy",
        "stussy": "Stüssy",
    }

    if brand_lower in normalization_map:
        return normalization_map[brand_lower]

    # Capitalisation par défaut
    return brand.title()
