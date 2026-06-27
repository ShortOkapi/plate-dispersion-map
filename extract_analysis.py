import json
import pandas as pd

# 1. Carrega os dados que o teu update_map.py já gerou
print("A ler o ebt_dispersion_master_data.json...")
with open('ebt_dispersion_master_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

CORE_COUNTRIES = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Estonia", "Finland", 
    "France", "Germany", "Greece", "Ireland", "Italy", "Latvia", 
    "Lithuania", "Luxembourg", "Malta", "Netherlands", "Portugal", 
    "Slovakia", "Slovenia", "Spain", "Andorra", "Monaco", "San Marino", 
    "Vatican City", "Kosovo", "Montenegro", "Switzerland"
}

rows = []

# 2. Percorre todas as chapas de todas as denominações
for plate_id, plate_data in data["plates"].items():
    if "High" not in plate_data["confidence"]:
        continue  # Filtra só as chapas com confiança alta global

    valid_lqs = []
    
    # 3. Recria a lógica de fiabilidade (High) para o país
    for country, c_data in plate_data["countries"].items():
        if country in CORE_COUNTRIES:
            notes = c_data["notes"]
            baseline = c_data["baseline"]
            ratio = notes / baseline if baseline > 0 else 0
            
            is_high = notes >= 100 or (notes >= 20 and ratio >= 0.05)
            if is_high:
                valid_lqs.append((country, c_data["lq"]))

    if not valid_lqs:
        continue

    # 4. Ordena do maior LQ para o mais baixo
    valid_lqs.sort(key=lambda x: x[1], reverse=True)

    row = {
        "Denom": plate_data["denomination"],
        "Origin": plate_data["origin"].split(" - ")[0] if " - " in plate_data["origin"] else plate_data["origin"],
        "Plate": plate_data["plate"],
        "EBT_Notes": plate_data["total_ebt"]
    }

    # 5. Adiciona os LQ e os nomes dos países
    for i, (cntry, lq) in enumerate(valid_lqs):
        row[f"Cntry{i+1}"] = cntry
        row[f"LQ{i+1}"] = lq

    # 6. Calcula os quocientes (rácios) entre países vizinhos
    for i in range(1, len(valid_lqs)):
        prev_lq = valid_lqs[i-1][1]
        curr_lq = valid_lqs[i][1]
        ratio = prev_lq / curr_lq if curr_lq > 0 else 999
        row[f"r{i}"] = round(ratio, 3)

    rows.append(row)

# 7. Exporta para o CSV
df = pd.DataFrame(rows)
output_filename = "all_denominations_lq_analysis.csv"
df.to_csv(output_filename, index=False)
print(f"Sucesso! Dados extraídos para {output_filename}")
