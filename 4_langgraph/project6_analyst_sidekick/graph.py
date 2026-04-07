# graph.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: ReAct-style LangGraph agent with marketing analytics tools
# Author: Pushparajan Ramar

"""LangGraph ReAct agent for the MarTech Analyst Sidekick.

Stateful, tool-augmented agent that queries Amplitude funnels, GA4 metrics,
runs Python analysis, searches marketing news, and generates charts.
Uses MemorySaver for multi-turn memory and supports streaming output.

Environment variables: OPENAI_API_KEY (required), USE_MOCK (default "true").
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from typing import Annotated, Any

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from tools.analytics_tools import query_amplitude_funnel, query_google_analytics
from tools.python_repl import run_python_analysis
from tools.web_search import search_marketing_news

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Shared state — conversation history with automatic message merging."""
    messages: Annotated[list, add_messages]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the MarTech Analyst Sidekick, an expert marketing analytics assistant \
that helps teams understand data, identify trends, and make data-driven decisions.

Capabilities: Amplitude funnels (signup_to_purchase, trial_to_paid, lead_to_demo), \
Google Analytics metrics (sessions, conversion_rate, revenue, bounce_rate, \
email_open_rate, cac), Python REPL (pandas/numpy), web search for benchmarks, \
and matplotlib chart generation.

Guidelines:
1. Query data sources before answering — never guess from memory.
2. Provide specific numbers, percentages, and comparisons.
3. Offer context: industry benchmarks, period-over-period change.
4. Suggest follow-up analyses the user might find valuable.
5. Use Python REPL for calculations beyond simple lookups.
6. Generate charts when a visual would help communicate the insight.
7. Be concise but thorough. Use markdown for readability.
"""


# ---------------------------------------------------------------------------
# LangChain tool wrappers
# ---------------------------------------------------------------------------

@tool
def query_amplitude_funnel_tool(funnel_name: str, date_range: str = "last_quarter") -> str:
    """Query Amplitude for funnel conversion metrics (steps, rates, drop-offs).

    Args:
        funnel_name: e.g. "signup_to_purchase", "trial_to_paid", "lead_to_demo".
        date_range:  e.g. "last_quarter" or "last_30_days".
    """
    return query_amplitude_funnel(funnel_name, date_range)


@tool
def query_google_analytics_tool(
    metric: str, dimension: str = "source_medium", date_range: str = "last_quarter",
) -> str:
    """Query GA4 for a marketing metric broken down by dimension.

    Args:
        metric:    sessions, conversion_rate, revenue, bounce_rate, email_open_rate, or cac.
        dimension: source_medium, landing_page, segment, or channel.
        date_range: e.g. "last_quarter" or "last_30_days".
    """
    return query_google_analytics(metric, dimension, date_range)


@tool
def run_python_analysis_tool(code: str) -> str:
    """Execute Python code in a sandboxed REPL with pandas (pd), numpy (np), json, math.

    Use print() to produce output. Returns captured stdout/stderr or error traceback.
    """
    return run_python_analysis(code)


@tool
def search_marketing_news_tool(query: str) -> str:
    """Search for real-time marketing news, benchmarks, and trends.

    Args:
        query: Natural-language search query about marketing topics.
    """
    return search_marketing_news(query)


@tool
def generate_chart(data: str, chart_type: str = "bar", title: str = "Chart") -> str:
    """Generate a matplotlib chart and return it as a base64-encoded PNG.

    Args:
        data:       JSON string: {"labels": [...], "values": [...]} or
                    {"labels": [...], "series": {"name1": [...], ...}}.
        chart_type: "bar", "line", "pie", or "horizontal_bar".
        title:      Chart title.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        chart_data = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError as exc:
        return f"[ERROR] Invalid JSON data: {exc}"

    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    series = chart_data.get("series", {})

    fig, ax = plt.subplots(figsize=(10, 6))
    color = "#2563eb"

    if chart_type == "pie":
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=140,
               colors=plt.cm.Set3.colors[:len(labels)])
    elif chart_type == "line":
        if series:
            for name, vals in series.items():
                ax.plot(labels, vals, marker="o", label=name, linewidth=2)
            ax.legend(loc="best")
        else:
            ax.plot(labels, values, marker="o", linewidth=2, color=color)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)
    elif chart_type == "horizontal_bar":
        ax.barh(range(len(labels)), values, color=color, height=0.6)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.grid(True, axis="x", alpha=0.3)
    else:  # bar
        if series:
            import numpy as np
            x = np.arange(len(labels))
            w = 0.8 / len(series)
            for i, (name, vals) in enumerate(series.items()):
                ax.bar(x + i * w, vals, w, label=name)
            ax.set_xticks(x + w * (len(series) - 1) / 2)
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.legend(loc="best")
        else:
            ax.bar(labels, values, color=color)
            ax.tick_params(axis="x", rotation=45)
        ax.grid(True, axis="y", alpha=0.3)
    ax.set_title(title, fontsize=14, fontweight="bold")

    plt.tight_layout()

    # Encode to base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")

    log.info("Generated %s chart: '%s' (%d labels)", chart_type, title, len(labels))
    return f"data:image/png;base64,{b64}"


# ---------------------------------------------------------------------------
# Tool list
# ---------------------------------------------------------------------------

ALL_TOOLS = [
    query_amplitude_funnel_tool,
    query_google_analytics_tool,
    run_python_analysis_tool,
    search_marketing_news_tool,
    generate_chart,
]

TOOL_NAMES = {t.name for t in ALL_TOOLS}


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def _get_llm() -> ChatOpenAI:
    """Create the ChatOpenAI instance with tool bindings."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0.1, streaming=True,
    )


def agent_node(state: AgentState) -> dict[str, Any]:
    """Invoke the LLM — it decides whether to call a tool or respond."""
    llm = _get_llm().bind_tools(ALL_TOOLS)
    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
    return {"messages": [llm.invoke(messages)]}


def should_continue(state: AgentState) -> str:
    """Route to 'tools' if the last message has tool calls, else end."""
    last = state["messages"][-1]
    return "tools" if hasattr(last, "tool_calls") and last.tool_calls else END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the ReAct graph with MemorySaver checkpointing."""
    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    compiled = builder.compile(checkpointer=MemorySaver())
    log.info("MarTech Analyst Sidekick graph compiled successfully")
    return compiled


# Module-level compiled graph for import by app.py
graph = build_graph()


def stream_response(user_message: str, thread_id: str = "default") -> Any:
    """Stream graph events for a user message. Yields node update dicts."""
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}
    for event in graph.stream(input_state, config=config, stream_mode="updates"):
        yield event


def invoke_response(user_message: str, thread_id: str = "default") -> str:
    """Invoke the agent and return the final text response."""
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}
    result = graph.invoke(input_state, config=config)
    return result["messages"][-1].content


if __name__ == "__main__":
    print("=" * 60)
    print("MarTech Analyst Sidekick — Graph Demo")
    print("=" * 60)

    thread = "demo-thread-001"
    for query in ["Which channels drove the most pipeline last quarter?",
                  "What's our current CAC trend?"]:
        print(f"\nUSER: {query}\n" + "-" * 60)
        for event in stream_response(query, thread_id=thread):
            for node_name, node_output in event.items():
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"  -> Tool: {tc['name']}({json.dumps(tc['args'])[:100]})")
                    elif isinstance(msg, ToolMessage):
                        print(f"  <- {msg.name}: {msg.content[:120].replace(chr(10), ' ')}...")
                    elif isinstance(msg, AIMessage) and msg.content:
                        print(f"\nASSISTANT:\n{msg.content[:500]}")
