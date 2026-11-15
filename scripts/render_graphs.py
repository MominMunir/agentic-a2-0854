"""Export compiled LangGraph topology and render publication diagrams offline."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as PlotPath

ROOT = Path(__file__).resolve().parents[1]


def main():
    from langgraph.checkpoint.memory import InMemorySaver
    from agent.graphs.bid_graph import build_graph as bid
    from agent.graphs.conversation_graph import build_graph as conversation

    output = ROOT / "docs/graphs"
    output.mkdir(exist_ok=True)
    for name, builder in [("bid", bid), ("conversation", conversation)]:
        graph = builder(InMemorySaver()).get_graph()
        topology = graph.to_json()
        (output / f"{name}.json").write_text(json.dumps(topology, indent=2), encoding="utf-8")
        (output / f"{name}.mmd").write_text(graph.draw_mermaid(), encoding="utf-8")
        if name == "bid":
            positions = {
                "__start__": (0, 12), "analyst": (-2.6, 10.9),
                "risk_assessor": (0, 10.9), "fit_matcher": (2.6, 10.9),
                "join_analysis": (0, 9.7), "corrective_retrieval": (2.6, 8.9),
                "decide": (0, 8.4), "pricing": (0, 7.3), "writer": (0, 6.2),
                "verifier": (0, 5.1), "critic": (0, 4), "compliance_guard": (0, 2.9),
                "dry_run": (0, 1.8), "human_review": (0, .7), "execute": (0, -.4),
                "__end__": (2.6, -1.5),
            }
            fig, ax = plt.subplots(figsize=(8.3, 11))
            ax.set_xlim(-4.1, 5.3)
            ax.set_ylim(-2.3, 13)
            width, height, size = 2.05, .62, 10
        else:
            ordered = ["__start__", "client_liaison", "verifier", "compliance_guard",
                       "dry_run", "human_review", "execute", "__end__"]
            positions = {node: (0, 7-i) for i, node in enumerate(ordered)}
            fig, ax = plt.subplots(figsize=(6.6, 8.2))
            ax.set_xlim(-2.6, 3.8)
            ax.set_ylim(-.8, 8)
            width, height, size = 3.1, .6, 11
        ax.axis("off")
        patches = {}
        labels = {"__start__": "Start", "__end__": "Stop / complete", "join_analysis": "Join parallel analysis",
                  "risk_assessor": "Risk assessor", "fit_matcher": "Fit matcher", "decide": "Bid / watch / skip",
                  "corrective_retrieval": "Corrective retrieval", "compliance_guard": "Compliance guard",
                  "human_review": "Human approval", "dry_run": "Dry-run preview", "execute": "Approved effect",
                  "client_liaison": "Client liaison"}
        for node in topology["nodes"]:
            key = node["id"]
            x, y = positions[key]
            fill = "#e8f0e4" if key == "human_review" else "#f6f8f7"
            box = FancyBboxPatch((x-width/2, y-height/2), width, height,
                                 boxstyle="round,pad=.06", fc=fill, ec="#648376", lw=1)
            ax.add_patch(box)
            patches[key] = box
            ax.text(x, y, labels.get(key, key.replace("_", " ").capitalize()),
                    ha="center", va="center", fontsize=size, color="#233c35")
        for edge in topology["edges"]:
            src, dst = edge["source"], edge["target"]
            sx, sy = positions[src]
            tx, ty = positions[dst]
            dashed = edge.get("conditional", False)
            kwargs = dict(arrowstyle="-|>", mutation_scale=12, lw=1.05,
                          linestyle="--" if dashed else "-", color="#62796e", zorder=0)
            if name == "bid" and src == "critic" and dst == "writer":
                points = [(sx-width/2-.06,sy),(-2.4,sy),(-2.4,ty),(tx-width/2-.06,ty)]
                ax.add_patch(FancyArrowPatch(path=PlotPath(points), **kwargs))
                ax.text(-2.5,(sy+ty)/2,"Revise at most twice",rotation=90,
                        ha="right",va="center",fontsize=8,color="#40594e")
            elif dst == "__end__" and src != "execute":
                bus = 4.6 if name == "bid" else 3.1
                points = [(sx+width/2+.06,sy),(bus,sy),(bus,ty),(tx+width/2+.06,ty)]
                ax.add_patch(FancyArrowPatch(path=PlotPath(points), **kwargs))
            else:
                ax.add_patch(FancyArrowPatch((sx,sy),(tx,ty),patchA=patches[src],patchB=patches[dst],
                                            shrinkA=5,shrinkB=5,**kwargs))
        ax.set_title("Bid workflow" if name == "bid" else "Conversation workflow",
                     fontsize=17,fontweight="bold",color="#195d4b",pad=15)
        fig.text(.5,.015,"Compiled from source. Dashed lines are conditional paths.",ha="center",fontsize=9,color="#52665c")
        fig.tight_layout(rect=(0,.035,1,.98))
        for extension in ["png", "svg"]:
            fig.savefig(output / f"{name}.{extension}",dpi=180,facecolor="white")
        plt.close(fig)
    print("Both compiled graph diagrams exported as Mermaid, JSON, SVG and PNG.")


if __name__ == "__main__":
    main()
