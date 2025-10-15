"""
Définition des contraintes de la Ligue des Champions (phase de ligue, nouveau format).

Ce module formalise les règles métier du tirage de la phase ligue.
Les contraintes sont décrites de manière déclarative, indépendante du solveur.

Aligné sur les règles explicites :
- Nombre de matchs par club et équilibre domicile/extérieur (via config)
- Répartition par chapeaux (2 adversaires par chapeau, avec 1 domicile / 1 extérieur)
- Aucune rencontre entre clubs d'une même association
- Au plus 2 adversaires d'une même AUTRE association
- (Équilibrage de séquences H/A en "soft")
"""

from typing import List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from src.models.club import Club
from src.models.match import Match
from src.models.draw import Draw
import src.config as config


class ConstraintType(Enum):
    """Types de contraintes CSP."""
    UNARY = "unary"              # Contrainte sur un club
    BINARY = "binary"            # Contrainte entre deux clubs
    GLOBAL = "global"            # Contrainte globale
    SOFT = "soft"                # Contrainte souple (préférence)


@dataclass
class Constraint:
    """
    Représente une contrainte du tirage.
    
    Attributes:
        name: Nom descriptif de la contrainte
        constraint_type: Type de contrainte
        check_fn: Fonction qui valide la contrainte
        severity: "hard" (obligatoire) ou "soft" (préférence)
        description: Texte explicatif
    """
    name: str
    constraint_type: ConstraintType
    check_fn: Callable[[Draw], bool]
    severity: str = "hard"
    description: str = ""
    
    def is_satisfied(self, draw: Draw) -> bool:
        """Vérifie si la contrainte est satisfaite."""
        return self.check_fn(draw)


