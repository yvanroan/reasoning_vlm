import networkx as nx
import spacy
from context_integration import analyze_image
import plotly.graph_objects as go
import plotly.express as px

# Initialize global dependencies
nlp = spacy.load("en_core_web_sm")

def build_scene_graph(scene_analysis):
    """
    Convert scene analysis into a knowledge graph
    
    Args:
        scene_analysis (dict): Analysis containing objects, relationships and context
    
    Returns:
        nx.DiGraph: Directed graph representing the scene
    """
    graph = nx.DiGraph()
    
    # Add nodes for objects
    for obj_name, att in scene_analysis['objects'].items():
        graph.add_node(obj_name, type='object', properties=att)
    
    # Add relationship edges
    for rel in scene_analysis['relationships']:
        graph.add_edge(
            rel['subject'],
            rel['object'],
            relation=(rel['spatial'], rel['functional'], rel['state'])
        )
    
    return graph

def find_implied_relations(graph):
    """
    Discovers indirect relationships between objects in a scene that aren't directly connected.
    For example, if a cup and a book are both on the same table, this function will identify
    their shared relationship through the table.
    
    Args:
        graph (nx.DiGraph): Scene knowledge graph where:
            - Nodes represent objects in the scene
            - Edges represent direct relationships between objects
    
    Returns:
        list: List of dictionaries containing implied relationships, where each dictionary has:
            - source: The first object
            - target: The second object
            - implied_by: List of paths showing how the objects are indirectly connected
    """
    implied_relations = []
    
    nodes = list(graph.nodes())
    for i, source in enumerate(nodes):
        for target in nodes[i+1:]: 
            
            if graph.has_edge(source, target) or graph.has_edge(target, source):
                continue
                
            # Find all paths of length 2 between the nodes
            paths = list(nx.all_simple_paths(graph, source, target, cutoff=2))
            if paths:
                indirect_paths = [path for path in paths if len(path) == 3]
                if indirect_paths:
                    implied_relations.append({
                        'source': source,
                        'target': target,
                        'implied_by': indirect_paths
                    })
    
    return implied_relations

def reason_over_graph(graph):
    """
    Analyzes the scene by breaking it down into logical groups of connected objects
    (like items in the same room) and finding hidden relationships within each group.
    This makes complex scenes more manageable by focusing on related objects together.
    
    Args:
        graph (nx.DiGraph): Scene knowledge graph where:
            - Nodes represent objects in the scene
            - Edges represent relationships between objects
    
    Returns:
        list: Analysis results for each group of connected objects, where each result contains:
            - component: Set of objects that are connected to each other
            - implied_relations: Hidden relationships discovered between objects in this group
    """
    components = list(nx.weakly_connected_components(graph))
    reasoning_results = []
    
    for component in components:
        subgraph = graph.subgraph(component)
        implied_relations = find_implied_relations(subgraph)
        reasoning_results.append({
            'component': component,
            'implied_relations': implied_relations
        })
    
    return reasoning_results

def visualize_scene_graph(graph):
    """
    Visualize the knowledge graph using Plotly for browser display
    
    Args:
        graph (nx.DiGraph): Scene knowledge graph
    """
    # Get node positions using networkx spring layout
    pos = nx.spring_layout(graph)
    
    # Create edge traces with annotations
    edge_x = []
    edge_y = []
    edge_text = []
    annotations = []
    
    for edge in graph.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
        # Calculate midpoint for edge label
        mid_x = (x0 + x1) / 2
        mid_y = (y0 + y1) / 2
        
        # Add edge relationship as annotation
        annotations.append(dict(
            x=mid_x,
            y=mid_y,
            xref='x',
            yref='y',
            text=str(edge[2]['relation']),
            showarrow=False,
            font=dict(
                size=12,
                color='#E74C3C',  # Red text for relationships
                family="Arial"
            ),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#BDC3C7',
            borderwidth=1,
            borderpad=4
        ))
        
        edge_text.append(f"{edge[0]} -> {edge[1]}<br>{edge[2]['relation']}")
    
    edges_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#2C3E50'),  # Darker, thicker lines
        hoverinfo='text',
        text=edge_text,
        mode='lines'
    )
    
    # Create node traces with updated styling
    nodes_trace = go.Scatter(
        x=[pos[node][0] for node in graph.nodes()],
        y=[pos[node][1] for node in graph.nodes()],
        mode='markers+text',
        text=[node for node in graph.nodes()],
        textposition="top center",
        hoverinfo='text',
        hovertext=[f"Properties: {', '.join(graph.nodes[node].get('properties', []))}" 
                  for node in graph.nodes()],
        marker=dict(
            showscale=False,
            size=25,
            line_width=2,
            color='#3498DB',
            line=dict(color='#2980B9')
        ),
        textfont=dict(
            size=16,  # Increased font size
            color='#E74C3C',  # Matching color with edge text
            family="Arial"
        )
    )
    
    # Create the figure with updated layout
    fig = go.Figure(
        data=[edges_trace, nodes_trace],
        layout=go.Layout(
            title=dict(
                text='Scene Knowledge Graph',
                font=dict(size=20, color='#2C3E50', family="Arial"),
                x=0.5
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=annotations,
            plot_bgcolor='rgba(240,248,255,0.8)',  # Light blue background
            paper_bgcolor='rgba(240,248,255,0.8)'  # Light blue background
        )
    )
    
    fig.show()

async def process_scene(image_id):
    """
    Process a scene through the complete pipeline
    
    Args:
        image_id (str): ID of the image to analyze
    
    Returns:
        dict: Complete analysis with graph and reasoning
    """
    # Get scene analysis from existing pipeline
    scene_analysis = await analyze_image(image_id)
    
    # Build and analyze knowledge graph
    graph = build_scene_graph(scene_analysis)
    print(graph.nodes(data=True))
    reasoning_results = reason_over_graph(graph)
    print(reasoning_results)
    # Visualize if needed
    visualize_scene_graph(graph)
    
    return {
        'graph': graph,
        'reasoning': reasoning_results,
        'analysis': scene_analysis
    }

if __name__ == "__main__":
    import asyncio

    asyncio.run(process_scene("id51"))