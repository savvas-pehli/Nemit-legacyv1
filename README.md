# NEMIT Spatial-Temporal Analytics Platform

## 📌 Executive Summary
The NEMIT platform is an enterprise data analytics engine designed to monitor, aggregate, and visualize environmental health metrics, economic correlations, and logistical impacts across Greece. It bridges the gap between raw meteorological sensor data and actionable business intelligence, providing researchers and policymakers with high-resolution insights into regional pollution footprints.

## 📊 Core Business Modules

The platform is divided into five distinct analytical domains:

*   **Regional Air Quality & Spatial Mapping:** Tracks atmospheric pollutants (e.g., $NO_2$, $CO$, Benzene) across municipalities. Features time-lapsed, interactive WebGL choropleth maps to visualize the geographical spread of emissions over two decades.
*   **Macro-Economic Emission Correlation:** Analyzes the direct relationship between specific macroeconomic sectors (e.g., manufacturing, transport) and localized air pollution spikes.
*   **Regional Fuel Consumption:** Tracks historical fuel utilization across Greek prefectures and regions, providing a foundation for correlating energy demands with environmental degradation.
*   **Port of Thessaloniki (SKG) Environmental Assessment:** A localized analytics module tracking air quality, water quality, and acoustic (noise) levels to assess the real-time environmental footprint of a major Mediterranean logistical hub.
*   **nPETS Particle Distribution:** Granular diurnal and weekly analysis of sub-micron particle emissions. Processes data from highly specialized ELPI and OPS tools to monitor microscopic air quality fluctuations based on seasonal and geographical metadata.

---

## 🏗️ Architectural Integrity & Security
Under the hood, the application abandons monolithic scripting in favor of enterprise software patterns, ensuring scalability, maintainability, and absolute database security.

*   **Strict MVC Separation:** The Streamlit user interface is completely decoupled from business logic and database execution. The UI layer only renders views and passes state; all data processing occurs within isolated service controllers.
*   **Zero-Trust Parameterization:** All database communications utilize strict SQLAlchemy dictionary parameterization. Direct string interpolation for user values is explicitly prohibited, neutralizing SQL injection vectors at the architecture level.

## 🌍 Spatial Data Engineering
Geospatial data inherently degrades during cross-database migrations. This platform implements a robust Python `geo.py` interceptor to mathematically heal corrupted topological payloads before they reach the rendering engine.

*   **Dynamic Matrix Inversion:** Detects illegal coordinate storage `[Latitude, Longitude]` via bounding box checks and utilizes Shapely to mathematically invert the spatial matrix back to the standard `[Longitude, Latitude]` format.
*   **WebGL Rendering Optimization:** Enforces the Right-Hand Rule (counter-clockwise polygon winding) to bypass WebGL Back-Face Culling crashes in the browser. 
*   **Topology Healing & Decimation:** Applies a zero-buffer sweep to fix microscopic self-intersections and decimates vertex payloads (`tolerance=0.002`) to optimize client-side memory overhead during map serialization.

## ⚡ Performance & Data Processing
*   **Multi-Engine Routing:** Utilizes **Polars** for multi-threaded, high-speed aggregation of massive hourly datasets, falling back to **Pandas** for specific categorical mappings and Cartesian expansions.
*   **The Cartesian Matrix Fix:** Bypasses Plotly's notorious WebGL First-Frame Deletion bug by mathematically forcing a Cartesian grid expansion across all timestamps and municipalities, guaranteeing chronological continuity in choropleth animations.
*   **C-Library Aggregation:** Pushes heavy statistical calculations (like exact Medians using `PERCENTILE_CONT`) down to the PostgreSQL engine layer rather than choking the Python runtime.

## 🛠️ Technology Stack
*   **Language:** Python 3.10+
*   **Frontend:** Streamlit, Plotly (WebGL)
*   **Data Processing:** Polars, Pandas, Shapely, GeoPandas
*   **Database:** PostgreSQL, SQLAlchemy