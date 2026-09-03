"""
Vision-Language Model Engine
Connects to AI models to answer questions about satellite images
"""

import base64
import io
import warnings
from PIL import Image

# Suppress harmless deprecation warnings
warnings.filterwarnings("ignore")

def ask_vision_model(image, question: str, model_type="placeholder"):
    """
    Send image + question to a vision-language model.

    Args:
        image: PIL Image object
        question: Natural language question about the image
        model_type: "gemini", "claude", "huggingface", "groq", "placeholder"

    Returns:
        dict with:
            - 'answer': Text response from the model
            - 'confidence': float (if available)
            - 'model_used': str
    """

    if model_type == "placeholder":
        # Mock response for testing
        return {
            'answer': f"Mock response: Analyzing your question '{question}'. "
                     f"The satellite image shows urban areas, vegetation, and water bodies.",
            'confidence': 0.85,
            'model_used': 'placeholder'
        }

    elif model_type == "gemini":
        return _call_gemini(image, question)

    elif model_type == "claude":
        return _call_claude(image, question)

    elif model_type == "huggingface":
        return _call_huggingface(image, question)

    elif model_type == "groq":
        return _call_groq(image, question)

    else:
        raise ValueError(f"Unknown model type: {model_type}")


def _call_gemini(image, question):
    """Call Google Gemini Vision API"""
    try:
        import os

        # Try new google.genai package first, fallback to deprecated google.generativeai
        try:
            from google import genai
            client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

            # Convert PIL image to bytes
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            # Use the new API
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=[question, {"mime_type": "image/png", "data": img_bytes.read()}]
            )
            answer_text = response.text
            model_name = 'gemini-2.0-flash-exp'

        except ImportError:
            # Fallback to deprecated package
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

            # Use gemini-3.6-flash (latest stable vision model as of 2026)
            model = genai.GenerativeModel('gemini-3.6-flash')
            model_name = 'gemini-3.6-flash'

            response = model.generate_content([question, image])
            answer_text = response.text if hasattr(response, 'text') else str(response)

        return {
            'answer': answer_text,
            'confidence': None,  # Gemini doesn't return confidence
            'model_used': model_name
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Gemini API Error: {error_details}")
        return {'answer': f"Error calling Gemini: {e}", 'confidence': 0, 'model_used': 'gemini'}


def _call_claude(image, question):
    """Call Anthropic Claude Vision API"""
    try:
        import anthropic
        import os

        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ],
                }
            ],
        )

        return {
            'answer': message.content[0].text,
            'confidence': None,
            'model_used': 'claude-sonnet-4'
        }
    except Exception as e:
        return {'answer': f"Error calling Claude: {e}", 'confidence': 0, 'model_used': 'claude'}


def _call_huggingface(image, question):
    """Call Hugging Face model (e.g., BLIP-2, Florence-2)"""
    try:
        from transformers import BlipProcessor, BlipForQuestionAnswering
        import torch

        # Load model (cache this in production!)
        processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
        model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

        # Process
        inputs = processor(image, question, return_tensors="pt")

        with torch.no_grad():
            outputs = model.generate(**inputs)

        answer = processor.decode(outputs[0], skip_special_tokens=True)

        return {
            'answer': answer,
            'confidence': None,
            'model_used': 'blip-vqa-base'
        }
    except Exception as e:
        return {'answer': f"Error calling HuggingFace: {e}", 'confidence': 0, 'model_used': 'huggingface'}


def _call_groq(image, question):
    """Call Groq API with Llama 3.2 Vision"""
    try:
        import os
        from groq import Groq

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Call Groq with vision model (using llama-3.2-11b-vision-preview)
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        return {
            'answer': completion.choices[0].message.content,
            'confidence': None,
            'model_used': 'llama-3.2-11b-vision'
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Groq API Error: {error_details}")
        return {'answer': f"Error calling Groq: {e}", 'confidence': 0, 'model_used': 'groq'}


def process_query(image, question: str, model_type="auto"):
    """
    Main entry point for query processing.
    Routes query and calls appropriate model.

    Args:
        image: PIL Image object
        question: User's natural language question
        model_type: "auto", "gemini", "claude", "huggingface", "placeholder"

    Returns:
        dict with answer and metadata
    """
    import os

    # Auto-detect best available model
    if model_type == "auto":
        if os.environ.get("GROQ_API_KEY"):
            model_type = "groq"
        elif os.environ.get("GOOGLE_API_KEY"):
            model_type = "gemini"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            model_type = "claude"
        else:
            model_type = "placeholder"

    # Preprocess image if needed (resize very large images)
    if image.width > 2048 or image.height > 2048:
        image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)

    # Call the vision model
    result = ask_vision_model(image, question, model_type)

    # Add query metadata
    result['query'] = question
    result['image_size'] = f"{image.width}x{image.height}"

    return result


# Test function
if __name__ == "__main__":
    print("Vision-Language Model Engine")
    print("To test: process_query(image, 'What do you see in this satellite image?')")
