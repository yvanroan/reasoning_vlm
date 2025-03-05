import aiofiles
import aiohttp
import os
from prompts import get_inference_prompt
from vector_db import get_n_similar_images, get_image_from_db
import json
from ingestion_pipeline import clean_response_string

    
#this shouldn't care about the object labels because they are based on similar images 
# they are likely to have similar objects, so now we focus on the relationships between them
def extract_relationships(image_id, current_relationships, similar_relationships_array):
    """
    Extract and classify relationships as typical or atypical based on comparison with similar images.
    
    Args:
        image_id (str): ID of the current image being analyzed
        current_relationships (list): List of relationship dictionaries from current image
        similar_relationships_array (list): List of tuples (image_id, relationships) from similar images
    
    Returns:
        tuple: (typical_relationships, atypical_relationships)
            - typical_relationships: List of relationships commonly found in similar images
            - atypical_relationships: List of relationships rarely found in similar images
    """
    #i can eventually add a filter for common objects. where i only check for similar
    #relationships between images that have common objects/subjectsto the current scene
    #in this way if a current relationship has no similar relationships, it will be added as an atypical relationship
    
    typical_relationships = []
    atypical_relationships = []
    
    
    for id, similar_relationships in similar_relationships_array:
        if id == image_id:
            continue
        len_similar_relationships = len(similar_relationships)

        for current_rel in current_relationships:
            if current_rel['confidence'] >= 0.8:
                match_count = 0
                current_objects = {current_rel["object"], current_rel["subject"]}
            
                for rel in similar_relationships:
                    similar_objects = {rel["object"], rel["subject"]}

                    if current_objects.intersection(similar_objects) and is_similar_relationship(current_rel, rel):
                        match_count += 1

                
                if match_count/len_similar_relationships >= 0.1: # Due to small dataset, we need to be more lenient
                    typical_relationships.append(current_rel)
                else:
                    atypical_relationships.append(current_rel)
    
    return typical_relationships, atypical_relationships


def is_similar_relationship(rel1, rel2):
    """
    Compare two relationships across multiple dimensions to determine similarity.
    
    Args:
        rel1 (dict): First relationship with spatial, functional, state, contextual dimensions
        rel2 (dict): Second relationship to compare against
    
    Returns:
        bool: True if relationships are similar (share at least one dimension)
    """
    # Compare relationship dimensions with some tolerance
    similarity_score = 0
    dimensions = ['spatial', 'functional', 'state', 'contextual']
    
    for dim in dimensions:
        if rel1[dim] == rel2[dim]:
            similarity_score += 1
    
    return similarity_score >= 1


def get_similar_relationships(image_id, n=5):
    """
    Retrieve relationships from n most similar images based on embeddings.
    
    Args:
        image_id (str): ID of the image to find similar images for
        n (int): Number of similar images to retrieve
    
    Returns:
        list: List of tuples (image_id, relationships) from similar images
    """
    similar_images = get_n_similar_images(image_id, n)
    similar_relationships = []
    
    for id,rels in zip(similar_images["ids"][0], similar_images['metadatas'][0]):

        similar_relationships.append((id,json.loads(rels["relationships"])))

    return similar_relationships


async def generate_inference(scene_context, image_path):
    """
    Generate inferences about a scene based on context and visual analysis.
    
    Args:
        scene_context (dict): Context information including:
            - objects: Dict of objects and their attributes
            - typical_relationships: List of common relationships
            - atypical_relationships: List of unusual relationships
            - scene_type: General description of the scene
        image_path (str): Path to the image file
    
    Returns:
        str: Generated inferences about the scene, including potential past/future events
    """
    try:
        # Read the image file
        async with aiofiles.open(image_path, 'rb') as f:
            file_data = await f.read()
            
        
        prompt = get_inference_prompt(scene_context)
            
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field('image',
                          file_data,
                          filename=os.path.basename(image_path),
                          content_type='image/jpeg')
        
        form_data.add_field('text', 
                    json.dumps({"text": prompt}),  # Send as JSON string
                    content_type='application/json')

        
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:5000/analyze/all", data=form_data) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    return response_text
                else:
                    print(f"Error analyzing image {image_path}: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"Error analyzing image {image_path}: {str(e)}")
        return None



async def analyze_image(image_id):
    """
    Complete image analysis pipeline combining visual analysis, context integration, and inference.
    
    Args:
        image_id (str): ID of the image to analyze
    
    Returns:
        dict: Complete analysis including:
            - objects: Detected objects and attributes
            - relationships: Object relationships in the scene
            - context: Scene context with typical/atypical patterns
            - inferences: Generated insights about the scene
    """
    image_metadata = get_image_from_db(image_id)
    
    objects_str = image_metadata['metadatas'][0]['objects_in_image']
    relationships_str = image_metadata['metadatas'][0]['relationships']
    image_path = image_metadata['uris'][0]

    objects = json.loads(clean_response_string(objects_str))
    relationships = json.loads(clean_response_string(relationships_str))
    
    similar_relationships = get_similar_relationships(image_id)
    # Stage 3: Context integration
    typical_relationships, atypical_relationships = extract_relationships(image_id, relationships, similar_relationships)
    
    scene_context = {
        "objects": objects,
        "typical_relationships": typical_relationships,
        "atypical_relationships": atypical_relationships,
        "scene_type": image_metadata['metadatas'][0]['description']
    }

    # Stage 4: Generate inferences
    inferences = await generate_inference(scene_context, image_path)
    
    print("image_path from analyze_image in context_integration.py", image_path)

    return {
        "objects": objects,
        "relationships": relationships,
        "context": scene_context,
        "inferences": inferences
    }

if __name__ == "__main__":
    import asyncio
    
    async def test():
        result = await analyze_image("id51")
        if result:
            print(result)
            
        else:
            print("Analysis failed")
    
    asyncio.run(test())