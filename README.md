# 🌍 plate-dispersion-map
Euro banknotes - Europa plates - Dispersion Map per combo denomination+plate

An interactive, auto-updating dashboard to explore the real geographic dispersion of Euro banknotes (Europa Series). 

Access the live dashboard here: **[Plate Dispersion Map](https://shortokapi.github.io/plate-dispersion-map)**

---

## 📖 Methodology: How it Works (The v2.0 Analytical Engine)

Creating an accurate map of Euro banknote dispersion presents a massive statistical challenge: **The EBT Bias**. 

Because the EuroBillTracker community is highly active in specific countries (like Germany, Finland, Austria, and the Netherlands) and less active in others, looking purely at the raw number of notes found is misleading. A plate with 500 hits in Germany and 500 hits in Portugal wasn't distributed equally—Portugal's baseline of users is much smaller, meaning finding 500 notes there represents a massive, anomalous concentration.

To counter this bias and reveal the true journey of the banknotes, this project uses a custom **v2.0 Analytical Engine** built on three statistical pillars: Location Quotient, Data Segregation, and Dynamic Clustering.

### 1. The Core Metric: Location Quotient (LQ)
Instead of raw counts, the map calculates the **Location Quotient (LQ)** for every plate in every country. LQ is an economic geography metric that measures a region's concentration of a variable relative to a larger reference area.

**The Formula:**
`LQ = (Plate Notes in Country / Total Notes in Country) / (Global Plate Notes / Global Total Notes)`

* **LQ = 1.0:** The plate is found exactly as often as expected (Normal dispersion).
* **LQ = 3.0:** The plate is 3 times more concentrated in this country than the European average (Over-represented / Extreme).
* **LQ = 0.2:** The plate is 5 times rarer than expected (Under-represented).

### 2. The Statistical Anchor (Core vs. Rest of World)
Tourist hubs outside the Eurozone (e.g., Cuba, Iceland, Albania) often have tiny EBT baselines. A single tourist registering a bundle of crisp notes in these countries can artificially spike the LQ to absurd levels (e.g., LQ = 45.0), destroying the map's color scale.

To prevent this, the engine divides the world into two tiers:
* **The Core Anchor:** The 27 Eurozone countries + Switzerland. The engine exclusively uses data from these deeply established markets to calculate the plate's taxonomy, dispersion profile, and maximum color scale limits.
* **The Periphery (Rest of World):** Notes found outside the core are aggregated into a virtual "Rest of World" pool to calculate a stable external LQ. While they are excluded from skewing the scale, peripheral countries are still drawn on the map with their individual LQs available in the tooltips.

### 3. Data Reliability & The "X-Ray" Filter
Not all LQs are created equal. An LQ of 5.0 based on 2,000 notes is a mathematical certainty; an LQ of 5.0 based on 4 notes is statistical noise. The engine strictly categorizes country data into three reliability tiers:

* 🟩 **High Reliability (Solid Colors):** > 100 notes found, OR > 20 notes representing at least 5% of the local baseline.
* 🟧 **Medium Reliability (50% Checker Pattern):** > 30 notes found, OR > 5 notes representing at least 2% of the local baseline.
* 🟥 **Low Reliability (25% Crosshatch Pattern):** Anything below the thresholds.

By default, the map only renders High Reliability data to guarantee absolute accuracy. Users can manually toggle the "Show low/medium reliability data" to explore provisional data represented via stencil textures.

### 4. Dynamic Clustering (Jenks Natural Breaks)
Rather than using rigid, hardcoded thresholds (e.g., arbitrarily deciding that an LQ > 2.5 is always "Extreme"), the map uses the **Jenks Natural Breaks algorithm** (1D K-Means clustering). 

The engine scans the high-reliability LQs of a specific plate and calculates the natural "abysses" or gaps in the data distribution. This means the color scale and the legend adapt dynamically to the unique topography of every single print run, accurately identifying what constitutes an "Extreme Concentration" for that specific plate.

### 5. Agnostic Taxonomy (Dispersion Profiles)
Because we cannot definitively prove *how* a note arrived at its destination (whether it was officially exported by a central bank or carried in a tourist's wallet), the v2.0 engine abandons presumptive terminology like "Exported to". 

Instead, it evaluates the top High-Reliability LQs and their ratios to assign a purely descriptive, data-driven geographic profile:

* **Domestic Concentration:** The absolute highest concentration peak remains in the country where the plate was originally printed.
* **Displaced Concentration:** The plate has a single, isolated massive peak in a foreign country, completely overshadowing the printer's home country.
* **Multi-Hub Concentration:** The plate shows statistically tied concentration peaks across multiple non-contiguous countries.
* **Endemic Leakage:** A massive concentration in the printer's home country, heavily shared with an immediate bordering neighbor (organic cross-border trade).
* **Pandemic Dispersion:** The standard deviation among LQs is exceedingly low, meaning the plate has spread uniformly across the continent with no major peaks.
* **Undetermined:** Insufficient high-reliability data to establish a profile.

---

## 🤝 Credits & Acknowledgements

* *Data Sources: EuroBillTracker (weekly public dump) and [Guy Sohier's Catalog](http://liste.eurobillets.free.fr).*
* **Idea, Conceptualization, and Project Management:** Miguel Viterbo (*lmviterbo* @ EuroBillTracker, *ShortOkapi* @ Banknotesworld)
* **Math Solutions, Algorithms, and Code:** Gemini 3.1 Pro
