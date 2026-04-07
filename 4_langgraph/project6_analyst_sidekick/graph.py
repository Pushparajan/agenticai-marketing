# graph.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: ReAct-style LangGraph agent with marketing analytics tools
# Author: Pushparajan Ramar

"""LangGraph ReAct agent for the MarTech Analyst Sidekick.

Builds a stateful, tool-augmented conversational agent that can:
  - Query Amplitude funnels and Google Analytics metrics
  - Execute ad-hoc Python analysis via a sandboxed REPL
  - Search for real-time marketing news and benchmarks
  - Generate matplotlib charts and return them as base64 images

The graph uses ``MemorySaver`` for multi-turn conversation memory and
supports streaming output for real-time UI updates.

Environment variables consumed (via .env):
    OPENAI_API_KEY  - Required for the ChatOpenAI LLM
    USE_MOCK        - "true" (default) or "false" for tool backends
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from datetime import datetime, timezone
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
# State definition
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    """Shared state for the analyst sidekick graph.

    Attributes:
        messages: Conversation history with automatic message merging.
    """

    messages: Annotated[list, add_messages]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the MarTech Analyst Sidekick, an expert marketing \
analytics assistant. You help marketing teams understand their data, identify \
trends, and make data-driven decisions.

## Capabilities
- **Amplitude Funnels**: Query funnel conversion data (signup_to_purchase, \
trial_to_paid, lead_to_demo, or custom funnels).
- **Google Analytics**: Retrieve metrics like sessions, conversion_rate, \
revenue, bounce_rate, email_open_rate, and cac (customer acquisition cost) \
broken down by dimensions.
- **Python Analysis**: Run ad-hoc calculations, data transformations, and \
statistical analysis with pandas and numpy.
- **Web Search**: Look up the latest marketing benchmarks, news, and trends.
- **Charts**: Generate matplotlib visualisations of data.

## Guidelines
1. Always start by querying the relevant data source before answering.
2. Provide specific numbers, percentages, and comparisons — not vague summaries.
3. When showing trends, offer context (industry benchmarks, period-over-period change).
4. Proactively suggest follow-up analyses the user might find valuable.
5. If the user asks about a metric, retrieve it first — don't guess from memory.
6. Use the Python REPL for calculations that go beyond simple lookups.
7. Generate charts when a visual would help communicate the insight.
8. Be concise but thorough. Format output with markdown for readability.
"""


# ---------------------------------------------------------------------------
# LangChain tool wrappers
# ---------------------------------------------------------------------------

@tool
def query_amplitude_funnel_tool(funnel_name: str, date_range: str = "last_quarter") -> str:
    """Query Amplitude for funnel conversion metrics.

    Args:
        funnel_name: Funnel identifier, e.g. "signup_to_purchase",
                     "trial_to_paid", or "lead_to_demo".
        date_range:  Date range such as "last_quarter" or "last_30_days".

    Returns:
        JSON string with funnel steps, conversion rates, and drop-off analysis.
    """
    return query_amplitude_funnel(funnel_name, date_range)


@tool
def query_google_analytics_tool(
    metric: str,
    dimension: str = "source_medium",
    date_range: str = "last_quarter",
) -> str:
    """Query Google Analytics 4 for a marketing metric by dimension.

    Args:
        metric:     Metric name: sessions, conversion_rate, revenue,
                    bounce_rate, email_open_rate, or cac.
        dimension:  Breakdown dimension: source_medium, landing_page,
                    segment, or channel.
        date_range: Date range such as "last_quarter" or "last_30_days".

    Returns:
        JSON string with the metric and dimensional breakdown.
    """
    return query_google_analytics(metric, dimension, date_range)


@tool
def run_python_analysis_tool(code: str) -> str:
    """Execute Python code in a sandboxed REPL with pandas and numpy.

    Use print() to produce output. The namespace includes pd (pandas),
    np (numpy), json, math, datetime, timedelta, mean, median, stdev.

    Args:
        code: Python source code to execute.

    Returns:
        Captured stdout and stderr, or error traceback.
    """
    return run_python_analysis(code)


@tool
def search_marketing_news_tool(query: str) -> str:
    """Search for real-time marketing news, benchmarks, and trends.

    Args:
        query: Natural-language search query about marketing topics.

    Returns:
        JSON string with search results including titles, snippets, and URLs.
    """
    return search_marketing_news(query)


