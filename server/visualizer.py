from sklearn.manifold import TSNE
from vector_db import get_all_images_from_db
import plotly.express as px
import matplotlib.pyplot as plt
import pandas as pd

def display_image():
    db_results = get_all_images_from_db()
    
    if not db_results or 'embeddings' not in db_results:
        print("No embeddings found in database")
        return
    
    embeddings = db_results['embeddings']
    metadata = db_results['metadatas']
    ids = db_results['ids']
    if len(embeddings) == 0:
        print("No embeddings to visualize")
        return

    # Reduce to 2D
    tsne = TSNE(n_components=2, perplexity=3) #perplexity has to be  less than the number of embeddings
    reduced_embeddings = tsne.fit_transform(embeddings)

    df = pd.DataFrame({
        'x': reduced_embeddings[:, 0],
        'y': reduced_embeddings[:, 1],
        'id': ids,
        'image_name': [m['image_name'] for m in metadata],
        'objects': [m['objects_in_image'] for m in metadata]
    })

    fig = px.scatter(
        data_frame=df,
        x='x',
        y='y',
        hover_data=['id', 'image_name', 'objects'],
        title='t-SNE Visualization of Image Embeddings'
    )
    fig.show()

if __name__ == "__main__":
    display_image() 