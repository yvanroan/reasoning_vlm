import json
import asyncio
import aiohttp
import os
from context_integration import analyze_image
from reasoning_loop import (
    store_inference_feedback,
    extract_relationship_keys
)
import aiofiles
from time import sleep
from vector_db import get_all_images_from_db



def extract_feedback_ratings(ai_response):
    """Extract feedback and ratings from AI response text"""
    if not ai_response:
        return []
        
    text = ai_response.strip('"').replace('\\n', '\n')
    parts = text.split("FEEDBACK ")
    
    results = []
    for part in parts[1:]:
        try:
            number_and_content = part.split(":", 1)
            if len(number_and_content) < 2:
                continue
                
            content = number_and_content[1].strip()
            feedback_parts = content.split("\nRATING:")
            
            if len(feedback_parts) < 2:
                continue
            
            feedback_text = feedback_parts[0].strip()
            rating_text = feedback_parts[1].strip()
            rating = float(rating_text.split("\n")[0])
            
            results.append((feedback_text, rating))
        except Exception as e:
            print(f"Error extracting feedback: {e}")
            continue
    
    return results

async def generate_feedback(prompt, image_path):
    """Generate feedback about a scene"""
    try:
        async with aiofiles.open(image_path, 'rb') as f:
            file_data = await f.read()
            
        form_data = aiohttp.FormData()
        form_data.add_field(
            'image',
            file_data,
            filename=os.path.basename(image_path),
            content_type='image/jpeg'
        )
        
        form_data.add_field(
            'text', 
            json.dumps({"text": prompt}),
            content_type='application/json'
        )

        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8000/analyze/all", data=form_data) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error analyzing image {image_path}: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"Error analyzing image {image_path}: {str(e)}")
        return None

def test_reasoning_pipeline_with_feedback(image_id, feedback_and_ratings, scene_analysis):
    """Process and store feedback"""
    
    for feedback_text, rating in feedback_and_ratings:
        store_inference_feedback(
            image_id,
            feedback_text,
            scene_analysis,
            rating
        )

async def test_reasoning_pipeline(image_name, image_id):
    """Run complete reasoning pipeline for an image"""
    
    scene_analysis = analyze_image(image_id)
    
    
    rel_keys = extract_relationship_keys(scene_analysis)

    base_prompt = f"""
    You are a visual scene analysis expert who can infer meaningful insights from object relationships in images. I'll provide you with extracted scene information, and I need you to:

    1) Generate a positive feedback about how accurate the scene information provided describes the images
    2) provide a rating on how well the response matches the scene

    Scene information:
    {scene_analysis}

    extracted relationship keys:
    {rel_keys}

    For each feedback focus on:
    - contextual understanding, 
    - causal connections, 
    - specificity of relationships, 
    - novel insights
    e.g. The connection between the unlit state of the candle and the inference about 'recently prepared' or 'will light soon' is insightful.

    For each rating (0.0-1.0):
    - Give 0.9-1.0 for insights that reveal non-obvious meaning from unusual object positions(set a high bar for this, they should be rare)
    - Give 0.6-0.8 for reasonable but more obvious interpretations
    - Rate below 0.6 if not well-supported by the visual evidence

    Format your response as:

    FEEDBACK 1: [Your detailed feedback]
    RATING: [0.0-1.0]
    """

    feedback = await generate_feedback(base_prompt, f"processed_images/{image_name}")
    feedback_and_ratings = extract_feedback_ratings(feedback)
    test_reasoning_pipeline_with_feedback(image_id, feedback_and_ratings, scene_analysis)

def bootstrap_reasoning_pipeline_with_feedback():
    """Run pipeline for all images"""
    images = get_all_images_from_db()

    for i, image_id in enumerate(images['ids']):
        if i > 185:
            image_name = images['metadatas'][i]['image_name']
            print(f"Processing image {image_name} (ID: {image_id})")
            asyncio.run(test_reasoning_pipeline(image_name, image_id))
            sleep(7)

if __name__ == "__main__":
    bootstrap_reasoning_pipeline_with_feedback()