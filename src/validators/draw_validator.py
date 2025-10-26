"""
Validateur de tirage (DrawValidator)

- Vérifie la cohérence structurelle du tirage (bornes de journées, unicité des paires,
  pas de self-match, total attendu, 1 match/jour/club, etc.)
- Vérifie les contraintes "hard" via UCLConstraints
- Signale les violations "soft" comme avertissements

Usage:
    validator = DrawValidator()
    ok, errors, warnings = validator.validate(draw)
"""
from __future__ import annotations

from typing import List, Tuple, Set, Dict

import src.config as config
from src.models.draw import Draw
from src.constraints.ucl_constraints import UCLConstraints


class DrawValidator:
    def __init__(self) -> None:
        self.constraints = UCLConstraints()

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def validate(self, draw: Draw) -> Tuple[bool, List[str], List[str]]:
        """Valide un tirage et retourne (ok, erreurs, avertissements)."""
        errors: List[str] = []
        warnings: List[str] = []

        # 1) Checks structurels internes
        errors += self._check_internal_consistency(draw)

        # 2) Contraintes "hard" officielles
        hard_ok, hard_violated = self.constraints.verify_hard_constraints(draw)
        if not hard_ok:
            errors.append(f"Hard constraints violated: {', '.join(hard_violated)}")

        # 3) Contraintes "soft" (préférences) => warnings
        soft_violated = [
            c.name for c in self.constraints.get_soft_constraints()
            if not c.is_satisfied(draw)
        ]
        if soft_violated:
            warnings.append(f"Soft constraints not satisfied: {', '.join(soft_violated)}")

        return len(errors) == 0, errors, warnings

    # ------------------------------------------------------------------
    # Structure interne
    # ------------------------------------------------------------------
    def _check_internal_consistency(self, draw: Draw) -> List[str]:
        errors: List[str] = []

        # a) Bornes de journée & self-matchs
        for m in draw.matches:
            if m.club_home.id == m.club_away.id:
                errors.append(f"Self-match interdit: club {m.club_home.id} à la J{m.journee}")
            if not (1 <= m.journee <= config.JOURNEES):
                errors.append(f"Journée hors bornes: {m.journee} (match {m.club_home.id}-{m.club_away.id})")

        # b) Total global de matchs
        expected_total = config.get_expected_total_matches()
        if len(draw.matches) != expected_total:
            errors.append(f"Total de matchs {len(draw.matches)} != attendu {expected_total}")

        # c) Un match par journée et par club, et pas plus d'une rencontre par paire
        #    + Comptages utiles réutilisés plus bas
        per_day_per_club: Dict[Tuple[int, int], int] = {}
        pair_days: Dict[Tuple[int, int], Set[int]] = {}
        home_count: Dict[int, int] = {}
        away_count: Dict[int, int] = {}

        for m in draw.matches:
            # compteur jour/club
            per_day_per_club[(m.club_home.id, m.journee)] = per_day_per_club.get((m.club_home.id, m.journee), 0) + 1
            per_day_per_club[(m.club_away.id, m.journee)] = per_day_per_club.get((m.club_away.id, m.journee), 0) + 1

            # compteur paires
            key = tuple(sorted((m.club_home.id, m.club_away.id)))
            pair_days.setdefault(key, set()).add(m.journee)

            # H/A par club
            home_count[m.club_home.id] = home_count.get(m.club_home.id, 0) + 1
            away_count[m.club_away.id] = away_count.get(m.club_away.id, 0) + 1

        # Par journée / club => exactement 1
        for club in draw.get_all_clubs():
            for d in range(1, config.JOURNEES + 1):
                if per_day_per_club.get((club.id, d), 0) != 1:
                    errors.append(
                        f"Club {club.id} a {per_day_per_club.get((club.id, d), 0)} match(s) à la J{d} (attendu: 1)"
                    )

        # Paires => au plus une rencontre
        for (a, b), days in pair_days.items():
            if len(days) > 1:
                errors.append(f"Paire jouée plusieurs fois: {a} vs {b} sur journées {sorted(list(days))}")

        # d) 4/4 H/A (ou valeurs du config)
        for club in draw.get_all_clubs():
            if home_count.get(club.id, 0) != config.HOME_MATCHES_PER_CLUB:
                errors.append(
                    f"Club {club.id}: {home_count.get(club.id, 0)} domicile != {config.HOME_MATCHES_PER_CLUB}"
                )
            if away_count.get(club.id, 0) != config.AWAY_MATCHES_PER_CLUB:
                errors.append(
                    f"Club {club.id}: {away_count.get(club.id, 0)} extérieur != {config.AWAY_MATCHES_PER_CLUB}"
                )

        return errors
