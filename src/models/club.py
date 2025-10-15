from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Chapeau(Enum):
    """Énumération des chapeaux de la Ligue des Champions."""
    CHAPEAU_1 = 1
    CHAPEAU_2 = 2
    CHAPEAU_3 = 3
    CHAPEAU_4 = 4

    @classmethod
    def from_int(cls, value: int) -> "Chapeau":
        """Crée un Chapeau à partir d'un entier."""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"Chapeau invalide: {value}. Doit être entre 1 et 4.")


@dataclass(frozen=True)
class Club:
    """
    Représente un club de la Ligue des Champions.
    
    Attributes:
        id: Identifiant unique du club (ex: "PSG", "RMA")
        nom: Nom complet du club
        pays: Code ISO 3 du pays (ex: "FRA", "ESP", "ENG")
        chapeau: Chapeau du club (1, 2, 3 ou 4)
    """
    
    id: str
    nom: str
    pays: str
    chapeau: Chapeau
    
    def __post_init__(self):
        """Valide les données du club."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("L'ID du club doit être une chaîne non vide.")
        
        if not self.nom or not isinstance(self.nom, str):
            raise ValueError("Le nom du club doit être une chaîne non vide.")
        
        if len(self.pays) != 3 or not self.pays.isupper():
            raise ValueError(
                f"Le code pays doit être un code ISO 3 (ex: 'FRA'). "
                f"Reçu: {self.pays}"
            )
    
    def __hash__(self):
        """Permet d'utiliser Club en tant que clé de dictionnaire ou dans des sets."""
        return hash(self.id)
    
    def __eq__(self, other):
        """Compare deux clubs par leur ID."""
        if not isinstance(other, Club):
            return NotImplemented
        return self.id == other.id
    
    def __repr__(self):
        """Représentation textuelle du club."""
        return f"Club({self.id}, {self.nom}, {self.pays}, chapeau={self.chapeau.value})"
    
    def __str__(self):
        """Chaîne de caractères lisible."""
        return f"{self.nom} ({self.id})"