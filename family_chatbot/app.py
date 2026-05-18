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

from prolog_bridge import create_engine, list_family_members, normalize_relation_name

BASE_DIR = Path(__file__).resolve().parent
AIML_PATH = BASE_DIR / "chat.aiml"
PL_PATH = BASE_DIR / "family_kb.pl"


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", "", name.strip().lower())


def normalize_relation(rel: str) -> str:
    return normalize_relation_name(rel)


def preprocess_input(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[?.!,;:]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.upper()


def title_name(name: str) -> str:
    return name.strip().capitalize()


def title_relation(rel: str) -> str:
    return rel.replace("_", " ")


@st.cache_resource
def load_engine(_kb_mtime: float):
    return create_engine()


@st.cache_resource
def load_aiml_kernel(_aiml_mtime: float):
    if aiml is None:
        raise RuntimeError("python-aiml is not installed. Run: pip install python-aiml")
    kernel = aiml.Kernel()
    if AIML_PATH.exists():
        kernel.learn(str(AIML_PATH))
    return kernel


def join_names(names: list[str]) -> str:
    if not names:
        return ""
    titles = [title_name(n) for n in names]
    if len(titles) == 1:
        return titles[0]
    if len(titles) == 2:
        return f"{titles[0]} and {titles[1]}"
    return ", ".join(titles[:-1]) + f", and {titles[-1]}"


def pluralize_relation(rel: str) -> str:
    rel = rel.strip().lower()
    plurals = {
        "parent": "parents",
        "child": "children",
        "grandparent": "grandparents",
        "grandfather": "grandfathers",
        "grandmother": "grandmothers",
        "grandchild": "grandchildren",
        "sibling": "siblings",
        "brother": "brothers",
        "sister": "sisters",
        "son": "sons",
        "daughter": "daughters",
        "uncle": "uncles",
        "aunt": "aunts",
        "cousin": "cousins",
        "nephew": "nephews",
        "niece": "nieces",
        "husband": "husbands",
        "wife": "wives",
        "spouse": "spouses",
        "ancestor": "ancestors",
        "descendant": "descendants",
        "father_in_law": "fathers-in-law",
        "mother_in_law": "mothers-in-law",
        "brother_in_law": "brothers-in-law",
        "sister_in_law": "sisters-in-law",
        "elder_sibling": "elder siblings",
        "younger_sibling": "younger siblings",
        "paternal_grandfather": "paternal grandfathers",
    }
    r_key = rel.replace(" ", "_")
    if r_key in plurals:
        return plurals[r_key]
    if rel.endswith("y"):
        return rel[:-1] + "ies"
    if rel.endswith("s") or rel.endswith("ch") or rel.endswith("sh"):
        return rel + "es"
    return rel + "s"


def format_relation_answer(relation: str, person: str, answers: list[str]) -> str:
    person_t = title_name(person)
    rel_norm = normalize_relation(relation)

    if not answers:
        rel_t = title_relation(rel_norm).lower()
        return f"I don't know the {rel_t} of {person_t}."

    names = join_names(answers)
    if len(answers) == 1:
        rel_t = title_relation(rel_norm).lower()
        return f"The {rel_t} of {person_t} is {names}."
    else:
        rel_t = title_relation(pluralize_relation(rel_norm)).lower()
        return f"The {rel_t} of {person_t} are {names}."



def format_age_answer(person: str, ages: list[str]) -> str:
    person_t = title_name(person)
    if not ages:
        return f"I don't have age information for {person_t}."
    return f"{person_t} is {ages[0]} years old."


LIST_DISPLAY = {
    "list_male": ("male member", "male members"),
    "list_female": ("female member", "female members"),
    "list_parent": ("parent", "parents"),
    "list_child": ("child", "children"),
    "list_son": ("son", "sons"),
    "list_daughter": ("daughter", "daughters"),
    "list_sibling": ("person with siblings", "people with siblings"),
    "list_married": ("married couple", "married couples"),
    "list_age": ("age record", "age records"),
    "list_father": ("father", "fathers"),
    "list_mother": ("mother", "mothers"),
    "list_grandfather": ("grandfather", "grandfathers"),
    "list_grandmother": ("grandmother", "grandmothers"),
    "list_grandparent": ("grandparent", "grandparents"),
    "list_brother": ("brother", "brothers"),
    "list_sister": ("sister", "sisters"),
    "list_uncle": ("uncle", "uncles"),
    "list_aunt": ("aunt", "aunts"),
    "list_cousin": ("cousin", "cousins"),
    "list_nephew": ("nephew", "nephews"),
    "list_niece": ("niece", "nieces"),
    "list_husband": ("husband", "husbands"),
    "list_wife": ("wife", "wives"),
    "list_spouse": ("spouse", "spouses"),
    "list_father_in_law": ("father-in-law", "fathers-in-law"),
    "list_mother_in_law": ("mother-in-law", "mothers-in-law"),
    "list_brother_in_law": ("brother-in-law", "brothers-in-law"),
    "list_sister_in_law": ("sister-in-law", "sisters-in-law"),
    "list_elder_sibling": ("elder sibling", "elder siblings"),
    "list_younger_sibling": ("younger sibling", "younger siblings"),
    "list_paternal_grandfather": ("paternal grandfather", "paternal grandfathers"),
}

# Maps many phrasings ("male", "all males", "every female") to list query types.
LIST_KEYWORD_MAP = {
    "MALE": "list_male",
    "MALES": "list_male",
    "FEMALE": "list_female",
    "FEMALES": "list_female",
    "PARENT": "list_parent",
    "PARENTS": "list_parent",
    "CHILD": "list_child",
    "CHILDREN": "list_child",
    "KID": "list_child",
    "KIDS": "list_child",
    "SON": "list_son",
    "SONS": "list_son",
    "DAUGHTER": "list_daughter",
    "DAUGHTERS": "list_daughter",
    "SIBLING": "list_sibling",
    "SIBLINGS": "list_sibling",
    "AGE": "list_age",
    "AGES": "list_age",
    "MARRIED": "list_married",
    "MARRIED COUPLES": "list_married",
    "COUPLES": "list_married",
    "FATHER": "list_father",
    "FATHERS": "list_father",
    "MOTHER": "list_mother",
    "MOTHERS": "list_mother",
    "GRANDFATHER": "list_grandfather",
    "GRANDFATHERS": "list_grandfather",
    "GRANDMOTHER": "list_grandmother",
    "GRANDMOTHERS": "list_grandmother",
    "GRANDPARENT": "list_grandparent",
    "GRANDPARENTS": "list_grandparent",
    "BROTHER": "list_brother",
    "BROTHERS": "list_brother",
    "SISTER": "list_sister",
    "SISTERS": "list_sister",
    "UNCLE": "list_uncle",
    "UNCLES": "list_uncle",
    "AUNT": "list_aunt",
    "AUNTS": "list_aunt",
    "COUSIN": "list_cousin",
    "COUSINS": "list_cousin",
    "NEPHEW": "list_nephew",
    "NEPHEWS": "list_nephew",
    "NIECE": "list_niece",
    "NIECES": "list_niece",
    "HUSBAND": "list_husband",
    "HUSBANDS": "list_husband",
    "WIFE": "list_wife",
    "WIVES": "list_wife",
    "SPOUSE": "list_spouse",
    "SPOUSES": "list_spouse",
    "FATHER IN LAW": "list_father_in_law",
    "FATHERS IN LAW": "list_father_in_law",
    "MOTHER IN LAW": "list_mother_in_law",
    "MOTHERS IN LAW": "list_mother_in_law",
    "BROTHER IN LAW": "list_brother_in_law",
    "BROTHERS IN LAW": "list_brother_in_law",
    "SISTER IN LAW": "list_sister_in_law",
    "SISTERS IN LAW": "list_sister_in_law",
    "ELDER SIBLING": "list_elder_sibling",
    "ELDER SIBLINGS": "list_elder_sibling",
    "YOUNGER SIBLING": "list_younger_sibling",
    "YOUNGER SIBLINGS": "list_younger_sibling",
    "PATERNAL GRANDFATHER": "list_paternal_grandfather",
    "PATERNAL GRANDFATHERS": "list_paternal_grandfather",
    "MEMBER": "members",
    "MEMBERS": "members",
}

LIST_PREFIXES = (
    "TELL ME ",
    "SHOW ME ",
    "SHOW ",
    "LIST ALL ",
    "LIST OF ALL ",
    "LIST OF ",
    "LIST ",
    "WHAT ARE ALL THE ",
    "WHAT ARE ALL ",
    "WHAT ARE THE ",
    "WHAT ARE ",
    "WHO ARE ALL THE ",
    "WHO ARE ALL ",
    "WHO ARE THE ",
    "WHO ARE ",
    "WHO IS THE ",
    "WHO IS ",
    "WHO IS A ",
    "WHO ARE A ",
    "GIVE ME ",
    "GIVE ALL ",
    "GIVE ",
    "NAMES OF ALL ",
    "NAMES OF ",
    "NAME ALL ",
    "ALL THE ",
    "ALL ",
    "EVERY ",
    "THE ",
)


def detect_list_intent(text: str) -> str | None:
    """Detect 'all males', 'male', 'females', etc. (not 'father of ali')."""
    core = text.upper().strip()
    changed = True
    while changed:
        changed = False
        for prefix in LIST_PREFIXES:
            if core.startswith(prefix):
                core = core[len(prefix) :].strip()
                changed = True
                break

    if re.search(r"\bOF\b", core):
        return None

    if core in LIST_KEYWORD_MAP:
        return LIST_KEYWORD_MAP[core]

    return None


def format_list_answer(list_type: str, items: list[str]) -> str:
    singular, plural = LIST_DISPLAY.get(list_type, ("entry", "entries"))

    if not items:
        return f"I could not find any {plural} in the family knowledge base."

    if list_type == "list_age":
        lines = [f"- {title_name(name)}: {age} years" for name, age in (i.split(":", 1) for i in items)]
        return "Ages in the family:\n" + "\n".join(lines)

    if list_type == "list_married":
        couples = []
        for item in items:
            h, w = item.split(":", 1)
            couples.append(f"{title_name(h)} & {title_name(w)}")
        return "Married couples: " + ", ".join(couples) + "."

    names = ", ".join(title_name(n) for n in items)
    if len(items) == 1:
        return f"There is 1 {singular} in the family: {names}."
    return f"All {plural} in the family ({len(items)}): {names}."


def parse_aiml_prolog_line(response: str) -> tuple[str, str, str] | None:
    """Parse 'haider IS father OF ali' from second AIML respond."""
    m = re.match(r"^(\w+)\s+IS\s+([\w\s]+)\s+OF\s+(\w+)\s*$", response.strip(), re.I)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None


def format_inverse_relation_answer(relation: str, person: str, answers: list[str]) -> str:
    person_t = title_name(person)
    rel_t = title_relation(normalize_relation(relation)).lower()

    if rel_t in ["married", "married to", "spouse"]:
        phrasing = "married to"
    else:
        phrasing = f"the {rel_t} of"

    if not answers:
        return f"I don't know who {person_t} is {phrasing}."

    names = join_names(answers)
    return f"{person_t} is {phrasing} {names}."


def resolve_pronouns(clause: str, context_person: str) -> str:
    c = clause.lower().strip()
    if "age" in c or "old" in c:
        return f"how old is {context_person}"
    c = re.sub(r'\b(he|she|him|his|her)\b', context_person, c)
    return c


def process_user_input(user_text: str, members: list[str]) -> list[str]:
    clauses = re.split(
        r'\s+and\s+(?=his\b|her\b|how\b|what\b|who\b|she\b|he\b|age\b|also\b)|\s+also\s+|\s*;\s*',
        user_text,
        flags=re.IGNORECASE
    )
    
    processed_clauses = []
    context_person = None
    
    for i, clause in enumerate(clauses):
        clause_str = clause.strip()
        if not clause_str:
            continue
            
        words = re.findall(r'\b\w+\b', clause_str.lower())
        for word in words:
            if word in members:
                context_person = word
                break
        
        if i > 0 and context_person:
            clause_str = resolve_pronouns(clause_str, context_person)
            
        processed_clauses.append(clause_str)
        
    return processed_clauses


def get_single_bot_reply(user_text: str, kernel, engine) -> str:
    text = preprocess_input(user_text)
    if not text:
        return "Please type a question."

    list_intent = detect_list_intent(text)
    if list_intent == "members":
        members = ", ".join(title_name(m) for m in list_family_members())
        return f"Every family member ({len(list_family_members())}): {members}."
    if list_intent:
        return format_list_answer(list_intent, engine.query_list(list_intent))

    kernel.setPredicate("rel", "")
    kernel.setPredicate("p1", "")
    kernel.setPredicate("p2", "")
    kernel.setPredicate("verify_p1", "")
    kernel.setPredicate("inverse", "")
    first = kernel.respond(text)

    if first == "MEMBERS_LIST":
        members = ", ".join(title_name(m) for m in list_family_members())
        return f"Family members: {members}."

    verify_p1 = kernel.getPredicate("verify_p1") or ""
    rel = kernel.getPredicate("rel") or ""
    p1 = kernel.getPredicate("p1") or ""
    inverse = kernel.getPredicate("inverse") or ""
    is_inv = (inverse.lower() == "true")

    if rel.startswith("list_"):
        return format_list_answer(rel, engine.query_list(rel))

    if verify_p1 and rel and p1:
        answers = engine.query_relation(rel, p1, inverse=is_inv)
        verify_p1_norm = normalize_name(verify_p1)
        answers_norm = [normalize_name(a) for a in answers]
        
        verify_p1_title = title_name(verify_p1)
        p1_title = title_name(p1)
        rel_title = title_relation(normalize_relation(rel))
        
        if verify_p1_norm in answers_norm:
            return f"Yes, {verify_p1_title} is the {rel_title} of {p1_title}."
        else:
            if answers:
                actual = join_names(answers)
                if len(answers) == 1:
                    return f"No, {verify_p1_title} is not the {rel_title} of {p1_title}. The {rel_title} of {p1_title} is {actual}."
                else:
                    return f"No, {verify_p1_title} is not the {rel_title} of {p1_title}. The {rel_title} of {p1_title} are {actual}."
            else:
                return f"No, {verify_p1_title} is not the {rel_title} of {p1_title}. I don't know who the {rel_title} of {p1_title} is."

    if rel and p1:
        answers = engine.query_relation(rel, p1, inverse=is_inv)
        kernel.setPredicate("p2", ",".join(answers) if answers else "unknown")
        second = kernel.respond(text)

        if normalize_relation(rel) == "age":
            if answers:
                return format_age_answer(p1, answers)
            return format_age_answer(p1, [])

        if is_inv:
            return format_inverse_relation_answer(rel, p1, answers)

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


def get_bot_reply(user_text: str, kernel, engine) -> str:
    members = [m.lower() for m in list_family_members()]
    sub_queries = process_user_input(user_text, members)
    
    replies = []
    for q in sub_queries:
        reply = get_single_bot_reply(q, kernel, engine)
        replies.append(reply)
        
    if len(replies) == 1:
        return replies[0]
    
    formatted_replies = []
    for r in replies:
        r = r.strip()
        if not r.endswith(('.', '?', '!')):
            r += '.'
        if r:
            r = r[0].upper() + r[1:]
        formatted_replies.append(r)
        
    return " Also, ".join(formatted_replies)


def main() -> None:
    st.set_page_config(page_title="Family Tree Chatbot", page_icon="🌳", layout="centered")
    st.title("🌳 Family Tree Chatbot")
    st.caption("Ask about relationships in natural language — powered by AIML, Prolog, and Streamlit.")

    kb_mtime = PL_PATH.stat().st_mtime if PL_PATH.exists() else 0.0
    aiml_mtime = AIML_PATH.stat().st_mtime if AIML_PATH.exists() else 0.0

    try:
        engine, engine_label = load_engine(kb_mtime)
        kernel = load_aiml_kernel(aiml_mtime)
    except Exception as exc:
        st.error(f"Could not start the chatbot: {exc}\n\nRun: pip install -r requirements.txt")
        st.stop()

    st.caption(f"Reasoning engine: {engine_label}")

    with st.sidebar:
        st.markdown("### Tips")
        st.markdown(
            "- **Who is the father of Ali?**\n"
            "- **Parents of Ali** / **Children of Haider**\n"
            "- **Wife of Haider** / **All males**\n"
            "- **List ages** / **MEMBERS**"
        )
        if st.button("Reload family data"):
            load_engine.clear()
            load_aiml_kernel.clear()
            st.rerun()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I can answer questions about our family tree. "
                    "Try: **Who is the father of Ali?**, **All males**, or type **HELP**."
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
