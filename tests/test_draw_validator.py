
from src.utils.solution_loader import SolutionLoader
from src.utils.data_loader import DataLoader
from src.validators.draw_validator import DrawValidator

CLUBS_PATH = "data/clubs_2025_26.json"
DRAW_PATH = "data/draw_2025_26.json"

clubs = DataLoader.load_clubs_from_file(CLUBS_PATH)
print(f"[OK] Clubs chargés : {len(clubs)}")

draw = SolutionLoader.load_draw_from_file(DRAW_PATH, clubs)
print(f"[OK] Tirage chargé : {len(draw.matches)} matchs")

validator = DrawValidator()
ok, errors, warnings = validator.validate(draw)

print("\n--- Résultat du validateur ---")
print(f"Valide : {ok}")
if errors:
    print(f"    Erreurs ({len(errors)}) :")
    for e in errors:
        print("   -", e)
if warnings:
    print(f"    Avertissements ({len(warnings)}) :")
    for w in warnings:
        print("   -", w)

assert ok, "Le tirage ne passe pas la validation (voir erreurs ci-dessus)"
assert not errors, "Des erreurs ont été détectées lors de la validation"
print("\n[OK] Tirage validé avec succès")
