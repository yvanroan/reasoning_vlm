import json
import asyncio
import os
from context_integration import get_inference_from_context_integration, analyze_image
from reasoning_loop import generate_enhanced_inference, store_inference_feedback
from ingestion_pipeline import process_single_image
from vector_db import add_image_to_db 
import aiohttp


PROCESSED_FOLDER = "processed_images"
IMAGE_FOLDER = "images"
async def ingest_single_image(image_name):
    """Process and ingest a single image from the images folder"""
    try:
        image_path = f"{IMAGE_FOLDER}/{image_name}"
        if not os.path.exists(image_path):
            print(f"Image {image_name} not found in server/images/")
            return None
            
        # Create processed images folder if it doesn't exist
        os.makedirs(PROCESSED_FOLDER, exist_ok=True)

        # Load existing mapping if it exists
        mapping_file = "image_mapping.json"
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                image_mapping = json.load(f)
        else:
            image_mapping = {}

        # Generate unique image ID
        image_id = f"id{len(os.listdir(PROCESSED_FOLDER)) + 1}"

        async with aiohttp.ClientSession() as session:
            result = await process_single_image(session, image_path)
        

        if result['objects'] is None:
            print("Failed to process image")
            return None
        
        add_image_to_db(
            image_id, 
            result['image_path'], 
            result['objects'], 
            result['scene_description'], 
            image_name, 
            result['relationships']
        )
         
        
        image_mapping[image_name] = image_id
        
        with open(mapping_file, 'w') as f:
            json.dump(image_mapping, f, indent=4)
        
        return image_id
        
    except Exception as e:
        print(f"Error ingesting image: {e}")
        return None

async def compare_inferences(image_name):
    """Compare basic vs enhanced inference generation for a new image"""
    try:
        print(f"\n=== Processing Image: {image_name} ===")

        image_id = None

        name_to_id = {}
        with open('image_mapping.json', 'r') as f:
            name_to_id = json.load(f)

        if image_name in name_to_id:
            print(f"Image already in database: {image_name}")
            image_id = name_to_id[image_name]
        else:
            print("\nIngesting image...")
            image_id = await ingest_single_image(image_name)


        if not image_id:
            print("Failed to process image")
            return
            
        print(f"Image processed with ID: {image_id}")
        
        # Get scene analysis first
        scene_analysis = analyze_image(image_id)
        if not scene_analysis:
            print("Failed to analyze scene")
            return

        # Get basic inference
        print("\n1. Basic Inference from Context Integration:")
        basic_inference = await get_inference_from_context_integration(scene_analysis, image_id)
        if basic_inference:
            try:
                inference_json = json.loads(basic_inference)
                print(inference_json)
            except json.JSONDecodeError:
                print(basic_inference)  # Print raw text if not JSON
            
            # Get user rating for basic inference
            print("\nRate the basic inference (0-1):")
            rating = float(input())
            
            # Optional feedback
            print("Enter feedback (optional, press Enter to skip):")
            feedback = input().strip()
            
            if feedback:
                store_inference_feedback(
                    image_id=image_id,
                    inference=feedback,
                    scene_context=scene_analysis,
                    rating=rating
                )
        
        # Get enhanced inference
        print("\n2. Enhanced Inference with Learning:")

        enhanced_inference, _ = await generate_enhanced_inference(
            scene_context=scene_analysis,
            image_path=f"{PROCESSED_FOLDER}/{image_name}"
        )
        if enhanced_inference:
            try:
                inference_json = json.loads(enhanced_inference)
                print(inference_json)
            except json.JSONDecodeError:
                print(enhanced_inference)
            
            print("\nRate the enhanced inference (0-1):")
            rating = float(input())
            
            print("Enter feedback (optional, press Enter to skip):")
            feedback = input().strip()
            
            if feedback:
                store_inference_feedback(
                    image_id=image_id,
                    inference=feedback,
                    scene_context=scene_analysis,
                    rating=rating
                )
                
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    
    selection = input("\nEnter the name of the image to analyze(e.g. 'image_name.jpg'): ")
    try:
        asyncio.run(compare_inferences(selection))
    except Exception as e:
        print(f"Error Invalid Image Name: {e}") 

    #delete the image from the db
    # delete_image_from_db("id289")
    # delete_image_from_db("id290")
