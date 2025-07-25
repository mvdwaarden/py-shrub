import dash
from dash import dcc, html, Input, Output, ALL
import plotly.graph_objects as go
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Parsing functions ---

def parse_nodes(text):
    """Extract node definitions from DOTTY text."""
    node_pat = re.compile(r"node (\w+)\s*\[([^\]]*)\]")
    get_val = lambda pat, s, default=None: pat.search(s).group(1) if pat.search(s) else default
    nodes = []
    idx_map = {}
    for match in node_pat.finditer(text):
        name, props = match.group(1), match.group(2)
        pos_str = get_val(re.compile(r"pos\s*=\s*\"([^\"]+)\""), props)
        pos = [float(v) for v in pos_str.split(",")] if pos_str else [0.5, 0.5, 0.5]
        shape = get_val(re.compile(r"shape\s*=\s*(\w+)"), props, "sphere")
        color = get_val(re.compile(r"color\s*=\s*(\w+)"), props, "blue")
        size = int(get_val(re.compile(r"size\s*=\s*(\d+)"), props, "12"))
        idx_map[name] = len(nodes)
        nodes.append({"name": name, "pos": pos, "shape": shape, "color": color, "size": size})
    return nodes, idx_map


def parse_edges(text, idx_map):
    """Extract edge definitions from DOTTY text, using node index map."""
    edge_pat = re.compile(r"(\w+)\s*--\s*(\w+)\s*\[([^\]]*)\]")
    get_val = lambda pat, s, default=None: pat.search(s).group(1) if pat.search(s) else default
    edges = []
    for match in edge_pat.finditer(text):
        n1, n2, props = match.group(1), match.group(2), match.group(3)
        if n1 not in idx_map or n2 not in idx_map:
            logger.error(f"Edge {n1}--{n2} references unknown node(s)")
            continue
        e_type = get_val(re.compile(r"type\s*=\s*(\w+)"), props, "solid")
        e_color = get_val(re.compile(r"color\s*=\s*(\w+)"), props, "black")
        e_width = int(get_val(re.compile(r"width\s*=\s*(\d+)"), props, "2"))
        edges.append({"from": n1, "to": n2, "type": e_type, "color": e_color, "width": e_width})
    return edges


def parse_dotty(text):
    """Parse both nodes and edges from DOTTY text."""
    nodes, idx_map = parse_nodes(text)
    edges = parse_edges(text, idx_map)
    return nodes, edges

# Scale nodes to fit within 80% of the cube interior
def fit_nodes(nodes):
    if not nodes:
        return nodes
    arr = np.array([n['pos'] for n in nodes])
    mn, mx = arr.min(axis=0), arr.max(axis=0)
    center = (mn + mx) / 2
    span = (mx - mn).max()
    scale = 0.8 / span if span > 0 else 1.0
    for n in nodes:
        p = np.array(n['pos'])
        n['pos'] = (0.5 + (p - center) * scale).tolist()
    return nodes

# Cube faces definitions: (name, vertices, camera pos, view direction)
cube_faces = [
    ("left",  [[0,0,0],[0,1,0],[0,1,1],[0,0,1]], np.array([-0.5,0.5,0.5]), np.array([1,0,0])),
    ("right", [[1,0,0],[1,1,0],[1,1,1],[1,0,1]], np.array([1.5,0.5,0.5]), np.array([-1,0,0])),
    ("bottom",[[0,0,0],[1,0,0],[1,0,1],[0,0,1]], np.array([0.5,-0.5,0.5]), np.array([0,1,0])),
    ("top",   [[0,1,0],[1,1,0],[1,1,1],[0,1,1]], np.array([0.5,1.5,0.5]), np.array([0,-1,0])),
    ("back",  [[0,0,0],[1,0,0],[1,1,0],[0,1,0]], np.array([0.5,0.5,-0.5]), np.array([0,0,1])),
    ("front", [[0,0,1],[1,0,1],[1,1,1],[0,1,1]], np.array([0.5,0.5,1.5]), np.array([0,0,-1])),
]

# Render face projection image for sidebar
# Ensure float types for normalization

