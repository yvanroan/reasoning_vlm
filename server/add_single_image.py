from vector_db import add_image_to_db, get_all_images_from_db
from visualizer import display_image

def add_single_image():
    # Path to the image
    image_path = "./images/kodim01.jpeg"
    image_path2 = "./images/kodim02.jpeg"
    image_path3 = "./images/kodim03.jpeg"
    image_path4 = "./images/kodim04.jpeg"
    
    # Generate a unique ID for the image
    image_id = "id0"
    image_id2 = "id1"
    image_id3 = "id2"
    image_id4 = "id3"
    
    # For this example, we'll just use an empty list for objects_in_image
    # You might want to replace this with actual object detection results
    objects_in_image = "test"
    
    # Add the image to the database
    add_image_to_db(image_id, image_path, objects_in_image)
    add_image_to_db(image_id2, image_path2, objects_in_image)
    add_image_to_db(image_id3, image_path3, objects_in_image)
    add_image_to_db(image_id4, image_path4, objects_in_image)
    print(f"Added image {image_path} with ID: {image_id}")

def display_db():
    db_results = get_all_images_from_db()
    print("Got results from DB:", bool(db_results))  # Debug print
    display_image(db_results)

if __name__ == "__main__":
    add_single_image() 
    display_db()