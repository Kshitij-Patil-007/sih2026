"""Direct test of Groq API to see actual error"""
import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
from PIL import Image
import base64
import io

# Create test image
img = Image.new('RGB', (100, 100), color='blue')

# Convert to base64
buffered = io.BytesIO()
img.save(buffered, format="PNG")
img_base64 = base64.b64encode(buffered.getvalue()).decode()

print(f"GROQ_API_KEY exists: {bool(os.environ.get('GROQ_API_KEY'))}")
print(f"API Key (first 20 chars): {os.environ.get('GROQ_API_KEY')[:20]}")

try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    print("Calling Groq API...")
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
                        "text": "What color is this image?"
                    }
                ]
            }
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    print("SUCCESS!")
    print(f"Response: {completion.choices[0].message.content}")

except Exception as e:
    print("ERROR!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {e}")
    import traceback
    traceback.print_exc()
