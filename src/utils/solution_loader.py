from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Tuple

from src.models.club import Club
from src.models.match import Match
from src.models.draw import Draw
from src.utils.data_loader import DataLoader


class DrawImportError(Exception):
    """Erreur levée lors d'un problème d'import du tirage (format, données, clubs manquants)."""
    pass


class SolutionLoader:
    """
    Charge et valide un tirage (Draw) à partir d'un fichier JSON.

    Responsabilités :
    - Lire le JSON et valider le schéma minimal attendu
    - Charger / vérifier la base clubs (via DataLoader)
    - Mapper les IDs des clubs vers des objets Club
    - Construire les objets Match et retourner un Draw
    """

    @staticmethod
    def load_draw_from_file(
        filepath: Union[str, Path],
        clubs_or_path: Union[List[Club], str, Path]
    ) -> Draw:
        """
        Charge un tirage (Draw) depuis un fichier JSON.

        Args:
            filepath: Chemin vers le fichier JSON de tirage (contenant 'season' et 'matches')
            clubs_or_path: Soit une liste d'objets Club, soit un chemin vers le JSON des clubs

        Returns:
            Draw: objet tirage avec la saison et la liste des Match

        Raises:
            DrawImportError: si le fichier est introuvable, JSON invalide, schéma invalide,
                             club inconnu, ou match mal formé.
        """
        path = Path(filepath)
        if not path.exists():
            raise DrawImportError(f"Fichier tirage introuvable: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise DrawImportError(f"JSON invalide pour le tirage: {e}") from e

        season, matches_payload = SolutionLoader._validate_draw_schema(payload)
        clubs_list = SolutionLoader._ensure_clubs(clubs_or_path)
        club_by_id = SolutionLoader._build_club_index(clubs_list)

        matches: List[Match] = []
        for i, row in enumerate(matches_payload):
            try:
                h = str(row["club_home_id"]).strip()
                a = str(row["club_away_id"]).strip()
                d = int(row["journee"])
            except Exception as e:
                raise DrawImportError(f"Ligne {i}: champs manquants/invalides: {e}")

            if h not in club_by_id or a not in club_by_id:
                missing = [x for x in (h, a) if x not in club_by_id]
                raise DrawImportError(f"Ligne {i}: club(s) inconnu(s): {missing}")

            try:
                matches.append(
                    Match(club_home=club_by_id[h], club_away=club_by_id[a], journee=d)
                )
            except Exception as e:
                raise DrawImportError(
                    f"Ligne {i}: match invalide ({h} vs {a}, J{d}): {e}"
                )

        return Draw(matches=matches, season=season)

    @staticmethod
    def _ensure_clubs(clubs_or_path: Union[List[Club], str, Path]) -> List[Club]:
        """Accepte une liste de Club ou un chemin JSON et retourne une liste de Club."""
        if isinstance(clubs_or_path, list):
            if not clubs_or_path:
                raise DrawImportError("La liste de clubs fournie est vide.")
            return clubs_or_path

        p = Path(clubs_or_path)
        if not p.exists():
            raise DrawImportError(f"Fichier clubs introuvable: {p}")

        try:
            return DataLoader.load_clubs_from_file(str(p))
        except Exception as e:
            raise DrawImportError(f"Echec du chargement des clubs: {e}") from e

    @staticmethod
    def _build_club_index(clubs: List[Club]) -> Dict[str, Club]:
        """Construit un index {id -> Club} en détectant d'éventuels doublons d'ID."""
        idx: Dict[str, Club] = {}
        for c in clubs:
            if c.id in idx:
                raise DrawImportError(f"ID de club en doublon: {c.id}")
            idx[c.id] = c
        return idx

    @staticmethod
    def _validate_draw_schema(payload: Dict[str, Any]) -> Tuple[str, list]:
        """
        Valide le schéma minimal du JSON de tirage et retourne (season, matches).
        Attendu:
            {
              "season": "2025-26",
              "matches": [
                {"club_home_id": "PSG", "club_away_id": "RMA", "journee": 1},
                ...
              ]
            }
        """
        if not isinstance(payload, dict):
            raise DrawImportError("Le JSON du tirage doit être un objet (dictionnaire).")

        season = payload.get("season", "2025-26")
        matches = payload.get("matches")

        if not isinstance(matches, list) or len(matches) == 0:
            raise DrawImportError("Champ 'matches' manquant ou vide.")

        # Vérifie la présence des clés minimales sur au moins un match (structure-type)
        for k in ("club_home_id", "club_away_id", "journee"):
            if k not in matches[0]:
                raise DrawImportError(f"Champ manquant dans un match: '{k}'")

        return season, matches