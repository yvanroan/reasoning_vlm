IMAGE_ANALYSIS_PROMPT = """
            Analyze this image and extract objects and their relationships. Provide your response in the following JSON format:

            {
                "objects": [
                    {"label": "coffee mug", "attributes": ["white", "ceramic", "full"]},
                    {"label": "desk", "attributes": ["wooden", "office"]}
                ],
                "relationships": [
                    {
                        "subject": "coffee mug",
                        "object": "desk",
                        "spatial": "on edge of",
                        "functional": "on",
                        "state": "unstable position", // state of the subject relative to the object
                        "contextual": "atypical", // could be atypical, typical
                        "confidence": 0.95
                    }
                ],
                "scene_annotation": "Office workspace with interrupted activity"
            }

            Important: 
            Include spatial relationships limited to: on top of, in, on, under, inside, above, below, next to, near, far from, in front of, behind, contains, within, on the edge of, between, in the middle of.
            functional relationships is up to you to determine based on the image.
            state relationships limited to: stable, unstable, moving, stationary, open, closed, empty, full, secure, loose, flat, tilted, resting, hanging, level, uneven, grounded, suspended, confined, free, attached, detached, aligned, misaligned.
            contextual relationships limited to: atypical, typical.
            confidence score between 0 and 1 on how confident you are about the relationship.
            scene_annotation is a brief scene description at the end.
            """

def get_context_integration_prompt(scene_context):
    return f"""
    Given this scene context:
    Common objects: {scene_context['objects']}
    Typical relationships: {scene_context['typical_relationships']}
    Atypical relationships: {scene_context['atypical_relationships']}
    Scene type: {scene_context['scene_type']}
    Common scene elements: {scene_context.get('common_scene_elements', [])}
    Similar scene categories: {scene_context.get('similar_scene_types', [])}

    Focus especially on the atypical relationships, as these often indicate meaningful deviations from expected patterns.

    Consider the common elements found across similar scenes to inform your understanding of what is normal for this type of scene.

    Generate 3 descriptive sentences of the scene using questions like  but not limited to:
    1. Why objects might be arranged this way, particularly explaining any atypical relationships
    2. What might have happened before this scene based on object positions and states
    3. What might happen next given the current arrangement
    4. Any implied human activities or intentions suggested by the scene

    only output the 3 sentences along with your reasoning based on the visual evidence.
    """

