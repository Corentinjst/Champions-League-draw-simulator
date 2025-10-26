from src.utils.solution_loader import SolutionLoader
from src.utils.data_loader import DataLoader

CLUBS_PATH = "data/clubs_2025_26.json"
DRAW_PATH = "data/draw_2025_26.json"

clubs = DataLoader.load_clubs_from_file(CLUBS_PATH)
print(f"[OK] Clubs chargés: {len(clubs)}")

draw = SolutionLoader.load_draw_from_file(DRAW_PATH, CLUBS_PATH)
print(f"[OK] Saison: {draw.season}")
print(f"[OK] Nombre de matchs: {len(draw.matches)}")

print("\n--- Aperçu des 5 premiers matchs ---")
for m in draw.matches[:5]:
    print(f"J{m.journee}: {m.club_home.id} vs {m.club_away.id}")

assert isinstance(draw.matches, list) and len(draw.matches) > 0, "Aucun match importé"
sample = draw.matches[0]
assert hasattr(sample, "club_home") and hasattr(sample, "club_away") and hasattr(sample, "journee"), \
    "Structure Match incomplète"

print("\n[OK] Import du tirage: structure vérifiée")
