"""
Query Router
Classifies user queries and routes them to appropriate backend modules
"""

import re

def route_query(question: str):
    """
    Analyze the user's question and determine the query type.

    Args:
        question: User's natural language question

    Returns:
        dict with:
            - 'query_type': str (single_image, change_detection, feature_count, ndvi_analysis)
            - 'keywords': list of detected keywords
            - 'suggested_action': str describing what to do
    """

    question_lower = question.lower()

    # Keyword patterns for different query types
    change_keywords = ['change', 'difference', 'before', 'after', 'compare', 'temporal',
                       'evolution', 'growth', 'expansion', 'loss', 'deforestation',
                       'flood', 'damage', 'inundat', 'destroyed', 'delta']

    fusion_keywords = ['fusion', 'fuse', 'optical-sar', 'optical sar', 'sar and optical']

    count_keywords = ['count', 'how many', 'number of', 'quantity', 'total']

    mapping_keywords = ['highlight', 'show me', 'map', 'mark', 'outline', 'detect',
                        'find', 'locate', 'identify', 'where are', 'where is']

    ndvi_keywords = ['vegetation', 'ndvi', 'green', 'forest', 'crop', 'agriculture', 'plant']

    # Check for fusion queries
    if any(keyword in question_lower for keyword in fusion_keywords):
        return {
            'query_type': 'optical_sar_fusion',
            'keywords': [kw for kw in fusion_keywords if kw in question_lower],
            'suggested_action': 'Use dual-encoder Optical-SAR fusion'
        }

    # Check for change detection queries
    if any(keyword in question_lower for keyword in change_keywords):
        return {
            'query_type': 'change_detection',
            'keywords': [kw for kw in change_keywords if kw in question_lower],
            'suggested_action': 'Use detect_changes() with before/after images'
        }

    # Check for feature mapping queries (highlight, detect, find)
    if any(keyword in question_lower for keyword in mapping_keywords):
        return {
            'query_type': 'feature_mapping',
            'keywords': [kw for kw in mapping_keywords if kw in question_lower],
            'suggested_action': 'Use detect_and_highlight() to map and highlight features'
        }

    # Check for counting queries
    if any(keyword in question_lower for keyword in count_keywords):
        return {
            'query_type': 'feature_mapping',
            'keywords': [kw for kw in count_keywords if kw in question_lower],
            'suggested_action': 'Use detect_and_highlight() to count and highlight features'
        }

    # Check for NDVI/vegetation analysis
    if any(keyword in question_lower for keyword in ndvi_keywords):
        return {
            'query_type': 'ndvi_analysis',
            'keywords': [kw for kw in ndvi_keywords if kw in question_lower],
            'suggested_action': 'Use NDVI calculation if multispectral data available'
        }

    # Default: single image Q&A
    return {
        'query_type': 'single_image',
        'keywords': [],
        'suggested_action': 'Use ask_vision_model() with the image and question'
    }


def extract_features(question: str):
    """
    Extract specific features/objects the user is asking about.

    Examples:
        "How many tanks?" -> ['tanks']
        "Detect buildings and roads" -> ['buildings', 'roads']
    """

    # Common satellite image features
    feature_patterns = [
        'building', 'road', 'vehicle', 'tank', 'ship', 'plane', 'aircraft',
        'tree', 'water', 'river', 'lake', 'ocean', 'forest', 'field',
        'urban', 'rural', 'industrial', 'residential', 'bridge', 'port'
    ]

    detected_features = []
    question_lower = question.lower()

    for feature in feature_patterns:
        if feature in question_lower:
            detected_features.append(feature)

    return detected_features


# Test function
if __name__ == "__main__":
    test_queries = [
        "What changed between these two images?",
        "How many storage tanks are visible?",
        "Describe the vegetation in this area",
        "What do you see in this satellite image?"
    ]

    print("Query Router Test:")
    for q in test_queries:
        result = route_query(q)
        print(f"\nQuery: {q}")
        print(f"Type: {result['query_type']}")
        print(f"Action: {result['suggested_action']}")
