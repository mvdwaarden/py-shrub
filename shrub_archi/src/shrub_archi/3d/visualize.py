import dash
from dash import dcc, html, Input, Output, ALL
import plotly.graph_objects as go
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
import re
import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass


def example_dotty():
    return """
      node BakerStreet [pos="0.15,0.2,0.5",shape=sphere,color=brown,size=8];
    node RegentPark [pos="0.25,0.2,0.5",shape=sphere,color=brown,size=8];
    node OxfordCircus [pos="0.35,0.2,0.5",shape=sphere,color=red,size=8];
    node PiccadillyCircus [pos="0.45,0.2,0.5",shape=sphere,color=blue,size=8];
    node LeicesterSquare [pos="0.55,0.2,0.5",shape=sphere,color=blue,size=8];
    node CoventGarden [pos="0.65,0.2,0.5",shape=sphere,color=blue,size=8];
    node TottenhamCourtRoad [pos="0.25,0.3,0.5",shape=sphere,ccolor=yellow,size=8];
    node ChanceryLane [pos="0.35,0.3,0.5",shape=sphere,ccolor=yellow,size=8];
    node Holborn [pos="0.45,0.3,0.5",shape=sphere,ccolor=yellow,size=8];
    node StPauls [pos="0.55,0.3,0.5",shape=sphere,ccolor=yellow,size=8];
    node Bank [pos="0.55,0.4,0.5",shape=sphere,color=yellow,size=8];
    node Monument [pos="0.65,0.4,0.5",shape=sphere,color=yellow,size=8];
    node LondonBridge [pos="0.75,0.4,0.5",shape=sphere,color=yellow,size=8];
    node CanaryWharf [pos="0.85,0.4,0.5",shape=sphere,color=yellow,size=8];
    node CanadaWater [pos="0.75,0.5,0.5",shape=sphere,color=yellow,size=8];
    node Bermondsey [pos="0.65,0.5,0.5",shape=sphere,color=yellow,size=8];
    node Waterloo [pos="0.45,0.4,0.5",shape=sphere,color=yellow,size=8];
    node Embankment [pos="0.35,0.4,0.5",shape=sphere,color=yellow,size=8];
    node Westminster [pos="0.25,0.4,0.5",shape=sphere,color=yellow,size=8];
    node GreenPark [pos="0.15,0.4,0.5",shape=sphere,color=yellow,size=8];
    node HydeParkCorner [pos="0.15,0.5,0.5",shape=sphere,color=yellow,size=8];
    node Knightsbridge [pos="0.15,0.6,0.5",shape=sphere,color=yellow,size=8];
    node SouthKensington [pos="0.15,0.7,0.5",shape=sphere,color=yellow,size=8];
    node SloaneSquare [pos="0.15,0.8,0.5",shape=sphere,color=yellow,size=8];
    node Victoria [pos="0.25,0.5,0.5",shape=sphere,color=red,size=8];
    node Pimlico [pos="0.25,0.6,0.5",shape=sphere,color=red,size=8];
    node Vauxhall [pos="0.25,0.7,0.5",shape=sphere,color=red,size=8];
    node Stockwell [pos="0.25,0.8,0.5",shape=sphere,color=red,size=8];
    node ElephantCastle [pos="0.25,0.9,0.5",shape=sphere,color=green,size=8];
    node Kennington [pos="0.35,0.9,0.5",shape=sphere,color=green,size=8];
    node Oval [pos="0.45,0.9,0.5",shape=sphere,color=green,size=8];
    node ClaphamNorth [pos="0.55,0.9,0.5",shape=sphere,color=green,size=8];
    node ClaphamCommon [pos="0.65,0.9,0.5",shape=sphere,color=green,size=8];
    node ClaphamSouth [pos="0.75,0.9,0.5",shape=sphere,color=green,size=8];
    node Balham [pos="0.85,0.9,0.5",shape=sphere,color=green,size=8];
    node TootingBec [pos="0.85,0.8,0.5",shape=sphere,color=green,size=8];
    node TootingBroadway [pos="0.85,0.7,0.5",shape=sphere,color=green,size=8];

    # Bakerloo Line (brown)
    BakerStreet -- RegentPark [type=solid,color=brown,width=2];
    RegentPark -- OxfordCircus [type=solid,color=brown,width=2];

    # Central Line (red)
    OxfordCircus -- TottenhamCourtRoad [type=solid,color=red,width=2];
    TottenhamCourtRoad -- ChanceryLane [type=solid,color=red,width=2];
    ChanceryLane -- Holborn [type=solid,color=red,width=2];
    Holborn -- TottenhamCourtRoad [type=solid,color=red,width=2];
    Holborn -- TottenhamCourtRoad [type=solid,color=red,width=2];

    # Piccadilly Line (blue)
    GreenPark -- HydeParkCorner [type=solid,color=blue,width=2];
    HydeParkCorner -- Knightsbridge [type=solid,color=blue,width=2];
    Knightsbridge -- SouthKensington [type=solid,color=blue,width=2];
    SouthKensington -- SloaneSquare [type=solid,color=blue,width=2];

    # Jubilee Line (grey)
    Westminster -- Waterloo [type=solid,color=yellow,width=2];
    Waterloo -- LondonBridge [type=solid,color=yellow,width=2];
    LondonBridge -- Bermondsey [type=solid,color=yellow,width=2];
    Bermondsey -- CanadaWater [type=solid,color=yellow,width=2];
    CanadaWater -- CanaryWharf [type=solid,color=yellow,width=2];
    CanaryWharf -- CanadaWater [type=solid,color=yellow,width=2];

    # Victoria Line (lightblue)
    Victoria -- Pimlico [type=solid,color=lightblue,width=2];
    Pimlico -- Vauxhall [type=solid,color=lightblue,width=2];
    Vauxhall -- Stockwell [type=solid,color=lightblue,width=2];

    # Northern Line (black)
    ElephantCastle -- Kennington [type=solid,color=black,width=2];
    Kennington -- Oval [type=solid,color=black,width=2];
    Oval -- ClaphamNorth [type=solid,color=black,width=2];
    ClaphamNorth -- ClaphamCommon [type=solid,color=black,width=2];
    ClaphamCommon -- ClaphamSouth [type=solid,color=black,width=2];
    ClaphamSouth -- Balham [type=solid,color=black,width=2];
    Balham -- TootingBec [type=solid,color=black,width=2];
    TootingBec -- TootingBroadway [type=solid,color=black,width=2];
  
    
    """
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Data Classes ---
@dataclass
class Node:
    name: str
    pos: List[float]
    shape: str
    color: str
    size: int

