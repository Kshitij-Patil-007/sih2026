# Task Instructions for Person 5 & Person 6

**Date:** August 30, 2026 | **Deadline:** September 5, 2026

---

## What You're Building

You're creating **specialized AI analysis modules** that will be integrated into our backend. These are NOT new AI models from scratch—you're using existing APIs (Gemini, Claude, GPT-4) with **specialized prompts and preprocessing** for specific satellite imagery types.

---

## 🛰️ Person 5: SAR (Radar) Image Analysis Module

### What is SAR?
Synthetic Aperture Radar (SAR) satellites use radar instead of cameras. SAR images:
- Are grayscale (not RGB color)
- Work through clouds and at night
- Bright pixels = metal/ships/buildings
- Dark pixels = water/smooth surfaces

### Your Task:
Create a file: `backend/sar_analyzer.py`

**What it should do:**
1. Detect if an image is SAR (grayscale + speckled texture)
2. Use specialized prompts that understand radar terminology
3. Integrate with Gemini or Claude API
4. Return analysis in the same format as our main VLM engine

**Example Function Structure:**
```python
def analyze_sar_image(image, question: str):
    """
    Analyze SAR satellite imagery.
    
    Args:
        image: PIL Image (SAR satellite image)
        question: User's question
    
    Returns:
        dict with 'answer', 'model_used', 'image_type'
    """
    # Your code here
    # Use Gemini/Claude API with SAR-specific prompts
    pass
```

**Test it with:**
- Download 2-3 SAR images (ships, ports, oil spills)
- Run: `py ask.py sample_data/sar_image.png "Detect ships in this radar image"`

---

## 🌾 Person 6: Agriculture & Crop Health Module

### What is NDVI?
NDVI (Normalized Difference Vegetation Index) measures plant health:
- Formula: `(NIR - Red) / (NIR + Red)`
- Range: -1 to +1
- Values: < 0.2 (stressed), 0.2-0.5 (moderate), > 0.5 (healthy)

### Your Task:
Create a file: `backend/agriculture_ai.py`

**What it should do:**
1. Calculate NDVI from satellite images (estimate from RGB if NIR not available)
2. Use agriculture-specific prompts (crop health, irrigation, pest damage)
3. Integrate with Gemini API
4. Return NDVI statistics + AI analysis

**Example Function Structure:**
```python
def analyze_agriculture(image, question: str):
    """
    Analyze agricultural satellite imagery with crop health focus.
    
    Args:
        image: PIL Image
        question: User's agricultural question
    
    Returns:
        dict with 'answer', 'ndvi_stats', 'model_used'
    """
    # Your code here
    # Calculate NDVI + use Gemini with agriculture prompts
    pass
```

**Test it with:**
- Download 2-3 crop field images
- Run: `py ask.py sample_data/farm.jpg "Assess crop health and irrigation"`

---

## 📝 What to Submit to Backend Lead (Kshitij)

When done, send him:
1. Your Python file (`sar_analyzer.py` or `agriculture_ai.py`)
2. 2-3 test images you used
3. Example questions that work well with your module

He will integrate it into the router and main backend.

---

## 🎯 Key Points

### **You are NOT training AI models!**
- You're using existing APIs (Gemini, Claude) just like our main backend
- The "specialization" comes from:
  1. Domain-specific prompts
  2. Custom preprocessing (NDVI calculation, SAR detection)
  3. Specialized output formatting

### **Example of what judges will ask you:**
- **Judge:** "Did you train this agriculture model?"
- **You:** "No, we use Gemini's multimodal foundation model but inject specialized remote sensing prompts and calculate NDVI vegetation indices for domain-specific crop health analysis."

---

## 📚 Resources

### SAR Images:
- https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1
- Search "Sentinel-1 SAR ship detection" on Google Images

### Agriculture/Crop Images:
- https://earthobservatory.nasa.gov/ (search "agriculture" or "crops")
- Google Earth screenshots of farm fields

### API Documentation:
- Gemini API: https://ai.google.dev/docs
- Our existing code: Check `backend/vlm_engine.py` for examples

---

## ⏰ Timeline

- **Today (Aug 30, evening):** Understand the task, collect test images
- **Tomorrow (Aug 31):** Write your module, test it independently
- **Sept 1:** Send to Kshitij for integration, test together
- **Sept 2-3:** Polish and prepare your 60-second pitch explanation

---

**Questions?** Ask Kshitij (Backend Lead) or check the existing `backend/vlm_engine.py` for reference on how to structure your code!
