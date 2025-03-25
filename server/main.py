from fastapi import FastAPI, UploadFile, HTTPException, Form, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import base64
import os
import json
import asyncio
from typing import Optional, List
from context_integration import analyze_image, generate_inference, get_inference_from_context_integration
from reasoning_loop import generate_enhanced_inference, store_inference_feedback
from google import genai
from compare_inferences import ingest_single_image
from prompts import IMAGE_ANALYSIS_PROMPT
from fastapi.staticfiles import StaticFiles
# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise HTTPException(status_code=500, detail="API key not configured")

client = genai.Client(api_key=api_key)
chat = client.chats.create(model='gemini-2.0-flash')

# Constants
PROCESSED_FOLDER = "processed_images"
IMAGE_FOLDER = "images"

# Load image mappings
id_to_name = {}
name_to_id = {}

try:
    with open('id_to_name_mapping.json', 'r') as f:
        id_to_name = json.load(f)
    
    with open('image_mapping.json', 'r') as f:
        name_to_id = json.load(f)
except Exception as e:
    print(f"Error loading mappings: {e}")

# Pydantic models
class TextRequest(BaseModel):
    text: str

class ExistingImageRequest(BaseModel):
    filename: str

class FeedbackRequest(BaseModel):
    filename: str
    basicRating: int
    basicFeedback: Optional[str] = ""

# Add this Pydantic model for the enhanced inference request
class EnhancedInferenceRequest(BaseModel):
    filename: str
    scene_analysis: dict

@app.get("/files")
async def get_files():
    """Return list of available image files"""
    try:
        files = []
        for filename in os.listdir(IMAGE_FOLDER):
            if filename.lower().endswith(('.jpg', '.jpeg')):
                files.append(filename)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inference/basic")
async def basic_inference(request: ExistingImageRequest):
    """Inference on an image using relationships stored in the vector database"""
    try:
        filename = request.filename
        # print(filename)
        
        if filename in name_to_id:
            image_id = name_to_id[filename]
        else:
            image_id = await ingest_single_image(filename)
            
        if not image_id:
            raise HTTPException(status_code=400, detail="Failed to process image")
            
        # Get scene analysis
        scene_analysis = analyze_image(image_id)

        # Get basic analysis
        basic_result = await get_inference_from_context_integration(scene_analysis, image_id)
        
        return {
            "text": basic_result,
            "scene_analysis": scene_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/inference/enhanced")
async def enhanced_inference(request: EnhancedInferenceRequest):
    """Inference on an image using relationships(from image) and feedback(from users) stored in the vector database"""
    try:
        filename = request.filename
        scene_analysis = request.scene_analysis
        
        print(f"Received request for enhanced inference: filename={filename}")
        print(f"Scene analysis: {scene_analysis}")
        
        if filename not in name_to_id:
            raise HTTPException(status_code=400, detail=f"Image not found: {filename}")
        
        image_path = f"{PROCESSED_FOLDER}/{filename}"
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail=f"Image file not found at {image_path}")
            
        # Get enhanced analysis
        result, relevant_patterns = await generate_enhanced_inference(
            scene_context=scene_analysis,
            image_path=image_path
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate enhanced inference")
        
        return {
            "text": result,
            "relevant_patterns": relevant_patterns
        }
        
    except Exception as e:
        print(f"Error in enhanced inference: {str(e)}")
        print(f"Full error details: ", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/all")
async def inference(image: UploadFile, text: str = Form()):
    try:
        # Read the image file
        image_contents = await image.read()
       
        message = [
            text,
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_contents).decode('utf-8')
                }
            }
        ]
        
        response = chat.send_message(message)
        return response.text

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/relationships/image")
async def analyze_image_route(image: UploadFile = File(...)):
    """Analyze a newly uploaded image and derive relationships"""
    try:
        # Read the image file
        image_contents = await image.read()
        
        # Create the message parts for basic analysis
        message = [
            IMAGE_ANALYSIS_PROMPT,
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_contents).decode('utf-8')
                }
            }
        ]
        
        response = chat.send_message(message)
        
        # For demo purposes, we'll just use the same analysis twice
        # In a real implementation, you'd process the image through your pipeline
        # and generate the enhanced analysis with few-shot learning
        
        return response.text
    # {
    #         "basic": basic_response.text,
    #         "enhanced": "Enhanced analysis would be generated through your few-shot learning pipeline."
    #     }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/text")
async def analyze_text(request: TextRequest):
    try:
        response = chat.send_message(request.text)
        return {"analysis": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Store user feedback on analyses"""
    try:
        # Find image ID from filename
        image_id = name_to_id.get(request.filename)
        
        if not image_id:
            raise HTTPException(status_code=400, detail="Image not found")
            
        # Get scene context for the image
        scene_context = analyze_image(image_id)
        
        # Store feedback if ratings are provided
        if request.basicRating > 0 and request.basicFeedback:
            store_inference_feedback(
                image_id=image_id,
                inference=request.basicFeedback,
                scene_context=scene_context,
                rating=request.basicRating / 5.0  # Convert 5-star to 0-1 scale
            )
            
        
            
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this after creating the FastAPI app
app.mount("/processed_images", StaticFiles(directory="processed_images"), name="processed_images")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)