@dataclass
class Edge:
    source: str
    target: str
    type: str
    color: str
    width: int

# --- Styles ---
SIDEBAR_STYLE = {
    'resize': 'horizontal',
    'overflow': 'auto',
    'minWidth': '180px',
    'maxWidth': '600px',
    'width': '300px',
    'background': '#f8f8ff',
    'padding': '20px',
    'borderRadius': '12px',
    'boxShadow': '0 2px 8px #ddd',
    'maxHeight': '100vh'
}
GRAPH_CONTAINER_STYLE = {'flex': 1, 'padding': '10px'}

# --- DOTTY Parser ---
def parse_dotty(text: str) -> Tuple[List[Node], List[Edge]]:
    # Nodes
    node_pat = re.compile(r"node (\w+)\s*\[([^\]]*)\]")
    get_val = lambda pat, s, default=None: pat.search(s).group(1) if pat.search(s) else default
    nodes: List[Node] = []
    idx_map: Dict[str,int] = {}
    for match in node_pat.finditer(text):
        name, props = match.group(1), match.group(2)
        pos_str = get_val(re.compile(r"pos\s*=\s*\"([^\"]+)\""), props)
        pos = [float(v) for v in pos_str.split(",")] if pos_str else [0.5,0.5,0.5]
        shape = get_val(re.compile(r"shape\s*=\s*(\w+)"), props, "sphere")
        color = get_val(re.compile(r"color\s*=\s*(\w+)"), props, "blue")
        size = int(get_val(re.compile(r"size\s*=\s*(\d+)"), props, "12"))
        idx_map[name] = len(nodes)
        nodes.append(Node(name, pos, shape, color, size))
    # Edges
    edge_pat = re.compile(r"(\w+)\s*--\s*(\w+)\s*\[([^\]]*)\]")
    edges: List[Edge] = []
    for match in edge_pat.finditer(text):
        n1, n2, props = match.group(1), match.group(2), match.group(3)
        if n1 not in idx_map or n2 not in idx_map:
            logger.error(f"Edge {n1}--{n2} references unknown node(s)")
            continue
        e_type = get_val(re.compile(r"type\s*=\s*(\w+)"), props, "solid")
        e_color = get_val(re.compile(r"color\s*=\s*(\w+)"), props, "black")
        e_width = int(get_val(re.compile(r"width\s*=\s*(\d+)"), props, "2"))
        edges.append(Edge(n1, n2, e_type, e_color, e_width))
    return nodes, edges

