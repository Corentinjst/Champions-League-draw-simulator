import json
from pathlib import Path
from typing import List, Dict, Any
from ..models.club import Club, Chapeau


class DataLoader:
    """
    Charge et valide les données des clubs à partir de fichiers JSON.
    
    Prend en charge la validation du format, la gestion des erreurs,
    et la transformation des données JSON en objets Club.
    """
    
    @staticmethod
    def load_clubs_from_file(filepath: str) -> List[Club]:
        """
        Charge une liste de clubs à partir d'un fichier JSON.
        
        Args:
            filepath: Chemin vers le fichier JSON contenant les clubs
        
        Returns:
            Liste d'objets Club
        
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            json.JSONDecodeError: Si le fichier JSON est invalide
            ValueError: Si les données des clubs sont invalides
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Fichier introuvable: {filepath}")
        
        if not filepath.suffix.lower() == ".json":
            raise ValueError(f"Le fichier doit être un JSON. Reçu: {filepath.suffix}")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Erreur lors de la lecture du JSON: {e.msg}",
                e.doc,
                e.pos
            )
        
        # Gère à la fois une liste directe et un dictionnaire avec clé "clubs"
        if isinstance(data, dict):
            if "clubs" in data:
                clubs_data = data["clubs"]
            else:
                raise ValueError(
                    "Si les données sont un dictionnaire, "
                    "elles doivent contenir une clé 'clubs'"
                )
        elif isinstance(data, list):
            clubs_data = data
        else:
            raise ValueError(
                "Les données JSON doivent être une liste ou un dictionnaire. "
                f"Reçu: {type(data)}"
            )
        
        if not clubs_data:
            raise ValueError("Aucun club trouvé dans le fichier JSON.")
        
        clubs = []
        for idx, club_data in enumerate(clubs_data):
            try:
                club = DataLoader._parse_club(club_data)
                clubs.append(club)
            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(
                    f"Erreur lors du parsing du club à l'index {idx}: {str(e)}"
                )
        
        return clubs
    
    @staticmethod
    def _parse_club(club_data: Dict[str, Any]) -> Club:
        """
        Parse un dictionnaire de données en objet Club.
        
        Args:
            club_data: Dictionnaire contenant les données du club
        
        Returns:
            Objet Club
        
        Raises:
            KeyError: Si une clé requise est manquante
            ValueError: Si les données sont invalides
        """
        required_fields = {"id", "nom", "pays", "chapeau"}
        missing_fields = required_fields - set(club_data.keys())
        
        if missing_fields:
            raise KeyError(
                f"Champs manquants: {', '.join(missing_fields)}"
            )
        
        club_id = club_data["id"].strip()
        nom = club_data["nom"].strip()
        pays = club_data["pays"].strip().upper()
        chapeau_value = club_data["chapeau"]
        
        # Valide et convertit la valeur du chapeau
        if not isinstance(chapeau_value, int):
            try:
                chapeau_value = int(chapeau_value)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Le chapeau doit être un entier. Reçu: {chapeau_value}"
                )
        
        chapeau = Chapeau.from_int(chapeau_value)
        
        return Club(id=club_id, nom=nom, pays=pays, chapeau=chapeau)
    
    @staticmethod
    def save_clubs_to_file(clubs: List[Club], filepath: str) -> None:
        """
        Sauvegarde une liste de clubs dans un fichier JSON.
        
        Args:
            clubs: Liste d'objets Club
            filepath: Chemin où sauvegarder le fichier JSON
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        clubs_data = [
            {
                "id": club.id,
                "nom": club.nom,
                "pays": club.pays,
                "chapeau": club.chapeau.value
            }
            for club in clubs
        ]
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(clubs_data, f, indent=4, ensure_ascii=False)
    
    @staticmethod
    def validate_clubs_list(clubs: List[Club]) -> Dict[str, Any]:
        """
        Valide une liste de clubs et retourne des statistiques.
        
        Args:
            clubs: Liste d'objets Club
        
        Returns:
            Dictionnaire contenant les statistiques de validation
        """
        if not clubs:
            return {"valide": False, "erreur": "La liste de clubs est vide"}
        
        # Vérifie les IDs uniques
        ids = [club.id for club in clubs]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in set(ids) if ids.count(id) > 1]
            return {
                "valide": False,
                "erreur": f"IDs en doublon: {duplicates}"
            }
        
        # Vérifie la distribution par chapeau
        chapeaux_count = {}
        for club in clubs:
            chapeau_num = club.chapeau.value
            chapeaux_count[chapeau_num] = chapeaux_count.get(chapeau_num, 0) + 1
        
        # Vérifie qu'il y a des clubs dans chaque chapeau
        expected_chapeaux = {1, 2, 3, 4}
        missing_chapeaux = expected_chapeaux - set(chapeaux_count.keys())
        
        return {
            "valide": True,
            "nombre_clubs": len(clubs),
            "distribution_chapeaux": chapeaux_count,
            "pays_uniques": len(set(club.pays for club in clubs)),
            "avertissement": (
                f"Chapeaux manquants: {missing_chapeaux}"
                if missing_chapeaux else None
            )
        }