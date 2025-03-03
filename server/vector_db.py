#https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide

import chromadb
from transformers import AutoImageProcessor, AutoModel
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction


embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()

client = chromadb.PersistentClient(path="chroma_data")

collection = client.get_or_create_collection("visual_concept",
                                      embedding_function=embedding_function,
    data_loader=data_loader)

processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")

def add_image_to_db(image_id, image_path,image_name, objects_in_image):
    # print(f"Adding image with path: {image_path}")  # Debug print
    collection.add(
        ids=[image_id],
        uris=[image_path], 
        metadatas=[{"objects_in_image": objects_in_image, "image_name": image_name}]
    )

def get_all_images_from_db():
    # Include embeddings in the query
    return collection.get(include=['embeddings', 'metadatas'])

def get_image_from_db(image_id):
    return collection.get(where={"id": image_id})

def delete_image_from_db(image_id):
    return collection.delete(where={"id": image_id})

def delete_all_images_from_db():
    return collection.delete_all()
        