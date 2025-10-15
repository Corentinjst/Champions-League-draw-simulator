from dataclasses import dataclass
from enum import Enum
from typing import Optional
from .club import Club


class VenueType(Enum):
    """Énumération des types de lieu de match."""
    DOMICILE = "domicile"
    EXTERIEUR = "extérieur"


@dataclass(frozen=True)
class Match:
    """
    Représente un match entre deux clubs.
    
    Dans le format ligue (phase régulière de la nouvelle LDC), chaque club joue
    8 matchs: 4 à domicile et 4 en extérieur contre des adversaires de niveaux variés.
    
    Attributes:
        club_home: Club qui joue à domicile
        club_away: Club qui joue en extérieur
        journee: Numéro de la journée (1-8)
    """
    
    club_home: Club
    club_away: Club
    journee: int
    
    def __post_init__(self):
        """Valide les données du match."""
        if self.club_home == self.club_away:
            raise ValueError(
                f"Un club ne peut pas jouer contre lui-même: {self.club_home}"
            )
        
        if not isinstance(self.journee, int) or self.journee < 1 or self.journee > 8:
            raise ValueError(
                f"La journée doit être entre 1 et 8. Reçu: {self.journee}"
            )
    
    @property
    def vs_string(self) -> str:
        """Retourne une représentation textuelle du match."""
        return f"{self.club_home.id} vs {self.club_away.id}"
    
    @property
    def full_string(self) -> str:
        """Retourne une représentation textuelle complète du match."""
        return (
            f"[J{self.journee}] {self.club_home.nom} (domicile) vs "
            f"{self.club_away.nom} (extérieur)"
        )
    
    def implies_reverse_match(self) -> "Match":
        """
        Retourne le match retour (inversion domicile/extérieur).
        La journée reste la même (dans le nouveau format, un club affronte
        le même adversaire à la même journée en aller-retour virtuel).
        """
        return Match(
            club_home=self.club_away,
            club_away=self.club_home,
            journee=self.journee
        )
    
    def get_venue_for_club(self, club: Club) -> VenueType:
        """
        Retourne le type de venue pour un club donné.
        
        Args:
            club: Club pour lequel déterminer le lieu
        
        Returns:
            VenueType.DOMICILE si le club joue à domicile,
            VenueType.EXTERIEUR si le club joue en extérieur
        
        Raises:
            ValueError: Si le club ne participe pas au match
        """
        if club == self.club_home:
            return VenueType.DOMICILE
        elif club == self.club_away:
            return VenueType.EXTERIEUR
        else:
            raise ValueError(
                f"Le club {club.id} ne participe pas au match {self.vs_string}"
            )
    
    def involves_club(self, club: Club) -> bool:
        """Vérifie si un club participe au match."""
        return club == self.club_home or club == self.club_away
    
    def opponent_of(self, club: Club) -> Optional[Club]:
        """
        Retourne l'adversaire d'un club dans ce match.
        
        Args:
            club: Club pour lequel trouver l'adversaire
        
        Returns:
            Club adversaire ou None si le club ne joue pas
        """
        if club == self.club_home:
            return self.club_away
        elif club == self.club_away:
            return self.club_home
        return None
    
    def __hash__(self):
        """Permet d'utiliser Match en tant que clé de dictionnaire."""
        # Utilise un frozenset pour que (A vs B) et (B vs A) soient différents
        return hash((self.club_home.id, self.club_away.id, self.journee))
    
    def __eq__(self, other):
        """Compare deux matchs."""
        if not isinstance(other, Match):
            return NotImplemented
        return (
            self.club_home == other.club_home
            and self.club_away == other.club_away
            and self.journee == other.journee
        )
    
    def __repr__(self):
        """Représentation textuelle du match."""
        return f"Match({self.vs_string}, J{self.journee})"
    
    def __str__(self):
        """Chaîne de caractères lisible."""
        return self.full_string