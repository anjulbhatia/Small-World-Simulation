import streamlit as st
import networkx as nx
from collections import deque
import matplotlib.pyplot as plt
import pandas as pd
import time

# --- Page Configuration ---
st.set_page_config(page_icon="💡", page_title="Small World Simulator", layout="wide")
st.markdown("<style>.stApp{margin-top: -5em;}</style>", unsafe_allow_html=True)

# --- Title & Description ---
st.title("Small World Simulator")
st.markdown("""
Explore a network of people and see **how quickly a message spreads**!  
Compare **regular, small-world, and random networks**.  
Created by: [Anjul Bhatia](https://www.linkedin.com/in/anjulbhatia)
""")

# --- Network Parameters ---
st.markdown("### Simulation Parameters")
col1, col2, col3 = st.columns(3)
with col1: nodes = st.slider("Population (nodes)", 20, 200, 50, step=10)
with col2: neighbours = st.slider("Average Friends (k)", 2, 10, 4)
with col3: randomness = st.slider("Randomness (p)", 0.01, 1.0, 0.1, step=0.01)

col4, col5 = st.columns(2)
with col4: run_ = st.button("Start Simulation", use_container_width=True, type="primary")
with col5: reset_ = st.button("Reset", use_container_width=True, type="secondary")
if reset_: st.stop()

# --- BFS Generator ---
def bfs_generator(G, start=0):
    visited, queue = set([start]), deque([start])
    while queue:
        node = queue.popleft()
        for neighbor in G.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
        yield visited.copy()

# --- Plot Graph Function ---
def plot_graph(G, visited, title):
    pos = nx.circular_layout(G)
    fig, ax = plt.subplots(figsize=(4,4), facecolor="#0e1117")
    node_colors = ["#00BFFF" if n in visited else "#555555" for n in G.nodes()]
    nx.draw(G, pos, node_size=20, node_color=node_colors, edge_color="#1c2028", with_labels=False, width=0.6, ax=ax)
    ax.set_title(title, fontsize=12, color="white", pad=8)
    ax.axis("off")
    fig.set_facecolor("#0e1117")
    return fig

# --- Run Simulation ---
if run_:
    st.markdown("### Network Visualization")
    colA, colB, colC = st.columns(3)
    ph_reg, ph_smw, ph_rand = colA.empty(), colB.empty(), colC.empty()

    # Create networks
    networks = {
        "Regular": nx.watts_strogatz_graph(nodes, neighbours, 0.0),
        "Small-World": nx.watts_strogatz_graph(nodes, neighbours, randomness),
        "Random": nx.watts_strogatz_graph(nodes, neighbours, 1.0)
    }

    # BFS generators
    bfs_gens = {k: bfs_generator(g) for k, g in networks.items()}
    placeholders = {"Regular": ph_reg, "Small-World": ph_smw, "Random": ph_rand}

    # Animate BFS faster
    done = False
    while not done:
        done = True
        for _ in range(5):  # advance multiple steps per iteration
            for key in networks:
                try:
                    visited = next(bfs_gens[key])
                    done = False
                except StopIteration:
                    visited = set(networks[key].nodes())
                placeholders[key].pyplot(plot_graph(networks[key], visited, f"{key} Network"), use_container_width=True)
        time.sleep(0.005)

    # --- BFS Spread for Line Chart ---
    def bfs_spread(G):
        visited, queue, levels = set([0]), deque([(0,0)]), {}
        while queue:
            node, depth = queue.popleft()
            levels[depth] = levels.get(depth, 0) + 1
            for n in G.neighbors(node):
                if n not in visited:
                    visited.add(n)
                    queue.append((n, depth+1))
        return levels

    df_all = pd.concat([
        pd.DataFrame({
            "Steps": list(bfs_spread(G).keys()),
            "Nodes Reached": [sum(list(bfs_spread(G).values())[:i+1]) for i in range(len(bfs_spread(G)))],
            "Network": label
        }) for label, G in networks.items()
    ])

    # --- Compact Line Chart ---
    st.markdown("### Message Spread Across Networks")
    fig2, ax2 = plt.subplots(figsize=(10,3), facecolor="#0e1117")  # shorter height
    ax2.set_facecolor("#0e1117")
    colors = {"Regular":"#001F3F","Small-World":"#00BFFF","Random":"#FFA500"}
    for label, data in df_all.groupby("Network"):
        ax2.plot(data["Steps"], data["Nodes Reached"], marker="o", markersize=3, label=label, color=colors[label], linewidth=1.5)
    ax2.set_xlabel("Steps", color="white", fontsize=10)
    ax2.set_ylabel("Total Reached", color="white", fontsize=10)
    ax2.set_title("Message Spread Across Networks", color="white", fontsize=12, pad=8)
    ax2.legend(facecolor="#0e1117", edgecolor="gray", labelcolor="white", fontsize=9)
    ax2.grid(True, color="#1A1A1A")
    ax2.tick_params(colors="white", labelsize=8)
    st.pyplot(fig2, use_container_width=True)

    # --- Result Cards ---
    st.markdown("##### Simulation Results")

    # Prepare data for table
    final_steps = {k: df_all[df_all["Network"]==k]["Steps"].iloc[-1] for k in networks.keys()}
    df_results = pd.DataFrame({
        "Network": list(final_steps.keys()),
        "Steps to Reach Everyone": list(final_steps.values())
    })

    # Display table
    st.table(df_results)