# --- Fit Nodes ---
def fit_nodes(nodes: List[Node]) -> List[Node]:
    arr = np.array([n.pos for n in nodes], dtype=float)
    mn, mx = arr.min(axis=0), arr.max(axis=0)
    center = (mn + mx) / 2
    span = (mx - mn).max()
    scale = 0.8 / span if span > 0 else 1.0
    return [Node(n.name, ((np.array(n.pos)-center)*scale+0.5).tolist(), n.shape, n.color, n.size) for n in nodes]

# --- Cube Faces ---
cube_faces = [
    ("left",  [[0,0,0],[0,1,0],[0,1,1],[0,0,1]], np.array([-0.5,0.5,0.5]), np.array([1,0,0])),
    ("right", [[1,0,0],[1,1,0],[1,1,1],[1,0,1]], np.array([1.5,0.5,0.5]), np.array([-1,0,0])),
    ("bottom",[[0,0,0],[1,0,0],[1,0,1],[0,0,1]], np.array([0.5,-0.5,0.5]), np.array([0,1,0])),
    ("top",   [[0,1,0],[1,1,0],[1,1,1],[0,1,1]], np.array([0.5,1.5,0.5]), np.array([0,-1,0])),
    ("back",  [[0,0,0],[1,0,0],[1,1,0],[0,1,0]], np.array([0.5,0.5,-0.5]), np.array([0,0,1])),
    ("front", [[0,0,1],[1,0,1],[1,1,1],[0,1,1]], np.array([0.5,0.5,1.5]), np.array([0,0,-1]))
]

# --- Render 2D Side ---
def render_face(i: int, nodes: List[Node], edges: List[Edge], W: int = 100, H: int = 100) -> Tuple[np.ndarray,str]:
    verts, cam_pos, view_dir = cube_faces[i][1], cube_faces[i][2].astype(float), cube_faces[i][3].astype(float)
    up = np.array([0.0,1.0,0.0]) if abs(view_dir[1])<0.9 else np.array([1.0,0.0,0.0])
    right = np.cross(view_dir, up); up = np.cross(right, view_dir)
    right /= np.linalg.norm(right); up /= np.linalg.norm(up)
    proj = [((np.dot(np.array(n.pos)-cam_pos, right)+0.5)*W,
             (np.dot(np.array(n.pos)-cam_pos, up)+0.5)*H) for n in nodes]
    img = Image.new('RGB',(W,H),(255,255,255)); draw=ImageDraw.Draw(img)
    for (x,y),n in zip(proj,nodes): r=int(n.size*0.3); draw.ellipse([(x-r,y-r),(x+r,y+r)],fill=n.color)
    buf=io.BytesIO(); img.save(buf,'PNG'); buf.seek(0)
    return np.array(Image.open(buf))/255.0, 'data:image/png;base64,'+base64.b64encode(buf.read()).decode()

# --- Cylinder Function ---
def cylinder(p1: List[float], p2: List[float], radius: float):
    p1_arr, p2_arr = np.array(p1), np.array(p2)
    v = p2_arr - p1_arr
    L = np.linalg.norm(v)
    if L == 0:
        return None, None, None
    v = v / L
    ortho = np.array([1, 0, 0]) if abs(v[0]) < 0.9 else np.array([0, 1, 0])
    n1 = np.cross(v, ortho)
    n1 = n1 / np.linalg.norm(n1)
    n2 = np.cross(v, n1)
    t, theta = np.meshgrid(np.linspace(0, L, 2), np.linspace(0, 2 * np.pi, 16))
    X = p1_arr[0] + v[0] * t + radius * (np.cos(theta) * n1[0] + np.sin(theta) * n2[0])
    Y = p1_arr[1] + v[1] * t + radius * (np.cos(theta) * n1[1] + np.sin(theta) * n2[1])
    Z = p1_arr[2] + v[2] * t + radius * (np.cos(theta) * n1[2] + np.sin(theta) * n2[2])
    return X, Y, Z

