import os
import json
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from vector_db import add_image_to_db
from time import sleep  
import json
import re


# Configuration
IMAGE_FOLDER = "images"  # Change this to your image folder path
PROCESSED_FOLDER = "processed_images"  # Folder to move processed images
API_ENDPOINT = "http://localhost:5000/analyze/relationships/image"
SUPPORTED_FORMATS = {'.jpg', '.jpeg'}


def clean_response_string(response_str):
    """
    Clean the response string to make it valid JSON
    
    response_str (str): String response from the analysis endpoint

    Returns:
        str: Cleaned response string
    """
    response_str = re.sub(r'```json\s*', '', response_str)

    response_str = re.sub(r'\s*```', '', response_str)
    
    response_str = response_str.strip('"')

    response_str = re.sub(r'\\n\s*', '', response_str)

    response_str = response_str.replace('\\"', '"')

    response_str = response_str.replace('\\', '')
    
    response_str = re.sub(r',(\s*[}\]])', r'\1', response_str)
    
    response_str = response_str.strip()
    
    return response_str

def parse_analysis_result(response_str):
    """
    Parse the analysis result string and extract objects, relationships, and scene description
    
    Args:
        response_str (str): String response from the analysis endpoint
    
    Returns:
        tuple: (objects_list, relationships_list, scene_description)
    """
    try:
        # Clean and parse the response string
        cleaned_response = clean_response_string(response_str)
        response = json.loads(cleaned_response)

        objects = {}  
        for obj in response["objects"]:
            objects[obj["label"]] = obj["attributes"]

        
        return objects, response["relationships"], response["scene_annotation"]
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print("Raw response:", cleaned_response)
        return {}, [], ""
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}, [], ""
 

async def process_single_image(session, image_path):
    try:
        # Prepare the file for upload
        async with aiofiles.open(image_path, 'rb') as f:
            file_data = await f.read()
            
        # Create form data with the file
        form_data = aiohttp.FormData()
        form_data.add_field('image',
                          file_data,
                          filename=os.path.basename(image_path),
                          content_type='image/jpeg')

        # Send request to the API
        async with session.post(API_ENDPOINT, data=form_data) as response:
            if response.status == 200:
                result = await response.text()
        
                objects, relationships, scene_description = parse_analysis_result(result)
                # Move the processed image
                processed_path = Path(PROCESSED_FOLDER) / os.path.basename(image_path)
                os.rename(image_path, processed_path)

                
                analysis_result = {
                    'image_path': str(processed_path),
                    'objects': json.dumps(objects),
                    'relationships': json.dumps(relationships),
                    'scene_description': scene_description
                }
                
                return analysis_result
            else:
                print(f"Error processing {image_path}: {response.status}")
                return None
                
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None

async def process_images():
    # Create processed images folder if it doesn't exist
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    # Load existing mapping if it exists
    mapping_file = "image_mapping.json"
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r') as f:
            image_mapping = json.load(f)
    else:
        image_mapping = {}

    id_to_name_file = "id_to_name_mapping.json" 
    if os.path.exists(id_to_name_file):
        with open(id_to_name_file, 'r') as f:
            id_to_name = json.load(f)
    else:
        id_to_name = {}  

    

    cur_dataset_size = len(list(Path(PROCESSED_FOLDER).iterdir())) + 1
    # Get list of images to process
    image_files = [
        f for f in Path(IMAGE_FOLDER).iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if len(image_files) == 0:
        print("No images found to process! Maybe you need to run get_dataset.py first")
        return

    # Process images concurrently
    async with aiohttp.ClientSession() as session:
        # Process images one at a time
        for image_path in image_files:
            image_name = os.path.basename(image_path)
            result = await process_single_image(session, str(image_path))
            if not result:
                print(f"Error processing {image_path}")
                return None
            
            image_id = "id" + str(cur_dataset_size)
            add_image_to_db(image_id, result['image_path'], result['objects'], result['scene_description'], image_name, result['relationships'])
            
            # Add to mapping
            image_mapping[image_name] = image_id
            id_to_name[image_id] = image_name
            
            # Save mapping after each image
            with open(mapping_file, 'w') as f:
                json.dump(image_mapping, f, indent=4)
            
            print(cur_dataset_size)
            cur_dataset_size += 1
            sleep(10)
    
    print(f"Processed {cur_dataset_size} images successfully")

if __name__ == "__main__":
    # Add aiofiles to requirements.txt
    asyncio.run(process_images())