"""Fresh replication worlds; versioned copy preserves the original R21A freeze."""

import hashlib
import json
import random
import re

MOTIFS = ("direct", "passive", "reassignment", "negation", "rumor", "distractors")
COLORS = ("red", "blue", "green", "yellow", "orange", "purple", "black", "white")
SYSTEM = (
    "Use only the supplied records. Work out the intermediate courier identity before "
    "answering the later badge-color question. Give only the courier's name, with no "
    "explanation or badge color. There is one established responsible courier."
)


def owner_from_events(events, parcel):
    owner = None
    for e in events:
        if e["parcel"] == parcel and e["kind"] == "assign":
            owner = e["courier"]
        elif e["parcel"] == parcel and e["kind"] == "deny" and e["courier"] == owner:
            owner = None
    return owner


def render_event(e, passive=False):
    if e["kind"] == "rumor":
        return (
            f"An unconfirmed rumor names {e['courier']} as responsible for {e['parcel']}; "
            "this rumor is not an assignment or an established fact."
        )
    if e["kind"] == "deny":
        return f"{e['courier']} is explicitly not responsible for {e['parcel']}."
    if passive:
        return f"Responsibility for {e['parcel']} is assigned to {e['courier']}."
    return f"{e['courier']} is assigned responsibility for {e['parcel']}."


def worlds(count=384, *, seed=210923073, excluded=()):
    if type(count) is not int or not 1 <= count <= 4096:
        raise ValueError("Invalid case count")
    rng = random.Random(seed)
    used = set(excluded)

    def name():
        while True:
            value = "".join(
                rng.choice("bcdfghjklmnprstvz") + rng.choice("aeiou") for _ in range(4)
            ).title()
            if value not in used:
                used.add(value)
                return value

    cases = []
    for i in range(count):
        people = [name() for _ in range(8)]
        parcel, other = "Parcel-" + name(), "Parcel-" + name()
        owner, wrong = rng.sample(people, 2)
        motif = MOTIFS[i % len(MOTIFS)]
        events = []
        if motif == "reassignment":
            events.append(dict(parcel=parcel, courier=wrong, kind="assign"))
        events.append(dict(parcel=parcel, courier=owner, kind="assign"))
        if motif in ("negation", "rumor"):
            events.append(
                dict(parcel=parcel, courier=wrong, kind="deny" if motif == "negation" else "rumor")
            )
        distractors = [
            dict(parcel=other + str(j), courier=p, kind="assign")
            for j, p in enumerate(people)
            if p != owner
        ]
        if motif == "distractors":
            distractors += [
                dict(parcel=other + "Extra" + str(j), courier=rng.choice(people), kind="assign")
                for j in range(20)
            ]
        # Keep target chronology but vary its position among unrelated records.
        rng.shuffle(distractors)
        at = rng.randrange(len(distractors) + 1)
        events = distractors[:at] + events + distractors[at:]
        evidence = (
            "These records are chronological, oldest first. Each parcel has one responsible "
            "courier. A later explicit assignment replaces an earlier assignment for the same "
            "parcel. Rumors never change assignments.\n"
            + "\n".join(render_event(e, motif == "passive") for e in events)
        )
        colors = rng.sample(COLORS, len(COLORS))
        badges = dict(zip(people, colors, strict=True))
        badge_text = "\n".join(f"{p} wears a {badges[p]} badge." for p in people)
        final_question = (
            f"What color badge does the courier currently responsible for {parcel} wear?"
        )
        case = dict(
            motif=motif,
            parcel=parcel,
            people=people,
            events=events,
            owner=owner,
            wrong_owner=wrong,
            assignments=evidence,
            badges=badges,
            answer=badges[owner],
            evidence=evidence + "\nBadge records:\n" + badge_text,
            final_question=final_question,
        )
        case["id"] = (
            "r21b/" + hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()[:20]
        )
        cases.append(case)
    return cases


def assess(case, text):
    # Whole response only: do not recover a name from contradictory or incomplete prose.
    normalized = re.sub(r"\s+", " ", text.strip()).rstrip(".").casefold()
    for name in case["people"]:
        if normalized == name.casefold():
            return {
                "entity": name,
                "supported": name == owner_from_events(case["events"], case["parcel"]),
            }
    return None


def feedback_view(case):
    return {"parcel": case["parcel"], "evidence": case["assignments"]}


def claim(case, draft):
    # Expose an entity-only intermediate decision as a claim; no answer information added.
    return (
        f"The courier currently responsible for {case['parcel']} is {draft.strip().rstrip('.')} ."
    )


def messages(case):
    return [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": (
                f"Records:\n{case['evidence']}\nLater question: {case['final_question']}\n"
                f"Intermediate step: Who is currently responsible for {case['parcel']}? "
                "Return only that courier's name."
            ),
        },
    ]
