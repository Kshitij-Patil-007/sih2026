# Sample Satellite Image Sources

The checked-in demo images are small, reproducible fixtures for local testing. The links below are optional sources for downloading additional imagery; downloaded files are not automatically part of the repository.

## Dataset 1: Single Urban/Port Image
**Option A: NASA Earth Observatory (Easiest)**
- Go to: https://earthobservatory.nasa.gov/images
- Search: "port" or "airport" or "city"
- Download any high-res satellite image (usually 4096px)
- Save as: `sample_data/urban_port.jpg`

**Quick picks:**
- Mumbai Port: https://eoimages.gsfc.nasa.gov/images/imagerecords/152000/152066/mumbai_oli_2023219_lrg.jpg
- Singapore Port: https://eoimages.gsfc.nasa.gov/images/imagerecords/151000/151973/singapore_oli_2023166_lrg.jpg

## Dataset 2: Disaster Before/After (Flood)
**NASA Disasters Mapping Portal:**
- Go to: https://maps.disasters.nasa.gov/
- Or use these direct links:

**Kerala Floods 2018:**
- Before: https://eoimages.gsfc.nasa.gov/images/imagerecords/92000/92568/kerala_oli_2018211_lrg.jpg
- After: https://eoimages.gsfc.nasa.gov/images/imagerecords/92000/92568/kerala_oli_2018219_lrg.jpg

**Pakistan Floods 2022:**
- Before: https://eoimages.gsfc.nasa.gov/images/imagerecords/150000/150083/pakistan_oli_2021230_lrg.jpg
- After: https://eoimages.gsfc.nasa.gov/images/imagerecords/150000/150083/pakistan_oli_2022230_lrg.jpg

## Dataset 3: Deforestation/Urban Growth
**Amazon Deforestation:**
- Before: https://eoimages.gsfc.nasa.gov/images/imagerecords/145000/145888/rondonia_tm5_1986227_lrg.jpg
- After: https://eoimages.gsfc.nasa.gov/images/imagerecords/145000/145888/rondonia_oli_2023228_lrg.jpg

**Dubai Urban Growth:**
- Before (1990): https://eoimages.gsfc.nasa.gov/images/imagerecords/7000/7464/dubai_tm5_1990_lrg.jpg
- After (2023): https://eoimages.gsfc.nasa.gov/images/imagerecords/151000/151730/dubai_oli_2023125_lrg.jpg

---

## Quick Download Instructions:

### Windows Quick Method:
1. Open this file in your browser
2. Right-click each URL above
3. Choose "Save link as..."
4. Save to: `C:\Users\Kshitij Patil\projects\helloworld\sih2026\sample_data\`

### Using Python (automated):
Run `py download_samples.py` from the repository root. Review licensing and file sizes before committing any downloaded imagery.

---

## Naming Convention:
Save as:
- `urban_port.jpg` - Single urban image
- `flood_before.jpg` + `flood_after.jpg` - Disaster pair
- `deforest_before.jpg` + `deforest_after.jpg` - Change detection pair
