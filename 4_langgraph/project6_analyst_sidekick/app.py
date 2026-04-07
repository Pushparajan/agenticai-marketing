# app.py
# Project 6: MarTech Analyst Sidekick
# Chapter Reference: Chapter 4 - LangGraph
# Description: Gradio chat UI with real-time tool call visibility
# Author: Pushparajan Ramar

"""Gradio chat interface for the MarTech Analyst Sidekick.

Conversational UI with real-time tool call visibility.  Run: ``python app.py``

Environment variables: OPENAI_API_KEY (required), USE_MOCK (default "true"),
GRADIO_SERVER_PORT (default 7860).
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Generator

import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from graph import graph, TOOL_NAMES

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOOL_DISPLAY_NAMES: dict[str, str] = {
    "query_amplitude_funnel_tool": "Querying Amplitude Funnels",
    "query_google_analytics_tool": "Querying Google Analytics",
    "run_python_analysis_tool": "Running Python Analysis",
    "search_marketing_news_tool": "Searching Marketing News",
    "generate_chart": "Generating Chart",
}

EXAMPLE_QUERIES: list[str] = [
    "Which channels drove most pipeline last quarter?",
    "Show me email open rates by segment",
    "What's our CAC trend?",
    "Walk me through our signup-to-purchase funnel conversion rates",
    "Compare our email performance across segments and suggest improvements",
    "Search for the latest B2B marketing benchmarks and compare to our data",
]


def _new_thread_id() -> str:
    """Generate a unique thread ID for conversation memory."""
    return f"gradio-{uuid.uuid4().hex[:12]}"


def chat_handler(
    user_message: str,
    history: list[dict[str, str]],
    thread_id: str,
) -> Generator[tuple[list[dict[str, str]], str], None, None]:
    """Stream agent responses, yielding (updated_history, thread_id) tuples."""
    if not user_message.strip():
        yield history, thread_id
        return

    # Append user message
    history = history + [{"role": "user", "content": user_message}]

    # Prepare streaming config
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}

    # Track tool calls for display
    tool_call_log: list[str] = []
    final_content: str = ""
    chart_images: list[str] = []

    try:
        for event in graph.stream(input_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                messages = node_output.get("messages", [])

                for msg in messages:
                    # --- Agent decides to call tools ---
                    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_label = TOOL_DISPLAY_NAMES.get(tc["name"], tc["name"])
                            args_preview = _format_tool_args(tc["args"])
                            tool_call_log.append(f"**{tool_label}** {args_preview}")

                            # Show tool calls as a status in the chat
                            status_md = _build_tool_status(tool_call_log, in_progress=True)
                            active_history = history + [
                                {"role": "assistant", "content": status_md}
                            ]
                            yield active_history, thread_id

                    # --- Tool results come back ---
                    elif isinstance(msg, ToolMessage):
                        log.info("Tool '%s' returned %d chars", msg.name, len(msg.content))

                        # Check for chart images in tool results
                        if msg.name == "generate_chart" and msg.content.startswith("data:image/png;base64,"):
                            chart_images.append(msg.content)

                    # --- Final agent response ---
                    elif isinstance(msg, AIMessage) and msg.content:
                        if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                            final_content = msg.content

    except Exception as exc:
        log.error("Agent error: %s", exc, exc_info=True)
        final_content = (
            f"I encountered an error while processing your request: {exc}\n\n"
            "Please check that your OPENAI_API_KEY is set correctly and try again."
        )

    # Build the final response with tool status + content
    response_parts: list[str] = []

    if tool_call_log:
        response_parts.append(_build_tool_status(tool_call_log, in_progress=False))

    if final_content:
        response_parts.append(final_content)

    # Append chart images as markdown
    for img_data in chart_images:
        response_parts.append(f"\n\n![Chart]({img_data})")

    full_response = "\n\n".join(response_parts) if response_parts else "I wasn't able to generate a response. Please try again."

    history = history[:-1] if history and history[-1].get("role") == "assistant" else history
    history = history + [{"role": "assistant", "content": full_response}]

    yield history, thread_id


def _format_tool_args(args: dict[str, Any]) -> str:
    """Format tool arguments for concise display."""
    if not args:
        return ""
    parts = []
    for key, value in args.items():
        if isinstance(value, str) and len(value) > 60:
            value = value[:57] + "..."
        parts.append(f"`{key}={value}`")
    return " | ".join(parts)


def _build_tool_status(tool_calls: list[str], in_progress: bool = True) -> str:
    """Build a markdown status block showing tool call progress."""
    icon = "..." if in_progress else "Done"
    header = f"**Agent Actions** [{icon}]"
    items = "\n".join(f"- {tc}" for tc in tool_calls)
    return f"{header}\n{items}"


def build_ui() -> gr.Blocks:
    """Construct the Gradio Blocks interface.

    Returns:
        A configured ``gr.Blocks`` application ready to launch.
    """
    with gr.Blocks(
        title="MarTech Analyst Sidekick",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
        ),
        css="""
        .tool-status { background: #f0f4ff; border-left: 3px solid #2563eb;
                       padding: 8px 12px; margin-bottom: 8px; font-size: 0.9em; }
        footer { display: none !important; }
        """,
    ) as demo:
        # State
        thread_state = gr.State(value=_new_thread_id)

        # Header
        gr.Markdown(
            """
            # MarTech Analyst Sidekick
            *Your AI-powered marketing analytics assistant.  Ask questions about
            funnels, traffic, CAC, email performance, and more.*

            **Powered by:** LangGraph ReAct Agent + Amplitude + Google Analytics + Python REPL
            """
        )

        # Chat interface
        chatbot = gr.Chatbot(
            label="Conversation",
            height=520,
            type="messages",
            show_copy_button=True,
            avatar_images=(None, "https://em-content.zobj.net/source/twitter/408/bar-chart_1f4ca.png"),
            render_markdown=True,
        )

        # Input row
        with gr.Row():
            msg_input = gr.Textbox(
                placeholder="Ask a marketing analytics question...",
                label="Your question",
                scale=8,
                container=False,
                autofocus=True,
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        # Example queries
        gr.Examples(
            examples=[[q] for q in EXAMPLE_QUERIES],
            inputs=[msg_input],
            label="Try these example queries",
        )

        # Controls row
        with gr.Row():
            clear_btn = gr.Button("Clear conversation", variant="secondary", size="sm")
            new_session_btn = gr.Button("New session", variant="secondary", size="sm")

        with gr.Accordion("About this agent", open=False):
            gr.Markdown(
                "**Tools:** Amplitude Funnels | Google Analytics | Python REPL "
                "(pandas/numpy) | Web Search | Chart Generator (bar/line/pie)\n\n"
                "Uses a **ReAct** loop: reason, call tools, analyse results, respond.\n\n"
                "*Built with LangGraph + Gradio for "
                '"Mastering Agentic AI for Marketing Technology" by Pushparajan Ramar.*'
            )

        # ----- Event handlers -----

        def on_submit(
            user_message: str,
            history: list[dict[str, str]],
            thread_id: str,
        ) -> Generator[tuple[str, list[dict[str, str]], str], None, None]:
            """Handle message submission with streaming updates."""
            for updated_history, tid in chat_handler(user_message, history, thread_id):
                yield "", updated_history, tid

        def on_clear() -> tuple[list, str]:
            """Clear the conversation and start a new thread."""
            return [], _new_thread_id()

        # Wire up submit
        submit_event = msg_input.submit(
            fn=on_submit,
            inputs=[msg_input, chatbot, thread_state],
            outputs=[msg_input, chatbot, thread_state],
        )

        send_btn.click(
            fn=on_submit,
            inputs=[msg_input, chatbot, thread_state],
            outputs=[msg_input, chatbot, thread_state],
        )

        clear_btn.click(
            fn=on_clear,
            outputs=[chatbot, thread_state],
        )

        new_session_btn.click(
            fn=on_clear,
            outputs=[chatbot, thread_state],
        )

    return demo


app = build_ui()

if __name__ == "__main__":
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    log.info("Launching MarTech Analyst Sidekick on port %d", port)

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
    )
