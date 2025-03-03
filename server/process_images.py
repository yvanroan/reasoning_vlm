import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from vector_db import add_image_to_db

# Configuration
IMAGE_FOLDER = "images"  # Change this to your image folder path
PROCESSED_FOLDER = "processed_images"  # Folder to move processed images
API_ENDPOINT = "http://localhost:5000/analyze/image"
SUPPORTED_FORMATS = {'.jpg', '.jpeg'}

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
        
                
                # Move the processed image
                processed_path = Path(PROCESSED_FOLDER) / os.path.basename(image_path)
                os.rename(image_path, processed_path)

                analysis_result = {
                    'image_name': os.path.basename(image_path),
                    'result': result
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
    
    # Get list of images to process
    image_files = [
        f for f in Path(IMAGE_FOLDER).iterdir()
        if f.suffix.lower() in SUPPORTED_FORMATS
    ]
    
    if not image_files:
        print("No images found to process!")
        return
    
    results = []
    i=1
    # Process images concurrently
    async with aiohttp.ClientSession() as session:
        # Process images one at a time
        for image_path in image_files:
            result = await process_single_image(session, str(image_path))
            if result:
                # add_image_to_db("id"+str(i), result['image_name'], result['result'])
                results.append(result)
                i+=1
            else:
                print(i)
                print(f"Error processing {image_path}")
                return None
    
    
    print(f"Processed {len(results)} images successfully")

if __name__ == "__main__":
    # Add aiofiles to requirements.txt
    asyncio.run(process_images())