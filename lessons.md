i use 228 image as bootstrap for the feedback loop.
and the rest of the images are used for testing.

it seems like the gemini api is able to memorize previous prompts and would generate similar inferences 
if the prompts are close enough even if they format is not the same.

cursor has very small issues with putting togetter functions. sometimes it jsut hallucinates, which is normal.

when you make a call, after a long time the generation gets worse.

kind of feedback that you shoudld provide:

the text feedback isn't important as it is too laborious the rating is good enough.


to do:
change the workflow of the front end so that we get the basic inference first, the user rates and submit feedback, then we use that feedback to generate the enhanced inference.

make sure that the inference/enhanced inference endpoint is used after the user has rated the basic inference.

show the user the reasoing pattern behind the enhanced inference.

also mention the type of feedback that you want the user to provide.




when you abuse on using gemini, it gets dumber. e.g:
it's assuming that every image must have a coffee mug or desk
"
Raw response: I am unable to analyze objects and their relationships as there is no coffee mug or desk in the image.
Error parsing analysis result for images/x.jpg: parse_analysis_result failed to parse objects, relationships and scene_description
Raw response: "I am unable to analyze objects and their relationships as there is no coffee mug or desk in the image."
Error ingesting image: 'NoneType' object is not subscriptable
Error in basic inference: Expected ID to be a str, got None in get.
Full error details: Expected ID to be a str, got None in get.
"