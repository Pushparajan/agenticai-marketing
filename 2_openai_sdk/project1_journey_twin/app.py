# =============================================================================
# app.py
# Project: Customer Journey Digital Twin
# Chapter: 2 - OpenAI Agents SDK
# Description: Dual deployment entry point — FastAPI REST endpoint and Gradio
#              chat UI for interactive testing of the Journey Twin agent.
# Author: Pushparajan Ramar
# =============================================================================

"""Dual deployment for the Customer Journey Digital Twin.

Provides:
- FastAPI endpoint (POST /chat) accepting contact_id and message
- Gradio chat UI for interactive browser-based testing
- __main__ block: Gradio by default, FastAPI with --api flag
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

USE_MOCK: bool = os.getenv("USE_MOCK_APIS", "true").lower() == "true"

logger = logging.getLogger("journey_twin.app")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
def create_fastapi_app() -> Any:
    """Create and configure the FastAPI application.

    Returns:
        A FastAPI app instance with the /chat endpoint registered.
    """
    from fastapi import FastAPI
    from pydantic import BaseModel

    from agent import run_conversation

    app = FastAPI(
        title="Customer Journey Digital Twin API",
        description=(
            "REST API for the Customer Journey Digital Twin agent. "
            "Send a contact_id and message to receive a personalised, "
            "stage-aware response."
        ),
        version="1.0.0",
    )

    class ChatRequest(BaseModel):
        """Incoming chat request payload."""

        contact_id: str
        message: str

    class ChatResponse(BaseModel):
        """Outgoing chat response payload."""

        contact_id: str
        response: str
        escalation: bool

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Return API health status.

        Returns:
            A dict with status and mock mode indicator.
        """
        return {
            "status": "healthy",
            "mock_mode": str(USE_MOCK),
        }

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        """Process a chat message through the Journey Twin agent.

        Args:
            request: The incoming chat request with contact_id and message.

        Returns:
            ChatResponse with the agent's reply and escalation flag.
        """
        logger.info(
            "POST /chat | contact_id=%s | msg_len=%d",
            request.contact_id, len(request.message),
        )

        response_text = await run_conversation(
            contact_id=request.contact_id,
            user_message=request.message,
        )

        escalation = "[ESCALATION NOTICE]" in response_text

        return ChatResponse(
            contact_id=request.contact_id,
            response=response_text,
            escalation=escalation,
        )

    return app


# ---------------------------------------------------------------------------
# Gradio chat interface
# ---------------------------------------------------------------------------
def create_gradio_app() -> Any:
    """Create a Gradio chat interface for the Journey Twin agent.

    Returns:
        A Gradio Blocks app ready for .launch().
    """
    import gradio as gr

    from agent import clear_session, run_conversation

    default_contact_id = "gradio-user-001"

    async def respond(
        message: str,
        history: list[dict[str, str]],
        contact_id: str,
    ) -> str:
        """Handle a user message in the Gradio chat.

        Args:
            message: The user's latest input.
            history: Previous chat turns (managed by Gradio).
            contact_id: The CRM contact ID for session tracking.

        Returns:
            The agent's response string.
        """
        cid = contact_id.strip() or default_contact_id
        logger.info("Gradio chat | contact_id=%s | msg=%s", cid, message[:60])
        response = await run_conversation(
            contact_id=cid,
            user_message=message,
        )
        return response

    def reset_session(contact_id: str) -> tuple[list[Any], str]:
        """Clear the agent session for the given contact.

        Args:
            contact_id: The contact whose session to clear.

        Returns:
            Tuple of (empty chat history, status message).
        """
        cid = contact_id.strip() or default_contact_id
        clear_session(cid)
        logger.info("Session cleared for contact_id=%s", cid)
        return [], f"Session cleared for {cid}"

    with gr.Blocks(
        title="Customer Journey Digital Twin",
        theme=gr.themes.Soft(),
    ) as demo:
        gr.Markdown(
            "# Customer Journey Digital Twin\n"
            "Chat with the AI-powered marketing assistant. "
            "Provide a Contact ID to maintain session context."
        )

        with gr.Row():
            contact_input = gr.Textbox(
                label="Contact ID",
                value=default_contact_id,
                placeholder="Enter CRM contact ID...",
                scale=2,
            )
            clear_btn = gr.Button("Clear Session", scale=1)
            status_output = gr.Textbox(
                label="Status",
                interactive=False,
                scale=2,
            )

        chatbot = gr.ChatInterface(
            fn=respond,
            type="messages",
            additional_inputs=[contact_input],
            title=None,
            examples=[
                "Tell me about your marketing automation platform.",
                "We have fragmented data across 8 tools. Can you help?",
                "What kind of ROI can we expect from your attribution tool?",
                "Can you send me pricing for the Enterprise Suite?",
            ],
        )

        clear_btn.click(
            fn=reset_session,
            inputs=[contact_input],
            outputs=[chatbot.chatbot, status_output],
        )

    return demo


# ---------------------------------------------------------------------------
# Server launchers
# ---------------------------------------------------------------------------
def run_fastapi_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI server with uvicorn.

    Args:
        host: Bind address.
        port: Bind port.
    """
    import uvicorn

    logger.info("Starting FastAPI server on %s:%d", host, port)
    app = create_fastapi_app()
    uvicorn.run(app, host=host, port=port)


def run_gradio_server(
    server_name: str = "0.0.0.0", server_port: int = 7860
) -> None:
    """Start the Gradio chat interface.

    Args:
        server_name: Bind address.
        server_port: Bind port.
    """
    logger.info("Starting Gradio UI on %s:%d", server_name, server_port)
    demo = create_gradio_app()
    demo.launch(server_name=server_name, server_port=server_port)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Customer Journey Digital Twin — Deployment",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start FastAPI server instead of Gradio UI",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Server port (default: 8000 for API, 7860 for Gradio)",
    )

    args = parser.parse_args()

    if args.api:
        port = args.port or 8000
        run_fastapi_server(host=args.host, port=port)
    else:
        port = args.port or 7860
        run_gradio_server(server_name=args.host, server_port=port)
