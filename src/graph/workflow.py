from langgraph.graph import StateGraph, START, END
from src.graph.state import BotnetState
from src.graph.nodes import node_extract_features, node_predict_botnet, node_firewall_rule

builder = StateGraph(BotnetState)

builder.add_node("extractor", node_extract_features)
builder.add_node("detector", node_predict_botnet)
builder.add_node("firewall", node_firewall_rule)

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "detector")
builder.add_edge("detector", "firewall")
builder.add_edge("firewall", END)

botnet_agent = builder.compile()
