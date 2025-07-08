# Trends in Population and Settlement at Risk of Seaward Hazards in the U.S., 1990–2020: Data Choice Really Matters

## Authors
Yoonjung Ahn¹, Deborah Balk², Kytt MacManus³, Stefan Leyk⁴, Hasim Engin⁵  
¹University of Kansas  
²CUNY Institute for Demographic Research  
³Columbia University (CIESIN)  
⁴University of Colorado Boulder  
⁵Columbia University (CIESIN)

## Project Overview

This project evaluates how different spatial population datasets impact estimates of population and settlement exposure to seaward hazards in the U.S. Low Elevation Coastal Zone (LECZ) from 1990 to 2020. It compares census-based data with global population products and highlights discrepancies due to data choices.

---

## Repository Structure

This repository contains scripts used to process population datasets, calculate zonal statistics, and produce summary metrics and sensitivity analyses.

### Python Scripts

| Filename | Purpose |
|----------|---------|
| `assemble_county_times_series_attributes.py` | Combines county-level attributes (population, elevation, etc.) over time into a unified timeseries dataframe. |
| `calculate_allocations.py` | Allocates population estimates to LECZ zones using various data sources. |
| `calculate_global_zonal_statistics.py` | Computes zonal population statistics for global datasets like GPW, WorldPop, GHS-POP, and LandScan. |
| `create_zones.py` | Creates LECZ and administrative boundary zones for analysis. |
| `infill_hisdac.py` | Processes and interpolates historical HISDAC-US building data. |
| `infill_hisdac_update_counties.py` | Updated version of `infill_hisdac.py` that includes county-level handling and additional corrections. |
| `transfer_global_zstats.py` | Transfers global zonal statistics results into the main dataset format for integration and comparison. |

### R Markdown

| Filename | Purpose |
|----------|---------|
| `Sensitivity analysis county.Rmd` | Performs a sensitivity analysis comparing population estimates across different datasets at the county level. Generates visualizations and summary tables. |

---

## Dependencies

### Python

- Python ≥ 3.8
- Required packages (install via `pip install -r requirements.txt` or manually):
  - `numpy`
  - `pandas`
  - `rasterio`
  - `geopandas`
  - `shapely`
  - `scipy`
  - `tqdm`

Make sure `GDAL` and `PROJ` are properly installed on your system.

### R

- R ≥ 4.0
- Required R packages:
  - `tidyverse`
  - `sf`
  - `raster`
  - `exactextractr`
  - `tmap`
  - `knitr`

---

## Data Requirements

### Input Data
The scripts assume access to the following data:
- Global population datasets: GPWv4, WorldPop, GHS-POP, LandScan
- U.S. Census and HISDAC-US datasets (county-level)
- LECZ shapefiles (Low Elevation Coastal Zones)
- U.S. county boundary shapefiles

Due to licensing restrictions, datasets are **not included**. Please acquire and place them in the appropriate directories before running scripts.

---

## Running the Code

1. **Create spatial zones**  
   Run `create_zones.py` to generate the LECZ and county zones.

2. **Process HISDAC-US data**  
   Run `infill_hisdac.py` or `infill_hisdac_update_counties.py` to interpolate historical data on buildings and housing units.

3. **Calculate global population statistics**  
   Run `calculate_global_zonal_statistics.py` to generate zonal statistics from each global population dataset.

4. **Allocate populations**  
   Run `calculate_allocations.py` to spatially allocate population values within LECZ boundaries.

5. **Assemble final dataset**  
   Run `assemble_county_times_series_attributes.py` to combine all data into a unified county-year dataset.

6. **Transfer results**  
   Run `transfer_global_zstats.py` to integrate global statistics into the final analysis dataset.

7. **Run Sensitivity Analysis**  
   Open and knit `Sensitivity analysis county.Rmd` in RStudio to generate sensitivity analysis plots and tables.

---

## Citation

If you use this code or dataset, please cite the associated paper:

> Ahn, Y., Balk, D., MacManus, K., Leyk, S., & Engin, H. (2025). *Trends in population and settlement at risk of seaward hazards in the U.S., 1990–2020: Data choice really matters.*

---

## License

This project is released under the [MIT License](LICENSE).

---

## Contact

For questions or issues, contact **Yoonjung Ahn** at [yjahn@ku.edu](mailto:y943a214@ku.edu).
