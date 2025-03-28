#https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide

import chromadb
from transformers import AutoImageProcessor, AutoModel
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
import json



embedding_function = OpenCLIPEmbeddingFunction()

data_loader = ImageLoader()

client = chromadb.PersistentClient(path="chroma_data")

collection = client.get_or_create_collection(
    "visual_concept",
    embedding_function=embedding_function,
    data_loader=data_loader
)

feedback_collection = client.get_or_create_collection(
    "feedback"
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


def add_feedback_to_db(feedback_id, text, metadata):
    '''
    Add feedback to the feedback collection in ChromaDB
    
    Args:
        feedback_id (str): Unique ID for this feedback
        text (str): Text of the inference for embedding
        metadata (dict): Metadata including image_id, inference, rating
    '''
    try:
        feedback_collection.upsert(
            ids=[feedback_id],
            documents=[text if text else ""],
            metadatas=[metadata]
        )
        return True
    except Exception as e:
        print(f"Error adding feedback to DB: {e}")
        return False

def get_feedback_by_relationships(feedback_id,relationship_keys, limit=3):
    """
    Find feedback entries that match specific relationship patterns
    
    Args:
        relationship_keys (list): List of relationship key strings (e.g., "cup-on-table")
        limit (int): Maximum number of results to return
    """
    try:
        all_results = []
        seen_ids = set()
        seen_image_ids = set()
        seen_relationships = set()
        seen_ids.add(feedback_id)
        
        # First try the simplest approach - get all feedback with high ratings
        all_feedback = feedback_collection.get(
            where={"rating": {"$gte": 0.5}}
        )
        
        if not all_feedback or 'ids' not in all_feedback or not all_feedback['ids']:
            return {"ids": [[]], "metadatas": [[]]}
            
        # Then manually filter for relationship matches
        for i, metadata in enumerate(all_feedback['metadatas']):
            feedback_id = all_feedback['ids'][i]
            image_id = metadata.get("image_id", "")
            
            # Skip if we've already seen this ID
            if feedback_id in seen_ids:
                continue

            if image_id in seen_image_ids:
                continue
                
            for field in ["atypical_relationships", "typical_relationships"]:
                field_data = metadata.get(field, "")

                if image_id in seen_image_ids or field_data == "":
                    break
                    
                # Parse the JSON string into a list of dictionaries
                try:
                    field_data = json.loads(field_data)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON for {field}: {field_data}", flush=True)
                    continue
                    
                for key in relationship_keys:
                    subject, spatial, state, functional, contextual, obj = key.split("-")

                    if image_id in seen_image_ids:
                        break
                    
                    # If all three components are in the field data, consider it a match
                    for data in field_data:
                        

                        if (
                            (subject in data['subject'] or subject in data['object']) and
                            (
                                spatial in data['spatial'] or
                                state in data['state'] or
                                functional in data['functional'] or
                                contextual in data['contextual']
                            ) and
                            (obj in data['object'] or obj in data['subject'])
                        ):
                            seen_ids.add(feedback_id)
                            seen_image_ids.add(image_id)
                            all_results.append((feedback_id, metadata))
                            break  # Move to next ID after finding a match
        
        # Format results to match ChromaDB's return format
        if not all_results:
            return {"ids": [[]], "metadatas": [[]]}
        
        # Limit results
        all_results = all_results[:limit]
        result_ids = [r[0] for r in all_results]
        
        result_metadatas = [r[1] for r in all_results]
        
        return {
            "ids": [result_ids],
            "metadatas": [result_metadatas]
        }
    except Exception as e:
        print(f"Error in get_feedback_by_relationships: {e}")
        return {"ids": [[]], "metadatas": [[]]}


def get_similar_feedback(query_text, limit=3):
    '''
    Get similar feedback using text similarity
    
    Args:
        query_text (str): Text to match against
        limit (int): Maximum number of results
    '''
    try:
        results = feedback_collection.query(
            query_texts=[query_text],
            n_results=limit,
            where={"rating": {"$gte": 0.5}}
        )

        return results
    
    except Exception as e:
        print(f"Error getting similar feedback: {e}")
        return {"ids": [[]], "metadatas": [[]]}

def delete_feedback_collection():
    feedback_collection.delete(where={})