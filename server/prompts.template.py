# Template for prompts.py - Copy this file to prompts.py and fill in your prompts
IMAGE_ANALYSIS_PROMPT = """
Analyze this image and extract objects and their relationships. Provide your response in JSON format
with the following fields:
- objects: list of objects in the image
- relationships: list of relationships between objects
- scene_annotation: brief scene description at the end
"""

def get_inference_prompt(scene_context):
    return f"""
    Given this scene context:
    Common objects: {scene_context['common_objects']}
    Typical relationships: {scene_context['typical_relationships']}
    Atypical relationships: {scene_context['atypical_relationships']}

    Generate reasonable inferences about the scene.
    """