i use 228 image as bootstrap for the feedback loop.
and the rest of the images are used for testing.

it seems like the gemini api is able to memorize previous prompts and would generate similar inferences 
if the prompts are close enough even if they format is not the same.

cursor has very small issues with putting togetter functions. sometimes it jsut hallucinates, which is normal.

when you make a call, after a long time the generation gets worse.

kind of feedback that you shoudld provide:

Specificity of relationships: "I appreciate how the enhanced inference recognized the relationship between the candle and reflective surfaces and how they work together to create an effect."

Causal connections: "The connection between the unlit state of the candle and the inference about 'recently prepared' or 'will light soon' is insightful."

: "The enhanced inference's mention of 'self-care ritual' shows good understanding of how these objects typically function together."

Novel insights: "I'd like more insight into why certain objects were positioned in relation to others - for example, why the vase is next to the candle rather than elsewhere."

examples: 
This analysis shows strong causal connections by linking the illuminated phone screen to recent usage and explaining the positioning as a deliberate user action. The context understanding is excellent, correctly identifying the Walkman branding and connecting it to music functionality. However, it could be improved with more specificity about the unique relationships between interface elements (like the arrangement of playback controls and how they relate to the screen display). The analysis lacks novel insights that go beyond obvious observations—consider what the specific arrangement of controls or the interface design reveals about user experience or interaction patterns that aren't immediately apparent.


to do:
change the workflow of the front end so that we get the basic inference first, the user rates and submit feedback, then we use that feedback to generate the enhanced inference.

make sure that the inference/enhanced inference endpoint is used after the user has rated the basic inference.

show the user the reasoing pattern behind the enhanced inference.

also mention the type of feedback that you want the user to provide.