@tool
def generate_chart(data: str, chart_type: str = "bar", title: str = "Chart") -> str:
    """Generate a matplotlib chart and return it as a base64-encoded PNG.

    Args:
        data:       JSON string with chart data. Expected format:
                    {"labels": ["A", "B"], "values": [10, 20]}
                    or {"labels": [...], "series": {"name1": [...], "name2": [...]}}
        chart_type: Chart type — "bar", "line", "pie", or "horizontal_bar".
        title:      Chart title.

    Returns:
        Base64-encoded PNG image string prefixed with 'data:image/png;base64,'.
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

    if chart_type == "pie":
        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=plt.cm.Set3.colors[:len(labels)],
        )
        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    elif chart_type == "line":
        if series:
            for name, vals in series.items():
                ax.plot(labels, vals, marker="o", label=name, linewidth=2)
            ax.legend(loc="best", fontsize=10)
        else:
            ax.plot(labels, values, marker="o", linewidth=2, color="#2563eb")
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis="x", rotation=45)

    elif chart_type == "horizontal_bar":
        y_pos = range(len(labels))
        ax.barh(y_pos, values, color="#2563eb", edgecolor="white", height=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, axis="x", alpha=0.3)

    else:  # default: bar
        if series:
            import numpy as np
            x = np.arange(len(labels))
            width = 0.8 / len(series)
            for i, (name, vals) in enumerate(series.items()):
                ax.bar(x + i * width, vals, width, label=name)
            ax.set_xticks(x + width * (len(series) - 1) / 2)
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
            ax.legend(loc="best", fontsize=10)
        else:
            ax.bar(labels, values, color="#2563eb", edgecolor="white")
            ax.tick_params(axis="x", rotation=45)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, axis="y", alpha=0.3)

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
    """Create the ChatOpenAI instance bound to the tool definitions."""
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
    return ChatOpenAI(model=model_name, temperature=0.1, streaming=True)


def agent_node(state: AgentState) -> dict[str, Any]:
    """Invoke the LLM with the current conversation and tool bindings.

    The LLM decides whether to call a tool or respond directly.
    """
    llm = _get_llm().bind_tools(ALL_TOOLS)

    messages = state["messages"]

    # Prepend system prompt if not already present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    response = llm.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Route to 'tools' if the last message has tool calls, else 'end'."""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the MarTech Analyst Sidekick graph.

    Returns:
        A compiled LangGraph StateGraph with memory checkpointing.
    """
    tool_node = ToolNode(ALL_TOOLS)

    graph_builder = StateGraph(AgentState)

    # Add nodes
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)

    # Add edges
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph_builder.add_edge("tools", "agent")

    # Compile with memory
    memory = MemorySaver()
    graph = graph_builder.compile(checkpointer=memory)

    log.info("MarTech Analyst Sidekick graph compiled successfully")
    return graph


# Module-level compiled graph for import by app.py
graph = build_graph()


# ---------------------------------------------------------------------------
# Convenience: stream or invoke
# ---------------------------------------------------------------------------

def stream_response(
    user_message: str,
    thread_id: str = "default",
) -> Any:
    """Stream the agent's response for a user message.

    Yields events from the graph execution, including tool calls and
    final responses.

    Args:
        user_message: The user's natural-language query.
        thread_id:    Conversation thread ID for memory continuity.

    Yields:
        LangGraph stream events (dict) containing node outputs.
    """
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}

    for event in graph.stream(input_state, config=config, stream_mode="updates"):
        yield event


def invoke_response(
    user_message: str,
    thread_id: str = "default",
) -> str:
    """Invoke the agent and return the final text response.

    Args:
        user_message: The user's natural-language query.
        thread_id:    Conversation thread ID for memory continuity.

    Returns:
        The assistant's final text response.
    """
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}

    result = graph.invoke(input_state, config=config)
    last_message = result["messages"][-1]
    return last_message.content


# ---------------------------------------------------------------------------
# Demo / main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MarTech Analyst Sidekick — Graph Demo")
    print("=" * 60)

    test_queries = [
        "Which channels drove the most pipeline last quarter?",
        "What's our current CAC trend?",
    ]

    thread = "demo-thread-001"

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"USER: {query}")
        print("-" * 60)

        print("\n[Streaming events]")
        for event in stream_response(query, thread_id=thread):
            for node_name, node_output in event.items():
                if node_name == "agent":
                    msg = node_output["messages"][-1]
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"  -> Calling tool: {tc['name']}({json.dumps(tc['args'], indent=2)[:120]}...)")
                    elif hasattr(msg, "content") and msg.content:
                        print(f"\nASSISTANT:\n{msg.content[:500]}")
                elif node_name == "tools":
                    for msg in node_output["messages"]:
                        if isinstance(msg, ToolMessage):
                            preview = msg.content[:150].replace("\n", " ")
                            print(f"  <- Tool result ({msg.name}): {preview}...")
