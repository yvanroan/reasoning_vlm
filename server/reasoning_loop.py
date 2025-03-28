import json
from datetime import datetime
from vector_db import add_feedback_to_db, get_feedback_by_relationships, get_similar_feedback, get_image_from_db
from context_integration import generate_inference
import sys
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_inference_feedback(image_id, inference, scene_context, rating):
    """
    Store user feedback about an inference for future learning.
    
    Args:
        image_id (str): ID of the image
        inference (str): The inference text that received feedback
        scene_context (dict): The scene context (objects, relationships, etc.)
        rating (float): User rating from 0.0 to 1.0
        
    Returns:
        bool: Success status
    """
    

    # Only store positive feedback (ratings > 0.5)
    if rating <= 0.5:
        return False
        
    # Create a unique feedback ID with timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    feedback_id = f"feedback_{image_id}_{timestamp}"
    
    # Extract relationship keys for easier searching
    relationship_keys = extract_relationship_keys(scene_context)
    
    # Create document text combining inference and context
    document_text = f"{inference} {scene_context.get('scene_type', '')}"
    
    # Prepare metadata
    metadata = {
            "image_id": image_id,
            "inference": inference if isinstance(inference, str) else json.dumps(inference),
            "rating": rating,
            "timestamp": datetime.now().isoformat(),
            "scene_type": scene_context.get("scene_type", ""),
            "relationship_keys": json.dumps(relationship_keys),
            "typical_relationships": json.dumps(scene_context.get("typical_relationships", [])),
            "atypical_relationships": json.dumps(scene_context.get("atypical_relationships", []))
    }
    
    # Store in feedback collection
    add_feedback_to_db(feedback_id, document_text, metadata)
    print(f"Stored feedback with ID: {feedback_id}", flush=True)
    return feedback_id



def extract_relationship_keys(scene_context):
    """
    Extract searchable relationship keys from scene context.
    
    Args:
        scene_context (dict): The scene context with relationships
        
    Returns:
        list: List of relationship keys in "subject-spatial-object" format
    """
    keys = set()

    # Focus primarily on atypical relationships as they're most informative
    for rel in scene_context.get("atypical_relationships", []):
        if all(k in rel for k in ["subject", "spatial", "object"]):
            key = f"{rel['subject']}-{rel['spatial']}-{rel['state']}-{rel['functional']}-{rel['contextual']}-{rel['object']}"
            keys.add(key)
    
    # Also include typical relationships as fallback
    if len(keys) <= 2:
        i = len(keys)
        for rel in scene_context.get("typical_relationships", []):
            if i >= 5:
                break
        
            if all(k in rel for k in ["subject", "spatial", "object"]):
                key = f"{rel['subject']}-{rel['spatial']}-{rel['state']}-{rel['functional']}-{rel['contextual']}-{rel['object']}"
                if key not in keys:
                    keys.add(key)
                    i+=1
    return list(keys)

def find_relevant_inference_patterns(feedback_id,scene_context, limit=5):
    """
    Find relevant inference patterns based on relationship structures.
        
    Args:
        feedback_id (str): ID of the feedback entry
        scene_context (dict): Current scene context
        limit (int): Maximum number of patterns to return
            
        Returns:
        list: Relevant inference patterns from past analyses
    """
    print("Starting find_relevant_inference_patterns", flush=True)
    
    # Extract relationship keys from the current scene
    relationship_keys = extract_relationship_keys(scene_context)
    print(f"=== Relationship Keys we are looking for ===\n{relationship_keys}\n========================", flush=True)
    
    # If we have relationship keys, search by relationship structure first
    patterns = []
    if relationship_keys:
        rel_results = get_feedback_by_relationships(feedback_id,relationship_keys, limit)
        # print(f"=== Relationship Results ===\n{rel_results}\n==========================", flush=True)
        patterns = extract_patterns_from_results(rel_results)
        print(f"Found {len(patterns)} patterns from relationships", flush=True)

    # If we didn't find enough patterns by relationships, supplement with text similarity
    if len(patterns) < limit:
        remaining = limit - len(patterns)
        text_results = get_similar_feedback(scene_context.get("scene_type", ""), remaining)
        text_patterns = extract_patterns_from_results(text_results)
        
        # Add only patterns we haven't already included
        existing_inferences = {p.get("inference") for p in patterns}
        for pattern in text_patterns:
            if pattern.get("inference") not in existing_inferences:
                patterns.append(pattern)
                if len(patterns) >= limit:
                    break


    for pattern in patterns:
        if pattern.get('typical_relationships'):
            # Create a dictionary with (subject, spatial, object) tuple as key
            unique_typical = {
                (rel['subject'], rel['spatial'], rel['object']): rel 
                for rel in pattern['typical_relationships']
            }
            # Replace with deduplicated list
            pattern['typical_relationships'] = list(unique_typical.values())
            
        if pattern.get('atypical_relationships'):
            # Create a dictionary with (subject, spatial, object) tuple as key
            unique_atypical = {
                (rel['subject'], rel['spatial'], rel['object']): rel 
                for rel in pattern['atypical_relationships']
            }
            # Replace with deduplicated list
            pattern['atypical_relationships'] = list(unique_atypical.values())
    


    # print("patterns", patterns, flush=True)
    return patterns, relationship_keys