# --- Build 3D Figure ---
def build_fig(face_imgs, transp, nodes, edges) -> go.Figure:
    fig = go.Figure()
    # faces
    for i,(name,verts,_,_) in enumerate(cube_faces):
        f = np.array(verts); xs,ys,zs = f[:,0],f[:,1],f[:,2]
        col = face_imgs[i][0][:,:,0]  # grayscale
        fig.add_trace(go.Surface(
            x=[[xs[0],xs[1]],[xs[3],xs[2]]],
            y=[[ys[0],ys[1]],[ys[3],ys[2]]],
            z=[[zs[0],zs[1]],[zs[3],zs[2]]],
            surfacecolor=col, cmin=0, cmax=1,
            showscale=False, opacity=transp[name],
            colorscale='Greys', hoverinfo='skip'
        ))
    # nodes
    for n in nodes:
        sym = {'sphere':'circle','cube':'square','pyramid':'diamond'}.get(n.shape,'circle')
        fig.add_trace(go.Scatter3d(
            x=[n.pos[0]],y=[n.pos[1]],z=[n.pos[2]],
            mode='markers', marker=dict(size=n.size, color=n.color, symbol=sym),
            showlegend=False, hoverinfo='skip'
        ))
    # edges
    m = {n.name:n for n in nodes}
    for e in edges:
        p1,p2 = m[e.source].pos, m[e.target].pos
        X,Y,Z = cylinder(p1,p2,0.005*e.width)
        if X is not None:
            fig.add_trace(go.Surface(x=X,y=Y,z=Z, showscale=False, opacity=1.0,
                                     surfacecolor=np.ones(X.shape)*0.5, colorscale=[[0,e.color],[1,e.color]]))
        fig.add_trace(go.Scatter3d(x=[p1[0],p2[0]],y=[p1[1],p2[1]],z=[p1[2],p2[2]],
                                   mode='lines', line=dict(color=e.color, width=2, dash=e.type)))
    fig.update_layout(scene=dict(xaxis=dict(visible=False,range=[0,1]),
                                 yaxis=dict(visible=False,range=[0,1]),
                                 zaxis=dict(visible=False,range=[0,1]),
                                 aspectmode='cube'), margin=dict(l=0,r=0,t=0,b=0))
    return fig

# --- Dash App ---
app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div([
        html.Label("DOTTY Model"),
        dcc.Textarea(id='dotty-input', value=example_dotty(), style={'width':'100%','height':120}),
        html.Br(), html.Label("Group sliders"),
        dcc.Checklist(id='group-checks', options=[{'label':'L/R','value':'lr'},{'label':'T/B','value':'tb'}], value=[], inline=True),
        html.Div(id='sliders-div'), html.Hr(), html.Label("Face Views"),
        html.Div([html.Img(id={'type':'faceview','face':f}, style={'width':'64px','margin':'3px'}) for f in ['left','right','top','bottom','front','back']], style={'textAlign':'center'})
    ], style=SIDEBAR_STYLE),
    html.Div([dcc.Graph(id='cube-graph', style={'height':'80vh'})], style=GRAPH_CONTAINER_STYLE)
], style={'display':'flex'})

@app.callback(
    [Output({'type':'faceview','face':f}, 'src') for f in ['left','right','top','bottom','front','back']],
    Input('dotty-input','value'),
    Input('group-checks','value')
)
def update_faceviews(dot, groups):
    nodes, edges = parse_dotty(dot)
    nodes = fit_nodes(nodes)
    return [url for _,url in [render_face(i,nodes,edges) for i in range(6)]]

@app.callback(
    Output('cube-graph','figure'),
    Input('dotty-input','value'),
    Input('group-checks','value'),
    Input({'type':'faceview','face':ALL}, 'n_clicks_timestamp')
)
def update_figure(dot, groups, click_ts):
    nodes, edges = parse_dotty(dot)
    nodes = fit_nodes(nodes)
    # transparency defaults
    transp = {name:0.5 for name,_,_,_ in cube_faces}
    face_imgs = [render_face(i,nodes,edges) for i in range(6)]
    fig = build_fig(face_imgs, transp, nodes, edges)
    # camera reset
    ts = [t or 0 for t in click_ts]
    idx = int(np.argmax(ts))
    cam_dir = cube_faces[idx][3].astype(float)
    center = np.array([0.5,0.5,0.5])
    eye = (center + cam_dir*2).tolist()
    world_up = np.array([0,1,0])
    if abs(np.dot(world_up,cam_dir))>0.9: world_up=np.array([1,0,0])
    cam_up = np.cross(np.cross(cam_dir,world_up),cam_dir)
    cam_up /= np.linalg.norm(cam_up)
    fig.update_layout(scene_camera=dict(eye=dict(x=eye[0],y=eye[1],z=eye[2]), up=dict(x=cam_up[0],y=cam_up[1],z=cam_up[2])))
    return fig

if __name__=='__main__':
    app.run(debug=True)
