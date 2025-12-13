"""Constants for FlipRadar API."""

# Supported sources
SOURCES = [
    "nike",
    "adidas",
    "zalando",
    "courir",
    "footlocker",
    "ralph_lauren",
]

# Categories
CATEGORIES = [
    "sneakers",
    "textile",
    "accessoires",
]

# Subcategories by category
SUBCATEGORIES = {
    "sneakers": ["lifestyle", "running", "basketball", "trail", "skateboarding"],
    "textile": ["polos", "shirts", "tshirts", "knitwear", "jackets", "pants", "streetwear", "premium"],
    "accessoires": ["caps", "bags", "belts", "watches", "other"],
}

# Popular brands for scoring
BRAND_POPULARITY = {
    "Nike": 90,
    "Jordan": 95,
    "Adidas": 85,
    "New Balance": 80,
    "Asics": 70,
    "Puma": 65,
    "Reebok": 60,
    "Converse": 70,
    "Vans": 65,
    "Ralph Lauren": 75,
    "Lacoste": 70,
    "Tommy Hilfiger": 65,
}

# Standard sizes by category
POPULAR_SIZES = {
    "sneakers": {
        "men": ["41", "42", "43", "44", "45"],
        "women": ["37", "38", "39", "40"],
        "kids": ["35", "36", "37"],
    },
    "textile": {
        "men": ["M", "L", "XL"],
        "women": ["S", "M", "L"],
    },
}

# Safe colors for faster resale
SAFE_COLORS = ["black", "white", "grey", "navy", "noir", "blanc", "gris", "bleu marine"]

# Score thresholds
SCORE_THRESHOLDS = {
    "excellent": 80,
    "good": 60,
    "average": 40,
    "poor": 20,
}

# User plans
USER_PLANS = {
    "free": {
        "alerts_per_day": 5,
        "sources": 2,
        "history_days": 7,
    },
    "starter": {
        "alerts_per_day": 20,
        "sources": 4,
        "history_days": 30,
    },
    "pro": {
        "alerts_per_day": -1,  # Unlimited
        "sources": -1,  # All
        "history_days": 90,
    },
    "agency": {
        "alerts_per_day": -1,
        "sources": -1,
        "history_days": 365,
        "api_access": True,
        "multi_user": True,
    },
}
