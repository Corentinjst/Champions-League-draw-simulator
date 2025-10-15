"""
Configuration centralisée pour la Ligue des Champions.

Ce fichier contient toutes les constantes et paramètres du format de tirage,
permettant une modification facile des règles sans changer le code métier.
"""

# ============================================================================
# FORMAT DE LA PHASE LIGUE
# ============================================================================

# Nombre de matchs par club dans la phase ligue
MATCHES_PER_CLUB = 8

# Nombre de journées
JOURNEES = 8

# Nombre de matchs à domicile et en extérieur
HOME_MATCHES_PER_CLUB = 4
AWAY_MATCHES_PER_CLUB = 4

# Nombre de clubs participants
TOTAL_CLUBS = 36

# Distribution par chapeau
CLUBS_PER_CHAPEAU = {
    1: 9,   # Chapeau 1
    2: 9,   # Chapeau 2
    3: 9,   # Chapeau 3
    4: 9,   # Chapeau 4
}

# ============================================================================
# RÈGLES DE COMPOSITION
# ============================================================================

# Un club doit affronter combien de clubs de chaque chapeau ?
OPPONENTS_PER_CHAPEAU = {
    1: 2,   # 2 clubs du chapeau 1
    2: 2,   # 2 clubs du chapeau 2
    3: 2,   # 2 clubs du chapeau 3
    4: 2,   # 2 clubs du chapeau 4
}

# ============================================================================
# RÈGLES D'AFFRONTEMENTS
# ============================================================================

# Nombre maximum de clubs du même pays qu'un club peut affronter
MAX_SAME_COUNTRY_OPPONENTS = 0

# Nombre maximum d'adversaires issus d'une même AUTRE association (pays différent)
MAX_OPPONENTS_PER_FOREIGN_COUNTRY = 2

# ============================================================================
# RÈGLES DE BALANCE
# ============================================================================

# Distribution des matchs par chapeau
# (en général: 2 vs chapeau_1, 2 vs chapeau_2, etc.)
DISTRIBUTION_CHAPEAUX = {
    1: (1, 1),  # Chapeau 1: 1 à domicile, 1 en extérieur
    2: (1, 1),  # Chapeau 2: 1 à domicile, 1 en extérieur
    3: (1, 1),  # Chapeau 3: 1 à domicile, 1 en extérieur
    4: (1, 1),  # Chapeau 4: 1 à domicile, 1 en extérieur
}

# ============================================================================
# RÈGLES DE FAIRPLAY
# ============================================================================

# Maximum de matchs à domicile d'affilée
MAX_CONSECUTIVE_HOME_MATCHES = 2

# Maximum de matchs en extérieur d'affilée
MAX_CONSECUTIVE_AWAY_MATCHES = 2

# ============================================================================
# VALIDATIONS GLOBALES
# ============================================================================

def validate_config() -> bool:
    """
    Valide la cohérence globale de la configuration.
    
    Returns:
        True si la configuration est valide
    
    Raises:
        ValueError: Si la configuration est incohérente
    """
    # Total des clubs par chapeau
    total_clubs_config = sum(CLUBS_PER_CHAPEAU.values())
    if total_clubs_config != TOTAL_CLUBS:
        raise ValueError(
            f"Total des clubs par chapeau ({total_clubs_config}) != TOTAL_CLUBS ({TOTAL_CLUBS})"
        )

    # Couverture des chapeaux
    chapeaux_cfg = set(CLUBS_PER_CHAPEAU.keys())
    chapeaux_opp = set(OPPONENTS_PER_CHAPEAU.keys())
    chapeaux_dist = set(DISTRIBUTION_CHAPEAUX.keys())
    if not (chapeaux_cfg == chapeaux_opp == chapeaux_dist):
        raise ValueError(
            "Incohérence des clés entre CLUBS_PER_CHAPEAU, OPPONENTS_PER_CHAPEAU et DISTRIBUTION_CHAPEAUX"
        )

    # Nombre d'adversaires par chapeau
    total_opponents = sum(OPPONENTS_PER_CHAPEAU.values())
    if total_opponents != MATCHES_PER_CLUB:
        raise ValueError(
            f"Total des adversaires par chapeau ({total_opponents}) != MATCHES_PER_CLUB ({MATCHES_PER_CLUB})"
        )

    # Cohérence globale H/A
    if HOME_MATCHES_PER_CLUB + AWAY_MATCHES_PER_CLUB != MATCHES_PER_CLUB:
        raise ValueError(
            f"HOME_MATCHES_PER_CLUB + AWAY_MATCHES_PER_CLUB != MATCHES_PER_CLUB "
            f"({HOME_MATCHES_PER_CLUB} + {AWAY_MATCHES_PER_CLUB} != {MATCHES_PER_CLUB})"
        )

    # Distribution domicile/extérieur par chapeau + agrégats
    total_home, total_away = 0, 0
    for chapeau, (home, away) in DISTRIBUTION_CHAPEAUX.items():
        if home + away != OPPONENTS_PER_CHAPEAU.get(chapeau, 0):
            raise ValueError(
                f"Distribution H/A chapeau {chapeau}: {home} + {away} != {OPPONENTS_PER_CHAPEAU.get(chapeau)}"
            )
        total_home += home
        total_away += away

    if total_home != HOME_MATCHES_PER_CLUB or total_away != AWAY_MATCHES_PER_CLUB:
        raise ValueError(
            f"Somme H/A par chapeau incohérente avec les totaux: "
            f"H={total_home} vs {HOME_MATCHES_PER_CLUB}, A={total_away} vs {AWAY_MATCHES_PER_CLUB}"
        )

    # Parité du total de matchs (doit être pair avant division par 2)
    if (TOTAL_CLUBS * MATCHES_PER_CLUB) % 2 != 0:
        raise ValueError(
            f"({TOTAL_CLUBS} * {MATCHES_PER_CLUB}) doit être pair pour calculer le total de matchs."
        )

    return True


# Valide automatiquement au import
try:
    validate_config()
except ValueError as e:
    raise ValueError(f"Configuration invalide: {str(e)}")


# ============================================================================
# UTILITIES
# ============================================================================

def get_expected_total_matches() -> int:
    """Calcule le nombre total de matchs attendu."""
    return (TOTAL_CLUBS * MATCHES_PER_CLUB) // 2


def get_clubs_from_chapeau(chapeau: int) -> int:
    """Retourne le nombre de clubs d'un chapeau."""
    return CLUBS_PER_CHAPEAU.get(chapeau, 0)


def get_opponents_from_chapeau(chapeau: int) -> int:
    """Retourne le nombre d'adversaires à affronter d'un chapeau."""
    return OPPONENTS_PER_CHAPEAU.get(chapeau, 0)