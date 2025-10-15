from src.utils.data_loader import DataLoader

clubs = DataLoader.load_clubs_from_file("data/clubs_2025_26.json")
for club in clubs:
    print(club)

# Valider la liste
stats = DataLoader.validate_clubs_list(clubs)
print(stats)