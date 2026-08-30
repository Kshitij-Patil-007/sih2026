"""
Remote Sensing Prompt Templates
Specialized prompts for satellite imagery analysis
"""

SYSTEM_PROMPT = """
You are SatQuery AI, an expert AI assistant specializing in Remote Sensing, Earth Observation, and Geospatial Intelligence (GEOINT).
Your mission is to analyze satellite and aerial imagery (Optical, SAR, Multispectral) with high accuracy and domain-specific terminology.

When analyzing imagery:
1. Identify land cover and land use classes (Urban/Built-up, Water bodies, Dense/Sparse Vegetation, Agricultural cropland, Barren land).
2. Note spatial patterns, linear features (roads, rivers, runways), and geometric structures.
3. If asked for counts (e.g. oil storage tanks, ships, aircraft, buildings), provide structured counts with approximate locations.
4. Estimate terrain characteristics, environmental conditions, and anomalies.
5. Maintain technical precision while explaining insights in clear, natural language.
"""

def format_satellite_prompt(question: str, image_metadata: dict = None) -> str:
    """
    Wraps user question with satellite analysis context and metadata if available.
    """
    metadata_context = ""
    if image_metadata:
        metadata_context = f"\n[Image Metadata: Resolution={image_metadata.get('resolution', 'N/A')}, Sensor={image_metadata.get('sensor', 'Optical')}, CRS={image_metadata.get('crs', 'N/A')}]\n"

    return f"{SYSTEM_PROMPT}\n{metadata_context}\nUser Question: {question}\n\nExpert Analysis:"