def render_face(face_idx, nodes, edges, W=100, H=100):
    """Render a 2D projection of nodes and edges onto cube face for sidebar."""
    # Unpack face parameters and ensure floats
    verts = cube_faces[face_idx][1]
    cam_pos = cube_faces[face_idx][2].astype(float)
    view_dir = cube_faces[face_idx][3].astype(float)

    # Compute orthonormal basis
    up = np.array([0.0, 1.0, 0.0]) if abs(view_dir[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    right = np.cross(view_dir, up).astype(float)
    up = np.cross(right, view_dir).astype(float)
    # Use non-in-place division to avoid casting errors
    right = right / np.linalg.norm(right)
    up = up / np.linalg.norm(up)

    # Project nodes
    proj = []
    for n in nodes:
        v = np.array(n['pos'], dtype=float) - cam_pos
        x = np.dot(v, right)
        y = np.dot(v, up)
        proj.append(((x + 0.5) * W, (y + 0.5) * H))

    # Draw image
    img = Image.new('RGB', (W, H), (240, 240, 255))
    draw = ImageDraw.Draw(img)
    name2idx = {n['name']: i for i, n in enumerate(nodes)}

    # Draw edges
    for e in edges:
        if e['from'] not in name2idx or e['to'] not in name2idx:
            continue
        p1 = proj[name2idx[e['from']]]
        p2 = proj[name2idx[e['to']]]
        dash = [2, 6] if e['type'] == 'dotted' else ([8, 6] if e['type'] == 'dashed' else None)
        try:
            draw.line([p1, p2], fill=e['color'], width=e['width'], dash=dash)
        except TypeError:
            draw.line([p1, p2], fill=e['color'], width=e['width'])

    # Draw nodes
    for (x, y), n in zip(proj, nodes):
        r = int(n['size'] * 0.4)
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=n['color'], outline='black')

    # Convert to array and return URL
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    arr = np.array(Image.open(buf)) / 255.0
    buf.seek(0)
    url = 'data:image/png;base64,' + base64.b64encode(buf.read()).decode()
    return arr, url

# Create cylinder mesh between two points
def cylinder(p1,p2,radius):
    p1,p2=np.array(p1),np.array(p2)
    v=p2-p1;L=np.linalg.norm(v)
    if L==0: return None,None,None
    v/=L; ortho=np.array([1,0,0]) if abs(v[0])<0.9 else np.array([0,1,0])
    n1=np.cross(v,ortho); n1/=np.linalg.norm(n1); n2=np.cross(v,n1)
    t,theta=np.meshgrid(np.linspace(0,L,2),np.linspace(0,2*np.pi,2))
    X=p1[0]+v[0]*t+radius*(np.cos(theta)*n1[0]+np.sin(theta)*n2[0])
    Y=p1[1]+v[1]*t+radius*(np.cos(theta)*n1[1]+np.sin(theta)*n2[1])
    Z=p1[2]+v[2]*t+radius*(np.cos(theta)*n1[2]+np.sin(theta)*n2[2])
    return X,Y,Z

# Build the 3D figure
def build_fig(face_imgs,transparency,nodes,edges):
    fig=go.Figure()
    for i,(name,verts,_,_) in enumerate(cube_faces):
        f=np.array(verts); xs,ys,zs=f[:,0],f[:,1],f[:,2]; img=face_imgs[i][0]
        fig.add_trace(go.Surface(x=[[xs[0],xs[1]],[xs[3],xs[2]]],y=[[ys[0],ys[1]],[ys[3],ys[2]]],z=[[zs[0],zs[1]],[zs[3],zs[2]]],surfacecolor=img[:,:,2],cmin=0,cmax=1,showscale=False,opacity=transparency[name],colorscale='Blues',hoverinfo='skip'))
    for n in nodes:
        sym={'sphere':'circle','cube':'square','pyramid':'diamond'}.get(n['shape'],'circle')
        fig.add_trace(go.Scatter3d(x=[n['pos'][0]],y=[n['pos'][1]],z=[n['pos'][2]],mode='markers',marker=dict(size=n['size'],color=n['color'],symbol=sym,opacity=1),showlegend=False,hoverinfo='skip'))
    name2n={n['name']:n for n in nodes}
    for e in edges:
        p1=name2n[e['from']]['pos'];p2=name2n[e['to']]['pos']
        X,Y,Z=cylinder(p1,p2,0.01*e['width'])
        if X is not None: fig.add_trace(go.Surface(x=X,y=Y,z=Z,showscale=False,opacity=1.0,surfacecolor=np.ones(X.shape)*0.8,colorscale=[[0,e['color']],[1,e['color']]],hoverinfo='skip'))
        dash={'dotted':'dot','dashed':'dash'}.get(e['type'],None)
        fig.add_trace(go.Scatter3d(x=[p1[0],p2[0]],y=[p1[1],p2[1]],z=[p1[2],p2[2]],mode='lines',line=dict(color=e['color'],width=2,dash=dash),showlegend=False,hoverinfo='skip'))
    fig.update_layout(scene=dict(xaxis=dict(range=[0,1],visible=False),yaxis=dict(range=[0,1],visible=False),zaxis=dict(range=[0,1],visible=False),aspectmode='cube',bgcolor='white'),margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor='white')
    return fig

# Dash app
app = dash.Dash(__name__)

# Slider grouping options
group_options=[{'label':'Left/Right','value':'leftright'},{'label':'Top/Bottom','value':'topbottom'},{'label':'Front/Back','value':'frontback'}]

def example_dotty():
    return '''
    node 1 [pos="0.2,0.2,0.2",shape=sphere,color=red,size=18];
    node 2 [pos="0.8,0.2,0.2",shape=pyramid,color=green,size=24];
    node 3 [pos="0.5,0.8,0.2",shape=cube,color=blue,size=28];
    node 4 [pos="0.8,0.2,0.8",shape=pyramid,color=white,size=30];
    1 -- 2 [type=dotted,color=magenta,width=2];
    1 -- 3 [type=dotted,color=green,width=2];
    4 -- 2 [type=dotted,color=blue,width=2];
    4 -- 1 [type=dotted,color=blue,width=2];
    4 -- 3 [type=dotted,color=blue,width=2];
    '''

app.layout=html.Div([
    html.H3("3D Dotty Cube – Resizable Sidebar & Connected Vertices"),
    html.Div([
        html.Div([
            html.Label("DOTTY Model"),
            dcc.Textarea(id='dotty-input',value=example_dotty(),style={'width':'100%','height':120,'fontFamily':'monospace'}),
            html.Br(),html.Label("Group sliders"),
            dcc.Checklist(id='group-checks',options=group_options,value=[],inline=True),
            html.Div(id='sliders-div'),html.Hr(),
            html.Label("Face Views"),
            html.Div([html.Img(id={'type':'faceview','face':f},style={'width':'72px','margin':'3px'}) for f in ['left','right','top','bottom','front','back']],style={'textAlign':'center'})
        ],id='sidebar', style={'resize':'horizontal','overflow':'auto','overflow-x':'auto','overflow-y':'auto','minWidth':'180px','maxWidth':'2000px','width':'1000px','background':'#f8f8ff','padding':'20px','borderRadius':'12px','boxShadow':'0 2px 8px #ddd','maxHeight':'100vh'}),
        html.Div([dcc.Graph(id='cube-graph',style={'height':'80vh','minWidth':'600px'}),html.P("Drag to rotate, scroll to zoom, right-drag to pan.")],style={'flex':1,'padding':'10px'})
    ],style={'display':'flex','flexDirection':'row'})
])

@app.callback(
    [Output({'type':'faceview','face':f}, 'src') for f in ['left','right','top','bottom','front','back']],
    Input('dotty-input','value'),
    Input('group-checks','value'),
    Input({'type':'slider','name':ALL}, 'value')
)
def update_faceviews(dotty, groups, sv):
    nodes,edges=parse_dotty(dotty);nodes=fit_nodes(nodes)
    return [url for _,url in [render_face(i,nodes,edges) for i in range(6)]]

@app.callback(Output('cube-graph','figure'),Input('dotty-input','value'),Input('group-checks','value'),Input({'type':'slider','name':ALL},'value'))
def update_figure(dotty,groups,sv):
    nodes,edges=parse_dotty(dotty);nodes=fit_nodes(nodes)
    face_map,order={},[]
    if 'leftright' in groups: face_map['left']=face_map['right']='leftright';order.append('leftright')
    if 'topbottom' in groups: face_map['top']=face_map['bottom']='topbottom';order.append('topbottom')
    if 'frontback' in groups: face_map['front']=face_map['back']='frontback';order.append('frontback')
    for n,*_ in cube_faces:
        if n not in face_map: face_map[n]=n;order.append(n)
    transp={}
    for i,k in enumerate(order):
        v=sv[i] if sv and i<len(sv) and sv[i] is not None else 0.5
        for f,gp in face_map.items():
            if gp==k: transp[f]=v
    return build_fig([render_face(i,nodes,edges) for i in range(6)],transp,nodes,edges)

if __name__=='__main__':
    app.run(debug=True)
