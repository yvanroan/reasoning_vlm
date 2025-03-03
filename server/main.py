#http://ai.google.dev/gemini-api/docs/migrate

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import base64
import os
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise HTTPException(status_code=500, detail="API key not configured")

client = genai.Client(api_key=api_key)
chat = client.chats.create(model='gemini-2.0-flash')

class TextRequest(BaseModel):
    text: str

@app.post("/analyze/image")
async def analyze_image(image: UploadFile):
    # try:
        # Read the image file
    image_contents = await image.read()
    
    # Create the message parts
    message = [
        "Describe how the objects in this image relate to each other spatially in a json format",
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_contents).decode('utf-8')
            }
        }
    ]
    
    response = chat.send_message(message)
    return response.text

    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/text")
async def analyze_text(request: TextRequest):
    try:
        response = chat.send_message(request.text)
        return response.text

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)