class UCLConstraints:
    """
    Gestionnaire des contraintes de la Ligue des Champions.
    
    Centralise toutes les règles et fournit des méthodes pour les vérifier.
    """
    
    def __init__(self):
        """Initialise toutes les contraintes."""
        self.constraints: List[Constraint] = []
        self._build_constraints()
    
    def _build_constraints(self):
        """Construit toutes les contraintes du tirage."""
        
        # ====================================================================
        # CONTRAINTES SUR LE NOMBRE DE MATCHS
        # ====================================================================
        
        self.constraints.append(Constraint(
            name="total_matches",
            constraint_type=ConstraintType.GLOBAL,
            check_fn=self._check_total_matches,
            severity="hard",
            description="Le nombre total de matchs doit être correct"
        ))
        
        self.constraints.append(Constraint(
            name="matches_per_club",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_matches_per_club,
            severity="hard",
            description="Chaque club doit jouer exactement le nombre de matchs défini en config"
        ))
        
        self.constraints.append(Constraint(
            name="home_away_balance",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_home_away_balance,
            severity="hard",
            description="Chaque club doit jouer le bon nombre de matchs à domicile et à l'extérieur"
        ))
        
        # ====================================================================
        # CONTRAINTES SUR LES CHAPEAUX
        # ====================================================================
        
        self.constraints.append(Constraint(
            name="opponents_per_chapeau",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_opponents_per_chapeau,
            severity="hard",
            description="Chaque club doit affronter le bon nombre d'adversaires par chapeau"
        ))
        
        self.constraints.append(Constraint(
            name="chapeau_home_away_distribution",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_chapeau_home_away_distribution,
            severity="hard",
            description="Bonne distribution domicile/extérieur par chapeau"
        ))
        
        # ====================================================================
        # CONTRAINTES GÉOGRAPHIQUES
        # ====================================================================
        
        self.constraints.append(Constraint(
            name="no_same_country_opponents",
            constraint_type=ConstraintType.BINARY,
            check_fn=self._check_no_same_country_opponents,
            severity="hard",
            description="Pas d'affrontement entre clubs du même pays"
        ))
        
        # (NOUVELLE) Au plus 2 adversaires d'une même AUTRE association
        self.constraints.append(Constraint(
            name="max_two_from_same_foreign_country",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_max_two_from_same_foreign_country,
            severity="hard",
            description="Au plus deux adversaires provenant d'une même autre association"
        ))
        
        # ====================================================================
        # CONTRAINTES DE FAIRPLAY (SOFT)
        # ====================================================================
        
        self.constraints.append(Constraint(
            name="no_consecutive_matches",
            constraint_type=ConstraintType.UNARY,
            check_fn=self._check_no_consecutive_matches,
            severity="soft",
            description="Limite les matchs consécutifs domicile/extérieur"
        ))
    
    # ========================================================================
    # IMPLÉMENTATIONS DES CONTRAINTES
    # ========================================================================
    
    def _check_total_matches(self, draw: Draw) -> bool:
        """Vérifie le nombre total de matchs."""
        expected = config.get_expected_total_matches()
        return len(draw.matches) == expected
    
    def _check_matches_per_club(self, draw: Draw) -> bool:
        """Vérifie que chaque club joue le bon nombre de matchs (config.MATCHES_PER_CLUB)."""
        for club in draw.get_all_clubs():
            if draw.get_number_of_matches_for_club(club) != config.MATCHES_PER_CLUB:
                return False
        return True
    
    def _check_home_away_balance(self, draw: Draw) -> bool:
        """Vérifie la balance domicile/extérieur pour chaque club."""
        for club in draw.get_all_clubs():
            home = draw.get_number_of_home_matches_for_club(club)
            away = draw.get_number_of_away_matches_for_club(club)
            
            if home != config.HOME_MATCHES_PER_CLUB:
                return False
            if away != config.AWAY_MATCHES_PER_CLUB:
                return False
        
        return True
    
    def _check_opponents_per_chapeau(self, draw: Draw) -> bool:
        """Vérifie le nombre d'adversaires par chapeau pour chaque club."""
        for club in draw.get_all_clubs():
            opponents_by_chapeau = {}
            
            for opponent in draw.get_opponents_for_club(club):
                chapeau = opponent.chapeau.value
                opponents_by_chapeau[chapeau] = opponents_by_chapeau.get(chapeau, 0) + 1
            
            # Vérifie que la distribution correspond exactement à la config
            for chapeau, expected_count in config.OPPONENTS_PER_CHAPEAU.items():
                if opponents_by_chapeau.get(chapeau, 0) != expected_count:
                    return False
        
        return True
    
    def _check_chapeau_home_away_distribution(self, draw: Draw) -> bool:
        """Vérifie la distribution domicile/extérieur par chapeau pour chaque club."""
        for club in draw.get_all_clubs():
            for chapeau, (expected_home, expected_away) in config.DISTRIBUTION_CHAPEAUX.items():
                # Compte les matchs domicile vs ce chapeau
                home_count = sum(
                    1 for m in draw.get_home_matches_for_club(club)
                    if m.club_away.chapeau.value == chapeau
                )
                
                # Compte les matchs extérieur vs ce chapeau
                away_count = sum(
                    1 for m in draw.get_away_matches_for_club(club)
                    if m.club_home.chapeau.value == chapeau
                )
                
                if home_count != expected_home or away_count != expected_away:
                    return False
        
        return True
    
    def _check_no_same_country_opponents(self, draw: Draw) -> bool:
        """Vérifie qu'aucun club n'affronte un club de son pays."""
        max_allowed = config.MAX_SAME_COUNTRY_OPPONENTS
        
        for club in draw.get_all_clubs():
            clashes = draw.get_country_clashes_for_club(club)
            if len(clashes) > max_allowed:
                return False
        
        return True

    def _check_max_two_from_same_foreign_country(self, draw: Draw) -> bool:
        """Vérifie qu'un club n'affronte pas plus de deux clubs d'une même AUTRE association."""
        max_per_country = getattr(config, "MAX_OPPONENTS_PER_FOREIGN_COUNTRY", 2)
        
        for club in draw.get_all_clubs():
            counts = {}
            for opp in draw.get_opponents_for_club(club):
                if opp.pays == club.pays:
                    # Déjà couvert par _check_no_same_country_opponents (doit être 0)
                    continue
                counts[opp.pays] = counts.get(opp.pays, 0) + 1
                if counts[opp.pays] > max_per_country:
                    return False
        return True
    
    def _check_no_consecutive_matches(self, draw: Draw) -> bool:
        """Vérifie le fairplay (pas trop de matchs consécutifs domicile/extérieur)."""
        max_home = config.MAX_CONSECUTIVE_HOME_MATCHES
        max_away = config.MAX_CONSECUTIVE_AWAY_MATCHES
        
        for club in draw.get_all_clubs():
            matches = sorted(
                draw.get_matches_for_club(club),
                key=lambda m: m.journee
            )
            
            # Construit une séquence domicile/extérieur
            sequence = [
                'H' if m.club_home == club else 'A'
                for m in matches
            ]
            
            # Vérifie les séquences consécutives
            consecutive_home = 0
            consecutive_away = 0
            
            for venue in sequence:
                if venue == 'H':
                    consecutive_home += 1
                    consecutive_away = 0
                else:
                    consecutive_away += 1
                    consecutive_home = 0
                
                if consecutive_home > max_home or consecutive_away > max_away:
                    return False
        
        return True
    
    # ========================================================================
    # INTERFACE PUBLIQUE
    # ========================================================================
    
    def get_all_constraints(self) -> List[Constraint]:
        """Retourne toutes les contraintes."""
        return self.constraints
    
    def get_hard_constraints(self) -> List[Constraint]:
        """Retourne les contraintes obligatoires."""
        return [c for c in self.constraints if c.severity == "hard"]
    
    def get_soft_constraints(self) -> List[Constraint]:
        """Retourne les contraintes souples."""
        return [c for c in self.constraints if c.severity == "soft"]
    
    def verify_all_constraints(self, draw: Draw) -> Tuple[bool, List[str]]:
        """
        Vérifie toutes les contraintes sur un tirage.
        
        Returns:
            Tuple (tout_valide, liste_des_contraintes_violées)
        """
        violated = []
        
        for constraint in self.constraints:
            if not constraint.is_satisfied(draw):
                violated.append(constraint.name)
        
        return len(violated) == 0, violated
    
    def verify_hard_constraints(self, draw: Draw) -> Tuple[bool, List[str]]:
        """Vérifie uniquement les contraintes obligatoires."""
        violated = []
        
        for constraint in self.get_hard_constraints():
            if not constraint.is_satisfied(draw):
                violated.append(constraint.name)
        
        return len(violated) == 0, violated
    
    def get_constraint_details(self) -> List[dict]:
        """Retourne les détails de toutes les contraintes."""
        return [
            {
                "name": c.name,
                "type": c.constraint_type.value,
                "severity": c.severity,
                "description": c.description
            }
            for c in self.constraints
        ]
