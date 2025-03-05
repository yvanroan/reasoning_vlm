#https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide

import chromadb
from transformers import AutoImageProcessor, AutoModel
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction


embedding_function = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()

client = chromadb.PersistentClient(path="chroma_data")

collection = client.get_or_create_collection(
    "visual_concept",
    embedding_function=embedding_function,
    data_loader=data_loader
)

processor = AutoImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")

def add_image_to_db(image_id, image_path, objects_in_image, description, image_name, relationships):
    collection.add(
        ids=[image_id],
        uris=[image_path], 
        metadatas=[{"objects_in_image": objects_in_image, "description": description, "image_name": image_name, "relationships": relationships }]
    )

def get_all_images_from_db():
    return collection.get(include=['embeddings', 'metadatas'])

def get_image_from_db(image_id):
    return collection.get(ids=[image_id], include=['uris', 'metadatas'])

def delete_image_from_db(image_id):
    collection.delete(ids=[image_id])

def delete_all_images_from_db():
    collection.delete_all()

def get_n_similar_images(image_id, n):
    """
    Get similar images based on the entity graph
    """
    obj = collection.get(ids=[image_id], include=['embeddings'])
    
    similar_images = collection.query(
        query_embeddings=obj['embeddings'],
        include=['metadatas'],
        n_results=n
    )
    
    return similar_images
        