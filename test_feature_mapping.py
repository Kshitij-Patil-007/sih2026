"""Offline and API smoke tests for the in-house feature mapper."""
from pathlib import Path

import pytest
from PIL import Image

from backend.feature_mapper import detect_and_highlight


@pytest.fixture
def test_image():
    path = Path(__file__).parent / "test_satellite.png"
    if not path.exists():
        pytest.skip("test_satellite.png is not present")
    return Image.open(path).convert("RGB")


def test_roads_mapping_returns_overlay(test_image):
    result = detect_and_highlight(test_image, "Highlight all roads")
    assert result["feature"] == "roads"
    assert isinstance(result["count"], int)
    assert 0 <= result["coverage_pct"] <= 100
    assert result["highlighted"].mode == "RGB"


def test_water_mapping_returns_overlay(test_image):
    result = detect_and_highlight(test_image, "Show all water bodies")
    assert result["feature"] == "water"
    assert isinstance(result["count"], int)
    assert 0 <= result["coverage_pct"] <= 100
    assert result["highlighted"].mode == "RGB"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
