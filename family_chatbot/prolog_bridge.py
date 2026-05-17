"""
Bridge to SWI-Prolog via pyswip, with Python fallback that reads family_kb.pl.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Protocol

PL_PATH = Path(__file__).resolve().parent / "family_kb.pl"

SWIPL_SEARCH_PATHS = [
    r"C:\Program Files\swipl\bin",
    r"C:\Program Files (x86)\swipl\bin",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\SWI-Prolog\bin"),
]

_FACT_RE = re.compile(
    r"^\s*(parent|male|female|married|age)\s*\(\s*([^)]+)\s*\)\s*\.",
    re.IGNORECASE | re.MULTILINE,
)


def _atom(value: str) -> str:
    return re.sub(r"\s+", "", value.strip().lower())


def parse_family_kb(path: Path = PL_PATH) -> dict:
    """Load fact predicates from family_kb.pl (keeps fallback in sync with edits)."""
    text = path.read_text(encoding="utf-8")
    parent: set[tuple[str, str]] = set()
    male: set[str] = set()
    female: set[str] = set()
    married: set[tuple[str, str]] = set()
    age: dict[str, int] = {}

    for match in _FACT_RE.finditer(text):
        functor = match.group(1).lower()
        args = [_atom(a) for a in match.group(2).split(",")]

        if functor == "parent" and len(args) == 2:
            parent.add((args[0], args[1]))
        elif functor == "male" and len(args) == 1:
            male.add(args[0])
        elif functor == "female" and len(args) == 1:
            female.add(args[0])
        elif functor == "married" and len(args) == 2:
            married.add((args[0], args[1]))
        elif functor == "age" and len(args) == 2:
            age[args[0]] = int(args[1])

    return {
        "parent": parent,
        "male": male,
        "female": female,
        "married": married,
        "age": age,
    }


def list_family_members(path: Path = PL_PATH) -> list[str]:
    facts = parse_family_kb(path)
    members: set[str] = set()
    for p, c in facts["parent"]:
        members.add(p)
        members.add(c)
    members |= facts["male"]
    members |= facts["female"]
    for h, w in facts["married"]:
        members.add(h)
        members.add(w)
    members |= facts["age"].keys()
    return sorted(members)


def _prepend_swipl_to_path() -> None:
    for folder in SWIPL_SEARCH_PATHS:
        dll = os.path.join(folder, "libswipl.dll")
        if os.path.isfile(dll):
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
            os.environ.setdefault("SWI_HOME_DIR", os.path.dirname(folder))
            break


class PrologEngine(Protocol):
    def query_relation(self, relation: str, person: str) -> list[str]: ...


class PySwipEngine:
    def __init__(self) -> None:
        _prepend_swipl_to_path()
        from pyswip import Prolog

        self._prolog = Prolog()
        self._prolog.consult(str(PL_PATH))

    def query_relation(self, relation: str, person: str) -> list[str]:
        person = re.sub(r"\s+", "", person.strip().lower())
        relation = relation.strip().lower().replace("-", " ").replace(" ", "_")

        if relation == "age":
            goal = f"age({person}, X)"
        else:
            goal = f"{relation}(X, {person})"

        try:
            rows = list(self._prolog.query(goal))
        except Exception:
            return []

        return [str(row["X"]) for row in rows]


class PythonFallbackEngine:
    """Evaluates the same relations as family_kb.pl using parsed facts."""

    def __init__(self, path: Path = PL_PATH) -> None:
        facts = parse_family_kb(path)
        self.parent = facts["parent"]
        self.male = facts["male"]
        self.female = facts["female"]
        self.married = facts["married"]
        self.age = facts["age"]
        self._all_people = list_family_members(path)

    def _parents_of(self, child: str) -> set[str]:
        return {p for p, c in self.parent if c == child}

    def _children_of(self, parent: str) -> set[str]:
        return {c for p, c in self.parent if p == parent}

    def father(self, y: str) -> set[str]:
        return {p for p in self._parents_of(y) if p in self.male}

    def mother(self, y: str) -> set[str]:
        return {p for p in self._parents_of(y) if p in self.female}

    def sibling(self, y: str) -> set[str]:
        sibs: set[str] = set()
        for p in self._parents_of(y):
            sibs |= self._children_of(p)
        sibs.discard(y)
        return sibs

    def grandfather(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            out |= self.father(p)
        return out

    def grandmother(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            out |= self.mother(p)
        return out

    def grandparent(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            out |= self._parents_of(p)
        return out

    def brother(self, y: str) -> set[str]:
        return {x for x in self.sibling(y) if x in self.male}

    def sister(self, y: str) -> set[str]:
        return {x for x in self.sibling(y) if x in self.female}

    def son(self, y: str) -> set[str]:
        return {c for c in self._children_of(y) if c in self.male}

    def daughter(self, y: str) -> set[str]:
        return {c for c in self._children_of(y) if c in self.female}

    def uncle(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            out |= self.brother(p)
        return out

    def aunt(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            out |= self.sister(p)
        return out

    def cousin(self, y: str) -> set[str]:
        out: set[str] = set()
        for p in self._parents_of(y):
            for s in self.sibling(p):
                out |= self._children_of(s)
        return out

    def nephew(self, y: str) -> set[str]:
        out: set[str] = set()
        for s in self.sibling(y):
            out |= self.son(s)
        return out

    def niece(self, y: str) -> set[str]:
        out: set[str] = set()
        for s in self.sibling(y):
            out |= self.daughter(s)
        return out

    def ancestor(self, y: str) -> set[str]:
        found: set[str] = set()
        frontier = list(self._parents_of(y))
        while frontier:
            cur = frontier.pop()
            if cur in found:
                continue
            found.add(cur)
            frontier.extend(self._parents_of(cur))
        return found

    def descendant(self, y: str) -> set[str]:
        return {p for p in self._all_people if y in self.ancestor(p)}

    def husband(self, y: str) -> set[str]:
        return {h for h, w in self.married if w == y}

    def wife(self, y: str) -> set[str]:
        return {w for h, w in self.married if h == y}

    def spouse(self, y: str) -> set[str]:
        return self.husband(y) | self.wife(y)

    def father_in_law(self, y: str) -> set[str]:
        out: set[str] = set()
        for sp in self.spouse(y):
            out |= self.father(sp)
        return out

    def mother_in_law(self, y: str) -> set[str]:
        out: set[str] = set()
        for sp in self.spouse(y):
            out |= self.mother(sp)
        return out

    def brother_in_law(self, y: str) -> set[str]:
        out: set[str] = set()
        for sp in self.spouse(y):
            out |= self.brother(sp)
        return out

    def sister_in_law(self, y: str) -> set[str]:
        out: set[str] = set()
        for sp in self.spouse(y):
            out |= self.sister(sp)
        return out

    def elder_sibling(self, y: str) -> set[str]:
        return {s for s in self.sibling(y) if self.age.get(s, 0) > self.age.get(y, 0)}

    def younger_sibling(self, y: str) -> set[str]:
        return {s for s in self.sibling(y) if self.age.get(s, 0) < self.age.get(y, 0)}

    def paternal_grandfather(self, y: str) -> set[str]:
        out: set[str] = set()
        for f in self.father(y):
            out |= self.father(f)
        return out

    def query_relation(self, relation: str, person: str) -> list[str]:
        person = re.sub(r"\s+", "", person.strip().lower())
        relation = relation.strip().lower().replace("-", " ").replace(" ", "_")

        if relation == "age":
            if person in self.age:
                return [str(self.age[person])]
            return []

        method = getattr(self, relation, None)
        if method is None:
            return []
        return sorted(method(person))


def create_engine() -> tuple[PrologEngine, str]:
    _prepend_swipl_to_path()
    try:
        return PySwipEngine(), "SWI-Prolog (pyswip)"
    except Exception:
        return PythonFallbackEngine(), "Python fallback (reads family_kb.pl)"
