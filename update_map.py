import pandas as pd
import numpy as np
import io
import json
import requests
from bs4 import BeautifulSoup
import re
from collections import defaultdict
from datetime import datetime, timezone

VERSION = "1.1.0"
print(f"=== STARTING EBT MAP AUTO-UPDATE v{VERSION} ===")

# ==========================================
# 1. PARSE GUY SOHIER CATALOG (WEB SCRAPING)
# ==========================================
print("Step 1: Fetching Guy Sohier's catalog...")

url_sohier = "http://liste.eurobillets.free.fr/index_fichiers/sheet001.htm"
headers = {'User-Agent': 'Mozilla/5.0'}
r_sohier = requests.get(url_sohier, headers=headers)
r_sohier.encoding = 'windows-1252' # Excel standard encoding
soup = BeautifulSoup(r_sohier.text, 'html.parser')

def parse_qty(qty_str):
    qty_str = str(qty_str).replace('?', '').strip()
    if qty_str in ['_', '', 'infime'] or 'feuilles' in qty_str.lower() or 'unknown' in qty_str.lower() or 'testnote' in qty_str.lower():
        return 0.0
    if 'mio' in qty_str.lower():
        num_str = qty_str.lower().replace('mio', '').replace(' ', '').replace(',', '.')
        try: return float(num_str)
        except ValueError: return 0.0
    if 'billets' in qty_str.lower():
        num_str = re.sub(r'[^\d,]', '', qty_str).replace(',', '.')
        try: return float(num_str) / 1000000.0
        except ValueError: return 0.0
    num_str = qty_str.replace(' ', '').replace(',', '.')
    try: return float(num_str)
    except ValueError: return 0.0

whitelist = defaultdict(float)
current_denomination = 0
processed_lines = 0

for row in soup.find_all('tr'):
    cols = [td.get_text(separator=" ", strip=True) for td in row.find_all(['td', 'th'])]
    
    if len(cols) > 0:
        denom_str = cols[0].strip()
        if denom_str in ['5', '10', '20', '50', '100', '200', '500']:
            current_denomination = int(denom_str)
            
    if len(cols) > 4:
        mnemo = cols[1].strip() if len(cols) > 1 else ""
        if not mnemo: continue
        
        plate_text = cols[4].strip()
        plates = re.findall(r'\b[A-Z]\d{3}\b', plate_text)
        
        if plates:
            qty = 0.0
            if len(cols) > 8:
                qty = parse_qty(cols[8])
            if current_denomination > 0:
                for plate in plates:
                    whitelist[(current_denomination, plate)] += qty
                    processed_lines += 1

# Build Whitelist DataFrame
wl_data = []
for (denom, plate), qty in whitelist.items():
    wl_data.append({'denomination': denom, 'shortcode_detailed': plate, 'Print_Run_Millions': round(qty, 3)})
wl = pd.DataFrame(wl_data)

print(f"  > Successfully extracted {len(wl)} valid plates.")

# ==========================================
# 2. FETCH EBT DATA DUMP (COUNTRIES)
# ==========================================
print("Step 2: Fetching EBT raw data dump (Countries)...")
url_ebt = "https://www.eurobilltracker.com/tmp/denomination_serial_detailedshortcode_country.txt"
r_ebt = requests.get(url_ebt, headers=headers)
r_ebt.encoding = 'utf-8'

lines = [line for line in r_ebt.text.split('\n') if '|' in line]
ebt_df = pd.read_csv(io.StringIO('\n'.join(lines)), sep='|', skipinitialspace=True)
ebt_df.columns = ebt_df.columns.str.strip()
ebt_df = ebt_df.dropna(axis=1, how='all')
ebt_df = ebt_df[ebt_df['year'].astype(str).str.strip() != 'year']

ebt_df['year'] = pd.to_numeric(ebt_df['year'], errors='coerce')
ebt_df['denomination'] = pd.to_numeric(ebt_df['denomination'], errors='coerce')
ebt_df['count'] = pd.to_numeric(ebt_df['count'], errors='coerce')
ebt_df['country'] = ebt_df['country'].str.strip()
ebt_df['country'] = ebt_df['country'].replace({'Bosnia and Herz.': 'Bosnia and Herzegovina'})
ebt_df['shortcode_detailed'] = ebt_df['shortcode_detailed'].astype(str).str.strip().str[:4]
ebt_df = ebt_df.dropna(subset=['year', 'denomination', 'count'])

