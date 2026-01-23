import streamlit as st
import pandas as pd
import feedparser
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go # HARİTA İÇİN EKLENDİ
from urllib.parse import quote
import spacy
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from collections import Counter
import tempfile
import os
import sys
import subprocess
import re
import base64

# --- 1. SETTINGS ---
st.set_page_config(page_title="NEXUS PRIME", layout="wide", page_icon="N")

# --- BACKGROUND LOADER ---
def set_background(image_file):
    with open(image_file, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/jpeg;base64,{data}");
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

try:
    set_background('nexus_background.jpeg')
except FileNotFoundError:
    pass

# --- YENİ HALİ (YAPIŞTIRILACAK) ---
@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()

# --- GLOBAL COORDINATES DATABASE (SIMPLE) ---
# Ekstra kütüphane (geopy) kurdurmamak için temel koordinatları gömüyoruz.
COUNTRY_COORDS = {
    "USA": [37.0902, -95.7129], "US": [37.0902, -95.7129], "America": [37.0902, -95.7129],
    "China": [35.8617, 104.1954], "Beijing": [39.9042, 116.4074],
    "Russia": [61.5240, 105.3188], "Moscow": [55.7558, 37.6173],
    "Ukraine": [48.3794, 31.1656], "Kiev": [50.4501, 30.5234],
    "Germany": [51.1657, 10.4515], "Berlin": [52.5200, 13.4050],
    "UK": [55.3781, -3.4360], "London": [51.5074, -0.1278],
    "France": [46.2276, 2.2137], "Paris": [48.8566, 2.3522],
    "Turkey": [38.9637, 35.2433], "Istanbul": [41.0082, 28.9784], "Ankara": [39.9334, 32.8597],
    "India": [20.5937, 78.9629], "Delhi": [28.6139, 77.2090],
    "Japan": [36.2048, 138.2529], "Tokyo": [35.6762, 139.6503],
    "Israel": [31.0461, 34.8516], "Gaza": [31.5017, 34.4668],
    "Iran": [32.4279, 53.6880], "Tehran": [35.6892, 51.3890],
    "Brazil": [-14.2350, -51.9253],
    "Canada": [56.1304, -106.3468],
    "Australia": [-25.2744, 133.7751],
    "South Korea": [35.9078, 127.7669],
    "North Korea": [40.3399, 127.5101],
    "Italy": [41.8719, 12.5674],
    "Spain": [40.4637, -3.7492],
    "Syria": [34.8021, 38.9968],
    "Iraq": [33.2232, 43.6793],
    "Egypt": [26.8206, 30.8025],
    "Saudi Arabia": [23.8859, 45.0792],
    "UAE": [23.4241, 53.8478], "Dubai": [25.2048, 55.2708]
}

# --- 2. CSS & DESIGN ---
st.markdown("""
<style>
        /* 1. TITLE DESIGN */
        .nexus-title {
            font-family: 'Helvetica', sans-serif !important;
            font-weight: 900 !important;
            font-size: 4.5rem !important; 
            color: transparent !important; 
            -webkit-text-stroke: 1px #ffffff; 
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.5) !important; 
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
            white-space: nowrap; 
        }

        /* 2. SEARCH BAR */
        div[data-baseweb="input"] {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.7) !important;
            border-radius: 12px !important;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.2) !important;
            height: 55px !important; 
            min-height: 55px !important;
        }
        div[data-baseweb="base-input"] { background-color: transparent !important; }
        input[type="text"] { 
            background-color: transparent !important; 
            color: #ffffff !important; 
            font-size: 1.1rem !important;
        }

        /* 3. BUTTON DESIGN */
        div.stButton > button {
            background-color: transparent !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.7) !important;
            border-radius: 12px !important;
            height: 55px !important;
            min-height: 55px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1.8rem !important;
            padding-top: 0px !important;
            padding-bottom: 5px !important;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.2) !important;
            transition: all 0.3s ease-in-out;
        }
        div.stButton > button:hover {
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.9) !important;
            border-color: #ffffff !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            transform: scale(1.05);
        }
        div.stButton > button:active {
            background-color: #ffffff !important;
            color: #000000 !important;
        }

        /* 4. KPI CARDS */
        div[data-testid="stMetric"] {
            background-color: rgba(0, 0, 0, 0.5); 
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px !important;
            padding: 15px;
            backdrop-filter: blur(10px); 
            text-align: center !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        div[data-testid="stMetricLabel"] { 
            width: 100%; 
            text-align: center !important; 
            justify-content: center !important; 
            color: #ccc; 
            font-size: 1.1rem !important;
            font-weight: bold !important;
        }
        div[data-testid="stMetricValue"] { 
            width: 100%; 
            text-align: center !important; 
            color: #00f2ea; 
            font-size: 2.2rem !important; 
            text-shadow: 0 0 15px rgba(0, 242, 234, 0.6); 
        }
        div[data-testid="stMetricDelta"] {
            justify-content: center !important;
            font-size: 1rem !important;
        }

        /* 5. TABS */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { 
            color: #00f2ea !important; 
            font-size: 1.2rem; 
            font-weight: bold; 
            text-shadow: 0 0 5px rgba(0,0,0,0.8); 
            font-family: serif !important; 
        }
        .stTabs [aria-selected="true"] { 
            border-bottom: 2px solid #00f2ea; 
        }
</style>
""", unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = re.sub(r'http\S+', '', cleantext)
    return cleantext.strip()

def fetch_news(topic):
    try:
        safe_topic = quote(topic)
        url = f"https://news.google.com/rss/search?q={safe_topic}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        data = []
        for entry in feed.entries[:80]: # Veri sayısını artırdık ki harita dolsun
            summary_raw = entry.summary if 'summary' in entry else ""
            summary_clean = clean_html(summary_raw)
            data.append({
                "Title": entry.title,
                "Source": entry.source.title,
                "Date": entry.published,
                "Link": entry.link,
                "Summary": summary_clean
            })
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def process_nlp(df):
    df['Polarity'] = df['Title'].apply(lambda x: TextBlob(x).sentiment.polarity)
    df['Sentiment'] = df['Polarity'].apply(lambda s: "Positive" if s > 0.05 else ("Negative" if s < -0.05 else "Neutral"))
    
    entities_list = []
    locations_list = [] # Harita için lokasyonları tutacak liste

    for i, row in df.iterrows():
        full_text = f"{row['Title']} {row['Summary']}"
        doc = nlp(full_text)
        
        valid_labels = ['PERSON', 'ORG', 'GPE', 'PRODUCT']
        ents = []
        locs = [] # Bu haberdeki lokasyonlar
        
        for ent in doc.ents:
            text = ent.text.strip()
            # Genel varlıklar
            if (ent.label_ in valid_labels and len(text) > 2 and len(text) < 30 and "http" not in text):
                ents.append(text)
            
            # Sadece Lokasyonlar (GPE = Geopolitical Entity)
            if ent.label_ == 'GPE' and text in COUNTRY_COORDS:
                locs.append(text)
                
        entities_list.append(list(set(ents)))
        locations_list.append(list(set(locs)))

    df['Entities'] = entities_list
    df['Locations'] = locations_list # Yeni kolon
    return df

# --- 3D MAP GENERATOR ---
def generate_geo_map(df):
    # Lokasyon verilerini düzleştir
    flat_locs = []
    for i, row in df.iterrows():
        for loc in row['Locations']:
            flat_locs.append({'Location': loc, 'Polarity': row['Polarity'], 'Title': row['Title']})
    
    if not flat_locs:
        return None
    
    geo_df = pd.DataFrame(flat_locs)
    
    # Lokasyona göre grupla (Ortalama duygu ve Haber sayısı)
    grouped = geo_df.groupby('Location').agg({'Polarity': 'mean', 'Title': 'count'}).reset_index()
    
    # Koordinatları ekle
    grouped['lat'] = grouped['Location'].apply(lambda x: COUNTRY_COORDS[x][0])
    grouped['lon'] = grouped['Location'].apply(lambda x: COUNTRY_COORDS[x][1])
    
    # Duyguya göre renk (Pozitif: Yeşil, Negatif: Kırmızı)
    grouped['Color'] = grouped['Polarity'].apply(lambda x: '#00f2ea' if x > 0 else '#ff0055')
    
    # HARİTA TASARIMI (ORTHOGRAPHIC = KÜRE)
    fig = go.Figure(data=go.Scattergeo(
        lon = grouped['lon'],
        lat = grouped['lat'],
        text = grouped['Location'] + "<br>News Count: " + grouped['Title'].astype(str),
        mode = 'markers',
        marker = dict(
            size = grouped['Title'] * 5 + 5, # Haber sayısına göre büyüyen baloncuklar
            opacity = 0.8,
            reversescale = True,
            autocolorscale = False,
            symbol = 'circle',
            line = dict(width=1, color='rgba(102, 102, 102)'),
            color = grouped['Color'], # Duygu rengi
            shadow = False
        )
    ))

    fig.update_layout(
        title = '',
        geo = dict(
            scope='world',
            projection_type='orthographic', # 3D KÜRE MODU
            showland = True,
            landcolor = "rgb(20, 20, 20)",
            showocean = True,
            oceancolor = "rgba(0,0,0,0)",
            showlakes = True,
            lakecolor = "rgb(0, 0, 0)",
            showcountries = True,
            countrycolor = "rgb(50, 50, 50)",
            bgcolor= "rgba(0,0,0,0)"
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=600
    )
    return fig

# --- NETWORK GENERATOR ---
def generate_network_html(df):
    G = nx.Graph()
    for entities in df['Entities']:
        for entity in entities:
            G.add_node(entity, label=entity, title=entity)
        if len(entities) > 1:
            for i in range(len(entities)):
                for j in range(i + 1, len(entities)):
                    if G.has_edge(entities[i], entities[j]):
                        G[entities[i]][entities[j]]['weight'] += 1
                    else:
                        G.add_edge(entities[i], entities[j], weight=1)
    if len(G.nodes) == 0: return None

    # Arka plan SİYAH
    net = Network(height="650px", width="100%", bgcolor="#000000", font_color="white", select_menu=False, filter_menu=False, cdn_resources='remote')
    net.from_nx(G)
    
    # --- NODE TASARIMI ---
    for node in net.nodes:
        node['shape'] = 'dot' 
        node['size'] = 25
        
        # 1. PARLAMA EFEKTİ (GLOW)
        node['shadow'] = {
            'enabled': True, 
            'color': '#00f2ea', 
            'size': 30,         
            'x': 0, 'y': 0      
        }

        # 2. RENKLER
        node['color'] = {
            'background': '#000000', 
            'border': '#00f2ea',     
            'highlight': {
                'background': '#00f2ea', 
                'border': '#ffffff'              
            },
            'hover': {
                 'background': '#333333',
                 'border': '#ffffff'
            }
        }
        node['borderWidth'] = 3 
        
        # 3. YAZI STİLİ
        node['font'] = {
            'color': 'white', 
            'size': 16, 
            'face': 'arial',
            'strokeWidth': 4, 
            'strokeColor': '#000000',
            'vadjust': -35 
        }

    # 4. FİZİK VE ÇİZGİ AYARLARI (JSON FORMATI DÜZELTİLDİ)
    # Yorum satırları silindi ve 'var options =' kaldırıldı. Sadece süslü parantez {...} kaldı.
    options = """
    {
      "edges": {
        "color": {
          "color": "rgba(0, 242, 234, 0.3)",
          "highlight": "#ffffff",
          "inherit": false
        },
        "smooth": {
            "type": "continuous",
            "roundness": 0.5
        },
        "width": 1
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 150,
          "springConstant": 0.08,
          "damping": 0.4
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """
    net.set_options(options)
    
    try:
        path = os.path.join(tempfile.gettempdir(), "nexus_network.html")
        net.save_graph(path)
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        return None
# --- 4. MAIN INTERFACE ---

c_title, c_input, c_btn = st.columns([2.5, 3, 0.7])

with c_title:
    st.markdown('<h1 class="nexus-title">𝐍𝐄𝐗𝐔𝐒</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#ccc; text-shadow: 1px 1px 2px black; font-size: 0.9rem;">Advanced OSINT & Relationship Analyzer</p>', unsafe_allow_html=True)
    
with c_input:
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    topic = st.text_input("Search", "Elon Musk", label_visibility="collapsed", placeholder="Enter target...")

with c_btn:
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    run_btn = st.button("🚀", type="primary", use_container_width=True)


# --- 5. LOGIC & EXECUTION ---

if run_btn:
    raw_df = fetch_news(topic)
    
    if not raw_df.empty:
        raw_df['Date'] = pd.to_datetime(raw_df['Date'], errors='coerce')
        
        with st.spinner('Neural networks processing data...'):
            df = process_nlp(raw_df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # KPI CARDS
        k1, k2, k3 = st.columns(3)
        k1.metric("𝐒𝐎𝐔𝐑𝐂𝐄𝐒", len(df))
        
        mean_polarity = df['Polarity'].mean()
        if mean_polarity > 0.05:
            k2.metric("𝐆𝐋𝐎𝐁𝐀𝐋 𝐒𝐄𝐍𝐓𝐈𝐌𝐄𝐍𝐓", f"{mean_polarity:.2f}", delta="+ Positive Trend")
        elif mean_polarity < -0.05:
            k2.metric("𝐆𝐋𝐎𝐁𝐀𝐋 𝐒𝐄𝐍𝐓𝐈𝐌𝐄𝐍𝐓", f"{mean_polarity:.2f}", delta="- Negative Trend", delta_color="inverse")
        else:
            k2.metric("𝐆𝐋𝐎𝐁𝐀𝐋 𝐒𝐄𝐍𝐓𝐈𝐌𝐄𝐍𝐓", f"{mean_polarity:.2f}", delta="• Neutral", delta_color="off")
        
        all_ents = [e for sub in df['Entities'] for e in sub]
        k3.metric("𝐃𝐄𝐓𝐄𝐂𝐓𝐄𝐃 𝐄𝐍𝐓𝐈𝐓𝐈𝐄𝐒", len(set(all_ents)))
        
        st.divider()
        
        # --- NEW TAB STRUCTURE ---
        tab_charts, tab_network, tab_map = st.tabs(["📊 𝐆𝐑𝐀𝐏𝐇𝐒", "🕸️ 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", "🌍 𝐆𝐄𝐎-𝐌𝐀𝐏"])
        
        with tab_charts:
            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                st.subheader("Timeline Analysis")
                fig_scatter = px.scatter(df, x="Date", y="Polarity", color="Sentiment", template="plotly_dark",
                                 color_discrete_map={"Positive": "#00f2ea", "Negative": "#ff0055", "Neutral": "#888"})
                fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            with col_chart2:
                st.subheader("Source Distribution")
                src_counts = df['Source'].value_counts().head(5)
                fig_pie = px.pie(values=src_counts.values, names=src_counts.index, hole=0.4, template="plotly_dark",
                                 color_discrete_sequence=px.colors.sequential.Teal)
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.subheader("Latest Intelligence")
            st.dataframe(df[['Date', 'Title', 'Source', 'Sentiment']], use_container_width=True)

        with tab_network:
            html = generate_network_html(df)
            if html:
                components.html(html, height=670, scrolling=False)
            else:
                st.warning("Insufficient connections found.")
        
        # --- NEW MAP TAB ---
        with tab_map:
            st.subheader(f"Geopolitical Impact of '{topic}'")
            map_fig = generate_geo_map(df)
            if map_fig:
                st.plotly_chart(map_fig, use_container_width=True)
            else:
                st.warning("No geospatial data detected in the news content. Try searching for a country or major global event.")

    else:
        st.error("No data found.")

else:
    st.info("👆 Enter a subject above and click launch to start analysis.")