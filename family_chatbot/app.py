"""
Family Tree Chatbot — Streamlit UI with AIML pattern matching and Prolog reasoning.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import streamlit as st

try:
    import aiml
except ImportError:
    aiml = None  # type: ignore

from prolog_bridge import create_engine, list_family_members

BASE_DIR = Path(__file__).resolve().parent
AIML_PATH = BASE_DIR / "chat.aiml"


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", "", name.strip().lower())


def normalize_relation(rel: str) -> str:
    r = rel.strip().lower().replace("-", " ")
    r = re.sub(r"\s+", "_", r)
    return r


def title_name(name: str) -> str:
    return name.strip().capitalize()


def title_relation(rel: str) -> str:
    return rel.replace("_", " ")


@st.cache_resource
def load_engine():
    return create_engine()


@st.cache_resource
def load_aiml_kernel():
    if aiml is None:
        raise RuntimeError("python-aiml is not installed. Run: pip install python-aiml")
    kernel = aiml.Kernel()
    if AIML_PATH.exists():
        kernel.learn(str(AIML_PATH))
    return kernel


def format_relation_answer(relation: str, person: str, answers: list[str]) -> str:
    person_t = title_name(person)
    rel_t = title_relation(normalize_relation(relation))

    if not answers:
        return f"I don't know the {rel_t} of {person_t}."

    names = ", ".join(title_name(a) for a in answers)
    if len(answers) == 1:
        return f"The {rel_t} of {person_t} is {names}."
    return f"The {rel_t} of {person_t} are {names}."


def format_age_answer(person: str, ages: list[str]) -> str:
    person_t = title_name(person)
    if not ages:
        return f"I don't have age information for {person_t}."
    return f"{person_t} is {ages[0]} years old."


def parse_aiml_prolog_line(response: str) -> tuple[str, str, str] | None:
    """Parse 'haider IS father OF ali' from second AIML respond."""
    m = re.match(r"^(\w+)\s+IS\s+([\w\s]+)\s+OF\s+(\w+)\s*$", response.strip(), re.I)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None


def get_bot_reply(user_text: str, kernel, engine) -> str:
    text = user_text.strip()
    if not text:
        return "Please type a question."

    kernel.setPredicate("rel", "")
    kernel.setPredicate("p1", "")
    kernel.setPredicate("p2", "")
    first = kernel.respond(text.upper())

    if first == "MEMBERS_LIST":
        members = ", ".join(title_name(m) for m in list_family_members())
        return f"Family members: {members}."

    rel = kernel.getPredicate("rel") or ""
    p1 = kernel.getPredicate("p1") or ""

    if rel and p1:
        answers = engine.query_relation(rel, p1)
        kernel.setPredicate("p2", ",".join(answers) if answers else "unknown")
        second = kernel.respond(text.upper())

        if normalize_relation(rel) == "age":
            if answers:
                return format_age_answer(p1, answers)
            return format_age_answer(p1, [])

        if second and " IS " in second.upper() and " OF " in second.upper():
            parsed = parse_aiml_prolog_line(second)
            if parsed:
                answer_name, _, _ = parsed
                if answer_name.lower() != "unknown":
                    return format_relation_answer(rel, p1, [answer_name])

        if answers:
            return format_relation_answer(rel, p1, answers)

        return format_relation_answer(rel, p1, [])

    return first.strip() if first else "I did not understand that. Type HELP for examples."


def main() -> None:
    st.set_page_config(page_title="Family Tree Chatbot", page_icon="🌳", layout="centered")
    st.title("🌳 Family Tree Chatbot")
    st.caption("Ask about relationships in natural language — powered by AIML, Prolog, and Streamlit.")

    try:
        engine, engine_label = load_engine()
        kernel = load_aiml_kernel()
    except Exception as exc:
        st.error(f"Could not start the chatbot: {exc}\n\nRun: pip install -r requirements.txt")
        st.stop()

    st.caption(f"Reasoning engine: {engine_label}")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I can answer questions about our family tree. "
                    "Try: **Who is the father of Ali?** or type **HELP**."
                ),
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask a family question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = get_bot_reply(prompt, kernel, engine)
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