europa_df = ebt_df[ebt_df['year'] > 2002].copy()
valid_europa_df = pd.merge(europa_df, wl, on=['denomination', 'shortcode_detailed'], how='inner')

# ==========================================
# 2.5. FETCH EBT GLOBAL TOTALS (INCLUDES < 10 NOTES)
# ==========================================
print("Step 2.5: Fetching EBT global totals (including rare notes)...")
url_totals = "https://www.eurobilltracker.com/tmp/denomination_serial_detailedshortcode.txt"
r_totals = requests.get(url_totals, headers=headers)
r_totals.encoding = 'utf-8'

lines_totals = [line for line in r_totals.text.split('\n') if '|' in line]
totals_df = pd.read_csv(io.StringIO('\n'.join(lines_totals)), sep='|', skipinitialspace=True)
totals_df.columns = totals_df.columns.str.strip()
totals_df = totals_df.dropna(axis=1, how='all')
totals_df = totals_df[totals_df['year'].astype(str).str.strip() != 'year']

totals_df['year'] = pd.to_numeric(totals_df['year'], errors='coerce')
totals_df['denomination'] = pd.to_numeric(totals_df['denomination'], errors='coerce')
totals_df['count'] = pd.to_numeric(totals_df['count'], errors='coerce')
totals_df['shortcode_detailed'] = totals_df['shortcode_detailed'].astype(str).str.strip().str[:4]
totals_df = totals_df.dropna(subset=['year', 'denomination', 'count'])

europa_totals_df = totals_df[totals_df['year'] > 2002].copy()

# Calculate TRUE global totals from the uncensored list
real_plate_totals = europa_totals_df.groupby(['denomination', 'shortcode_detailed'])['count'].sum().reset_index()
real_plate_totals.rename(columns={'count': 'plate_global_total'}, inplace=True)

real_denom_totals = europa_totals_df.groupby('denomination')['count'].sum().reset_index()
real_denom_totals.rename(columns={'count': 'denom_global_total'}, inplace=True)

# ==========================================
# 3. CALCULATE LQs & CONFIDENCE
# ==========================================
print("Step 3: Calculating LQs and Confidence Algorithms...")
printers = {
    'E': {"name": "E - Oberthur (France)", "country": "France", "lon": -1.62223, "lat": 48.09598},
    'F': {"name": "F - Oberthur (Bulgaria)", "country": "Bulgaria", "lon": 23.38734, "lat": 42.66009},
    'M': {"name": "M - Valora (Portugal)", "country": "Portugal", "lon": -8.97792, "lat": 39.03514},
    'N': {"name": "N - OeBS (Austria)", "country": "Austria", "lon": 16.35710, "lat": 48.21710},
    'P': {"name": "P - Joh. Enschedé (Netherlands)", "country": "Netherlands", "lon": 4.66570, "lat": 52.38424},
    'R': {"name": "R - Bundesdruckerei (Germany)", "country": "Germany", "lon": 13.40095, "lat": 52.50783},
    'S': {"name": "S - Banca d'Italia (Italy)", "country": "Italy", "lon": 12.53644, "lat": 41.87130},
    'T': {"name": "T - Central Bank (Ireland)", "country": "Ireland", "lon": -6.23190, "lat": 53.27350},
    'U': {"name": "U - Banque de France", "country": "France", "lon": 3.07290, "lat": 45.77480},
    'V': {"name": "V - IMBISA (Spain)", "country": "Spain", "lon": -3.61894, "lat": 40.40927},
    'W': {"name": "W - G&D Leipzig (Germany)", "country": "Germany", "lon": 12.38355, "lat": 51.33704},
    'X': {"name": "X - G&D Munich (Germany)", "country": "Germany", "lon": 11.62249, "lat": 48.13881},
    'Y': {"name": "Y - Bank of Greece", "country": "Greece", "lon": 23.80440, "lat": 38.01063},
    'Z': {"name": "Z - NBB (Belgium)", "country": "Belgium", "lon": 4.36017, "lat": 50.85019}
}

# Injecting the REAL global totals into the algorithm
denom_totals = real_denom_totals

baseline_df = valid_europa_df.groupby(['denomination', 'country'])['count'].sum().reset_index()
baseline_df.rename(columns={'count': 'baseline_total_notes'}, inplace=True)
baseline_df = pd.merge(baseline_df, denom_totals, on='denomination')
baseline_df['baseline_pct'] = baseline_df['baseline_total_notes'] / baseline_df['denom_global_total']

