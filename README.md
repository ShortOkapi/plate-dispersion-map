# 🌍 plate-dispersion-map
Euro banknotes - Europa plates - Dispersion Map per combo denomination+plate

An interactive, auto-updating dashboard to explore the real geographic dispersion of Euro banknotes (Europa Series). 

Access the live dashboard here: **[Plates Dispersion Map](https://shortokapi.github.io/plate-dispersion-map)**

---

## 🔬 Methodology: How it Works (Countering the EBT Bias)

If we simply count the raw number of notes registered on EuroBillTracker (EBT) per country, the resulting map wouldn't show where the notes traveled; it would simply show **where the most active users live**. Countries with massive, highly active communities (like Austria, Germany, or the Netherlands) would completely overshadow the rest of Europe.

To solve this and reveal the **true organic migration** of the banknotes, this tool uses a statistical measure called the **Location Quotient (LQ)**.

### 1. The Location Quotient (LQ)
The algorithm calculates two percentages for every country:
*   **The Baseline:** What percentage of *ALL* Euro notes of a specific denomination (e.g., 20€) were found in Country X? (This measures the tracking power of the local community).
*   **The Plate Share:** What percentage of *THIS SPECIFIC PLATE* (e.g., 20€ U002) was found in Country X?

**LQ = Plate Share / Baseline**

*   **LQ ≈ 1.0 (Normal):** The note is found exactly as often as expected given the local community size.
*   **LQ > 2.0 (Over-represented):** The note is statistically concentrated here (e.g., local distribution).
*   **LQ < 0.5 (Under-represented):** The note is rare in this region compared to others.

### 2. The 10x Anomaly Detector (Data Confidence)
The tool also cross-references EBT captures with the official print run estimates from Guy Sohier's catalog. It calculates an average "Capture Rate" (e.g., EBT captures 4,000 notes for every 1 Million printed).

If a specific plate is being captured at a rate **10 times higher** than the European average, it triggers the **"Low (Anomalous Data)"** flag. This likely means one of three things:
1.  **The "Fake-Tracker" Effect:** Some "overzealous" users hallucinated their own registers of some rare plates, in order to have them in their virtual collection.
2.  **The "Super-Tracker" Effect:** A local user intercepted sequential, uncirculated bundles directly from the printer/bank and registered thousands of notes before they could disperse organically.
3.  **Catalog Error:** The official print run estimate for that plate is significantly underestimated in the catalog.

### 3. Dispersion Patterns
Based on the Standard Deviation of the LQ across all countries, the system classifies the note's behavior:
*   **Endemic:** Heavily retained in its country of origin.
*   **Emigrant:** Heavily exported and concentrated in a foreign country.
*   **Pandemic:** Uniformly spread across the entire continent.

### 💡 The "Visual Paradox" (Text vs. Map Colors)
When exploring the map, you might encounter situations that look contradictory. For example, looking at the **200€ E005** plate:
* The dashboard text declares it as **"Emigrant (Exported to Germany)"**.
* Yet, on the map, **Germany is colored light orange** (LQ 0.90), while France is colored dark brown (LQ 1.56).

**Why does the system say it was exported to a lighter-colored country?**
This is a feature, not a bug! The system calculates two different things:
1. **The Map Colors (Micro-Density):** This shows pure Location Quotient. France has a high LQ because it has very few 200€ notes registered overall (only 1,794). Finding 97 E005 notes there is a huge statistical spike (~5.4% of their pool), making it dark brown.
2. **The Text Label (Macro-Migration):** To declare that a plate was "Exported" to a specific country, the algorithm uses a **Confidence Volume Filter**. A country must have a massive baseline of notes (>10,000) and hold at least 1% of the plate's entire European volume. 

France's 97 notes are a statistical curiosity, but they don't represent a macro-economic migration. Germany (with 2,124 notes) passes the volume filter and stands as the true macro-destination for this plate's print run, even if it represents a smaller drop in their massive ocean of registered notes.

---

## 🤝 Credits & Acknowledgements

* *Data Sources: EuroBillTracker (weekly public dump) and [Guy Sohier's Catalog](http://liste.eurobillets.free.fr).*
* **Idea, Conceptualization, and Project Management:** Miguel Viterbo (*lmviterbo* @ EuroBillTracker, *ShortOkapi* @ Banknotesworld)
* **Math Solutions, Algorithms, and Code:** Gemini 3.1 Pro
