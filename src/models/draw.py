from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from .club import Club
from .match import Match


@dataclass
class Draw:
    """
    Représente le résultat complet du tirage de la phase ligue.
    
    Structure les 8 journées de matchs pour tous les clubs participants.
    Permet de valider et analyser l'intégrité du tirage.
    
    Attributes:
        matches: Liste de tous les matchs du tirage
        season: Saison (ex: "2025-26")
    """
    
    matches: List[Match] = field(default_factory=list)
    season: str = "2025-26"
    
    def __post_init__(self):
        """Valide la structure du tirage après création."""
        if self.matches is None:
            object.__setattr__(self, 'matches', [])
    
    def add_match(self, match: Match) -> None:
        """
        Ajoute un match au tirage.
        
        Args:
            match: Match à ajouter
        
        Raises:
            ValueError: Si le match est en doublon ou crée un conflit
        """
        if match in self.matches:
            raise ValueError(f"Le match {match} est déjà présent")
        
        self.matches.append(match)
    
    def add_matches(self, matches: List[Match]) -> None:
        """Ajoute plusieurs matchs au tirage."""
        for match in matches:
            self.add_match(match)
    
    def get_matches_for_club(self, club: Club) -> List[Match]:
        """
        Récupère tous les matchs d'un club.
        
        Args:
            club: Club pour lequel récupérer les matchs
        
        Returns:
            Liste des matchs impliquant le club
        """
        return [m for m in self.matches if m.involves_club(club)]
    
    def get_home_matches_for_club(self, club: Club) -> List[Match]:
        """Récupère tous les matchs à domicile d'un club."""
        return [m for m in self.matches if m.club_home == club]
    
    def get_away_matches_for_club(self, club: Club) -> List[Match]:
        """Récupère tous les matchs en extérieur d'un club."""
        return [m for m in self.matches if m.club_away == club]
    
    def get_opponents_for_club(self, club: Club) -> List[Club]:
        """
        Récupère tous les adversaires d'un club.
        
        Returns:
            Liste des clubs adversaires (pas de doublons)
        """
        opponents = set()
        for match in self.get_matches_for_club(club):
            opponent = match.opponent_of(club)
            if opponent:
                opponents.add(opponent)
        return sorted(list(opponents), key=lambda c: c.id)
    
    def get_matches_by_journee(self, journee: int) -> List[Match]:
        """Récupère tous les matchs d'une journée donnée."""
        if not (1 <= journee <= 8):
            raise ValueError(f"La journée doit être entre 1 et 8. Reçu: {journee}")
        return [m for m in self.matches if m.journee == journee]
    
    def get_number_of_matches_for_club(self, club: Club) -> int:
        """Retourne le nombre de matchs d'un club."""
        return len(self.get_matches_for_club(club))
    
    def get_number_of_home_matches_for_club(self, club: Club) -> int:
        """Retourne le nombre de matchs à domicile d'un club."""
        return len(self.get_home_matches_for_club(club))
    
    def get_number_of_away_matches_for_club(self, club: Club) -> int:
        """Retourne le nombre de matchs en extérieur d'un club."""
        return len(self.get_away_matches_for_club(club))
    
    def get_all_clubs(self) -> Set[Club]:
        """Récupère tous les clubs du tirage."""
        clubs = set()
        for match in self.matches:
            clubs.add(match.club_home)
            clubs.add(match.club_away)
        return clubs
    
    def get_clubs_by_country(self) -> Dict[str, List[Club]]:
        """Retourne les clubs groupés par pays."""
        clubs_by_country = defaultdict(list)
        for club in self.get_all_clubs():
            clubs_by_country[club.pays].append(club)
        return dict(clubs_by_country)
    
    def get_clubs_by_chapeau(self) -> Dict[int, List[Club]]:
        """Retourne les clubs groupés par chapeau."""
        clubs_by_chapeau = defaultdict(list)
        for club in self.get_all_clubs():
            clubs_by_chapeau[club.chapeau.value].append(club)
        return dict(sorted(clubs_by_chapeau.items()))
    
    def get_country_clashes_for_club(self, club: Club) -> List[Tuple[Club, int]]:
        """
        Récupère les affrontements entre clubs du même pays pour un club donné.
        
        Returns:
            Liste de tuples (adversaire, nombre_de_matchs)
        """
        opponents = self.get_opponents_for_club(club)
        clashes = []
        for opponent in opponents:
            if opponent.pays == club.pays:
                clashes.append((opponent, len([
                    m for m in self.matches
                    if (m.involves_club(club) and m.opponent_of(club) == opponent)
                ])))
        return clashes
    
    def has_country_clash(self, club1: Club, club2: Club) -> bool:
        """Vérifie s'il y a un affrontement entre deux clubs du même pays."""
        if club1.pays != club2.pays:
            return False
        opponents = self.get_opponents_for_club(club1)
        return club2 in opponents
    
    def get_statistics(self) -> Dict:
        """
        Retourne des statistiques complètes sur le tirage.
        
        Returns:
            Dictionnaire contenant diverses statistiques
        """
        all_clubs = self.get_all_clubs()
        
        stats = {
            "season": self.season,
            "nombre_clubs": len(all_clubs),
            "nombre_matchs": len(self.matches),
            "distribution_par_chapeau": self.get_clubs_by_chapeau(),
            "distribution_par_pays": {
                pays: len(clubs) 
                for pays, clubs in self.get_clubs_by_country().items()
            },
            "matchs_par_journee": {
                j: len(self.get_matches_by_journee(j)) for j in range(1, 9)
            },
            "clubs": {}
        }
        
        for club in sorted(all_clubs, key=lambda c: c.id):
            stats["clubs"][club.id] = {
                "nom": club.nom,
                "pays": club.pays,
                "chapeau": club.chapeau.value,
                "matchs_total": self.get_number_of_matches_for_club(club),
                "matchs_domicile": self.get_number_of_home_matches_for_club(club),
                "matchs_exterieur": self.get_number_of_away_matches_for_club(club),
                "adversaires": [c.id for c in self.get_opponents_for_club(club)],
                "affrontements_pays": [
                    {"adversaire": c.id, "nombre_matchs": nb}
                    for c, nb in self.get_country_clashes_for_club(club)
                ]
            }
        
        return stats
    
    def to_dict(self) -> Dict:
        """Convertit le tirage en dictionnaire."""
        return {
            "season": self.season,
            "matches": [
                {
                    "club_home_id": m.club_home.id,
                    "club_away_id": m.club_away.id,
                    "journee": m.journee
                }
                for m in self.matches
            ]
        }
    
    def __repr__(self):
        """Représentation textuelle du tirage."""
        clubs = len(self.get_all_clubs())
        matches = len(self.matches)
        return f"Draw(season={self.season}, clubs={clubs}, matches={matches})"
    
    def __str__(self):
        """Chaîne de caractères lisible."""
        lines = [f"Tirage - Saison {self.season}"]
        lines.append(f"Clubs: {len(self.get_all_clubs())}")
        lines.append(f"Matchs: {len(self.matches)}")
        lines.append("\nMatchs par journée:")
        
        for j in range(1, 9):
            matches_j = self.get_matches_by_journee(j)
            lines.append(f"  Journée {j}: {len(matches_j)} matchs")
        
        return "\n".join(lines)