plate_country_df = valid_europa_df.groupby(['denomination', 'shortcode_detailed', 'country'])['count'].sum().reset_index()
plate_country_df.rename(columns={'count': 'plate_notes_in_country'}, inplace=True)

# Injecting the REAL plate totals into the algorithm
plate_totals = real_plate_totals

plate_analysis = pd.merge(plate_country_df, plate_totals, on=['denomination', 'shortcode_detailed'], how='inner')
plate_analysis['plate_pct'] = plate_analysis['plate_notes_in_country'] / plate_analysis['plate_global_total']

results_df = pd.merge(plate_analysis, baseline_df, on=['denomination', 'country'])
results_df['location_quotient'] = results_df['plate_pct'] / results_df['baseline_pct']

denom_print_runs = wl.groupby('denomination')['Print_Run_Millions'].sum().to_dict()
denom_ebt_totals = denom_totals.set_index('denomination')['denom_global_total'].to_dict()
avg_capture_rate = {d: (denom_ebt_totals[d] / pr if pr > 0 else 500) for d, pr in denom_print_runs.items()}

# ==========================================
# 4. EXPORT TO JSON
# ==========================================
print("Step 4: Writing the JSON map database...")

# Injeta a versão e a data de atualização nos metadados
master_data = {
    "metadata": {
        "last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        "version": VERSION
    },
    "plates": {}, 
    "hierarchy": {}
}

for denom in results_df['denomination'].unique(): master_data["hierarchy"][str(denom)] = {}

grouped_plates = results_df.groupby(['denomination', 'shortcode_detailed'])

for name, group in grouped_plates:
    denom, plate = int(name[0]), name[1]
    printer_letter = plate[0]
    p_info = printers.get(printer_letter, {"name": f"{printer_letter} - Unknown", "country": "", "lon": None, "lat": None})
    
    if p_info["name"] not in master_data["hierarchy"][str(denom)]:
        master_data["hierarchy"][str(denom)][p_info["name"]] = []
    master_data["hierarchy"][str(denom)][p_info["name"]].append(plate)
    
    wl_row = wl[(wl['denomination'] == denom) & (wl['shortcode_detailed'] == plate)]
    print_run = float(wl_row['Print_Run_Millions'].sum()) if not wl_row.empty else 0.0
    total_ebt = int(group['plate_global_total'].iloc[0])
    
    if print_run > 0:
        print_run_str = f"{round(print_run, 3)}M notes"
        capture_rate = total_ebt / print_run 
        avg_rate = avg_capture_rate.get(denom, 500)
        
        if capture_rate > (avg_rate * 10.0): confidence = "Low (Anomalous Data)"
        elif capture_rate > (avg_rate * 0.4): confidence = "High"
        elif capture_rate > (avg_rate * 0.1): confidence = "Medium"
        else: confidence = "Low"
    else:
        print_run_str = "Unknown"
        confidence = "Undetermined"
        
    lq_std = group['location_quotient'].std()
    threshold_notes = max(total_ebt * 0.01, 20) 
    valid_dest = group[(group['plate_notes_in_country'] >= threshold_notes) & (group['baseline_total_notes'] >= 10000)]
    if valid_dest.empty: valid_dest = group[group['plate_notes_in_country'] >= 20]
    if valid_dest.empty: valid_dest = group
    
    max_country = valid_dest.loc[valid_dest['location_quotient'].idxmax(), 'country'] if not valid_dest.empty else ""

    if pd.isna(lq_std) or lq_std < 0.7: dispersion = "Pandemic (Uniformly spread)"
    elif lq_std > 1.0 and max_country == p_info["country"]: dispersion = "Endemic (Local retention)"
    elif lq_std > 1.0: dispersion = f"Emigrant (Exported to {max_country})"
    else: dispersion = "Mixed Pattern"

    countries_data = {row['country']: {"lq": round(row['location_quotient'], 2), "notes": int(row['plate_notes_in_country']), "baseline": int(row['baseline_total_notes'])} for _, row in group.iterrows()}
    
    master_data["plates"][f"{denom}_{plate}"] = {
        "denomination": denom, "plate": plate, "origin": p_info["name"],
        "origin_coords": {"lon": p_info["lon"], "lat": p_info["lat"]},
        "print_run": print_run_str, "total_ebt": total_ebt, "confidence": confidence,
        "dispersion": dispersion, "countries": countries_data
    }

with open('ebt_dispersion_master_data.json', 'w', encoding='utf-8') as f:
    json.dump(master_data, f, ensure_ascii=False, indent=2)

print("SUCCESS! JSON File generated and saved.")
