#https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide

import chromadb
from extract_visual import extract_image_features
from transformers import AutoImageProcessor, AutoModel
import torch
from PIL import Image
import numpy as np  # Add numpy import
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction





embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()
# Initialize client and models once
client = chromadb.Client()
collection = client.create_collection("visual_concepts",
                                      embedding_function=embedding_function,
    data_loader=data_loader)
processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")

def add_image_to_db(image_id, image_path, objects_in_image):
    # print("embeddings", embeddings)
    # Store in DB
    collection.add(
        ids=[image_id],
        uris=[image_path], 
        metadatas=[{"image_path": image_path, "objects_in_image": objects_in_image}]
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
        