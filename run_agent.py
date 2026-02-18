#!/usr/bin/env python3
"""Run the sprint demo automation agent once. Intended for cron (e.g. every two weeks)."""
import logging
import sys
from pathlib import Path

# Ensure project root is on path when running as script
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Load config (and .env) before other imports that use config
import config  # noqa: F401

from src.agent import create_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TASK_MESSAGE = "Create the next sprint demo and archive the previous one."


def main():
    try:
        graph = create_graph()
        logger.info("Invoking agent: %s", TASK_MESSAGE)
        result = graph.invoke({"messages": [{"role": "user", "content": TASK_MESSAGE}]})
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            content = getattr(last, "content", str(last))
            logger.info("Agent finished: %s", content)
        else:
            logger.info("Agent finished (no messages in state).")
        return 0
    except Exception as e:
        logger.exception("Agent run failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
