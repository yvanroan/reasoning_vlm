from datasets import load_dataset
import os
from PIL import Image
import io   
from pathlib import Path


def save_dataset_images(output_dir="./images", processed_folder="./processed_images", limit=None):
    
    os.makedirs(output_dir, exist_ok=True)
    
    dataset = load_dataset(path="detection-datasets/coco", split="val", streaming=True)

    #get the number of images in the processed folder because we dont want to overwrite the existing images 
    #in the processed folder (and the chroma db)
    count = len(list(Path(processed_folder).iterdir())) +1
    
    for item in dataset:
        # Get the image
        image = item['image']
        
        filename = f"coco_image_{count}.jpg"
        filepath = os.path.join(output_dir, filename)

        image.save(filepath)
        
        print(f"Saved image {count} to {filepath}")
        
        count += 1
        if limit and count >= limit:
            break


if __name__ == "__main__":
    save_dataset_images(limit=500)