def extract_patterns_from_results(results):
    """
    Extract clean pattern objects from ChromaDB results.
    
    Args:
        results (dict): ChromaDB results with metadatas
        
    Returns:
        list: Cleaned pattern objects
    """
    patterns = []
    
    if not results or 'metadatas' not in results or not results['metadatas'][0]:
        return patterns
        
    for metadata in results['metadatas'][0]:
        try:
            # Get inference text
            inference = metadata.get("inference", "")
            if not inference:
                inference = metadata.get("item", "")
                print(f"No inference found for {metadata.get('image_id', 'unknown')}")
                
            # Parse JSON strings if needed
            typical_rels = metadata.get("typical_relationships", "[]")
            if isinstance(typical_rels, str):
                typical_rels = json.loads(typical_rels)
                
            atypical_rels = metadata.get("atypical_relationships", "[]")
            if isinstance(atypical_rels, str):
                atypical_rels = json.loads(atypical_rels)

            image_id = metadata.get("image_id", "")
            image_metadata = get_image_from_db(image_id)
            image_name = image_metadata.get("metadatas", [{}])[0].get("image_name", "")
            
            # Create pattern object
            pattern = {
                "image_name": image_name,
                "inference": inference,
                "scene_type": metadata.get("scene_type", ""),
                "typical_relationships": typical_rels,
                "atypical_relationships": atypical_rels,
                "rating": float(metadata.get("rating", 0.5))
            }
            patterns.append(pattern)
        except Exception as e:
            print(f"Error extracting pattern: {e}")
            continue
            
    return patterns

def format_relationship_summary(relationship):
    """
    Create a human-readable summary of a relationship.
    
    Args:
        relationship (dict): Relationship dictionary
        
    Returns:
        str: Human-readable description
    """
    if not relationship:
        return "certain relationship"
        
    subject = relationship.get("subject", "object")
    spatial = relationship.get("spatial", "positioned")
    obj = relationship.get("object", "location")
    
    return f"{subject}-{spatial}-{obj}"

def create_enhanced_prompt(feedback_id,scene_context):
    """
    Create an enhanced prompt with learned inference patterns.
    
    Args:
        feedback_id (str): ID of the feedback entry
        scene_context (dict): Current scene context
        
    Returns:
        str: Enhanced prompt for inference generation
    """
    # Start with base prompt
    prompt = f"""
    Given this scene context:
    Objects: {scene_context.get('objects', {})}
    Typical relationships: {scene_context.get('typical_relationships', [])}
    Atypical relationships: {scene_context.get('atypical_relationships', [])}
    Scene description: {scene_context.get('scene_type', '')}

    Focus especially on the atypical relationships, as these often indicate meaningful deviations from expected patterns.
    """
    
    # Find relevant patterns from past successful analyses
    relevant_patterns, relationship_keys = find_relevant_inference_patterns(feedback_id,scene_context)
    


    # Add patterns to prompt if we found any
    if relevant_patterns:
        prompt += "\n\nBased on similar relationship patterns that were successfully analyzed before:"
        
        for pattern in relevant_patterns:
            # Get inference text
            inference_text = pattern.get("inference", "")
            if not isinstance(inference_text, str):
                inference_text = str(inference_text)
            
            # Create a preview of the inference
            words = inference_text.split()
            preview = " ".join(words[:min(10, len(words))]) + "..."
            
            # Get the key relationship that defined this pattern
            relationship_summary = "certain relationships"
            if pattern.get("atypical_relationships"):
                relationship_summary = format_relationship_summary(pattern["atypical_relationships"][0])
            elif pattern.get("typical_relationships"):
                relationship_summary = format_relationship_summary(pattern["typical_relationships"][0])
                
            # Add to prompt
            prompt += f"\n- When analyzing a scene with {relationship_summary}, a useful inference was: \"{preview}\""
            
        prompt += "\n\nConsider whether similar reasoning might apply to this scene."
    
    # Add standard inference request
    prompt += """
    
    Generate 3 descriptive sentences of the scene using questions like  but not limited to:
    1. Why objects might be arranged this way, particularly explaining any atypical relationships
    2. What might have happened before this scene based on object positions and states
    3. What might happen next given the current arrangement
    4. Any implied human activities or intentions suggested by the scene

    just output the 3 sentences along with your reasoning based on the visual evidence.
    """
    
    return prompt, relevant_patterns, relationship_keys

async def generate_enhanced_inference(feedback_id, scene_context, image_path):
    """
    Generate inferences with few-shot learning enhancement.
    
    Args:
        feedback_id (str): ID of the feedback entrys
        scene_context (dict): Scene context with objects and relationships
        image_path (str): Path to the image file
        generate_function (function): Async function that generates inferences given prompt and image path
        
    Returns:
        str: Generated inferences
    """

    # Create enhanced prompt with learned patterns
    enhanced_prompt, relevant_patterns, relationship_keys = create_enhanced_prompt(feedback_id,scene_context)
    
    
    # Call the provided generation function
    return await generate_inference(enhanced_prompt, image_path), relevant_patterns, relationship_keys