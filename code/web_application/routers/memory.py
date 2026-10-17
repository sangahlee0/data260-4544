import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from mongo.schemas import ChatRequest
from mongo.ollama_service import embed_text
from mongo.utils import (
    save_message,
    get_recent_messages,
    get_session_summary,
    get_latest_session_summary,
    get_user_summary,
    get_relevant_episodes,
    save_episode,
    count_user_messages,
    save_summary,
    get_session_summary_texts,
    get_user_messages,
    get_recent_episodes,
    get_recent_summaries,
    get_daily_message_counts,
    serialize_message,
    serialize_summary,
    serialize_episode,
)

# model_client.py is in the src folder from HW1 that we pull from the previous homework
SRC_DIR = Path(__file__).resolve().parents[3] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from model_client import complete


router = APIRouter(tags=["Memory"])

SHORT_TERM_N = int(os.environ.get("SHORT_TERM_N", "12"))    # defaut is 12; for short-term memory comparison
SUMMARIZE_EVERY_USER_MSGS = 4
EPISODE_TOP_K = 3
EVICT = os.environ.get("EVICT") == "1"

# Part 3 raw results. Same folder pattern as reports/hw01/raw/.
RAW_LOG_PATH = Path(__file__).resolve().parents[3] / "reports" / "hw06" / "raw" / "memory_logs.json"
RUN_LOG_PATH = Path(__file__).resolve().parents[3] / "reports" / "hw06" / "RUN_LOG.txt"
PROBES_PATH = Path(__file__).resolve().parents[3] / "reports" / "hw06" / "memory_probes.yaml"
AGENT_PATH = Path(__file__).resolve().parents[3] / "AGENT.md"
MEMORY_PATH = Path(__file__).resolve().parents[3] / "MEMORY.md"


def tokens_used_by_each_part(prompt_tokens, pieces):
    # Ollama gives one prompt total. Split it across the four parts
    # by how many characters each part has.
    lengths = {}
    total_characters = 0
    for name in pieces:
        text = pieces[name]
        if text is None:
            length = 0
        else:
            length = len(text)
        lengths[name] = length
        total_characters = total_characters + length

    part_tokens = {}
    for name in lengths:
        if total_characters == 0:
            part_tokens[name] = 0
        else:
            part_tokens[name] = round(prompt_tokens * lengths[name] / total_characters)
    return part_tokens


def save_turn_log(row):
    RAW_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if RAW_LOG_PATH.exists():
        rows = json.loads(RAW_LOG_PATH.read_text())
    else:
        rows = []
    rows.append(row)
    RAW_LOG_PATH.write_text(json.dumps(rows, indent=2))

    with RUN_LOG_PATH.open("a") as log_file:
        log_file.write(
            "SHORT_TERM_N = " + str(row["short_term_n"])
            + " session_id = " + str(row["session_id"])
            + " prompt_tokens = " + str(row["prompt_tokens"])
            + " completion_tokens = " + str(row["completion_tokens"])
            + " system_primer_tokens = " + str(row["system_primer_tokens"])
            + " long_term_summary_tokens = " + str(row["long_term_summary_tokens"])
            + " short_term_window_tokens = " + str(row["short_term_window_tokens"])
            + " episodic_facts_tokens = " + str(row["episodic_facts_tokens"])
            + " latency_ms = " + str(row["latency_ms"])
            + " eviction = " + str(row["eviction"])
            + "\n"
        )


# Ask the model for up to 3 short facts from one user message.
# Each line comes back as the fact, then an importance from 0 to 1.
def extract_facts(message):
    result = complete([
        {
            "role": "system",
            "content": "Extract up to 3 short facts. One per line: the fact, an importance from 0 to 1. If there is no fact, reply NONE.",
        },
        {"role": "user", "content": message},
    ])

    facts = []
    lines = result["content"].splitlines()

    for line in lines:
        words = line.strip().split()
        if len(words) < 2:
            continue

        try:
            importance = float(words[-1])
        except ValueError:
            continue

        if importance < 0 or importance > 1:
            continue

        fact = line.strip()
        fact = fact[:fact.rfind(words[-1])].strip(" -|")

        if fact == "" or fact.upper() == "NONE":
            continue

        facts.append((fact, importance))

        if len(facts) == 3:
            break

    return facts


def load_markdown(path):
    if path.exists():
        return path.read_text()
    return ""


def memory_fact_lines(text):
    count = 0
    for line in text.splitlines():
        if line.strip() == "":
            continue
        count = count + 1
    return count


def last_consolidated_time():
    # The computer stores when MEMORY.md was last saved.
    if not MEMORY_PATH.exists():
        return None
    return datetime.fromtimestamp(MEMORY_PATH.stat().st_mtime)


def write_memory(lines):
    text = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            continue
        text = text + stripped + "\n"
    MEMORY_PATH.write_text(text)


def compact_memory():
    before_text = load_markdown(MEMORY_PATH)
    before_count = memory_fact_lines(before_text)

    # One copy of each exact line.
    lines = []
    for line in before_text.splitlines():
        line = line.strip()
        if line == "" or line in lines:
            continue
        lines.append(line)

    # If two lines match except for one word, keep the first and record the other.
    kept = []
    notes = []
    for line in lines:
        earlier_line = ""
        for earlier in kept:
            words = line.split()
            earlier_words = earlier.split()
            if len(words) == 0 or len(words) != len(earlier_words):
                continue
            changes = 0
            for i in range(len(words)):
                if words[i] != earlier_words[i]:
                    changes = changes + 1
            if changes == 1:
                earlier_line = earlier
                break
        if earlier_line == "":
            kept.append(line)
        else:
            notes.append('Kept "' + earlier_line + '" The other fact was "' + line + '"')

    write_memory(kept + notes)
    after_count = memory_fact_lines(load_markdown(MEMORY_PATH))
    return "Before: " + str(before_count) + "\nAfter: " + str(after_count)


def dream_memory(user_id, session_id):
    recent = get_recent_messages(user_id, session_id, limit=SHORT_TERM_N)
    lines = ""
    for doc in recent:
        lines = lines + doc.get("role", "") + ": " + doc.get("content", "") + "\n"

    result = complete([
        {
            "role": "system",
            "content": "List useful long-term facts from this conversation. One fact per line.",
        },
        {"role": "user", "content": lines},
    ])

    existing = load_markdown(MEMORY_PATH)
    added = 0
    for line in result["content"].splitlines():
        fact = line.strip().lstrip("-").strip()
        if fact == "" or fact.upper() == "NONE" or fact.endswith(":"):
            continue
        while len(fact) > 0 and fact[0].isdigit():
            fact = fact[1:]
        fact = fact.lstrip(".").strip()
        if fact == "":
            continue
        if fact in existing:
            continue
        existing = existing.rstrip() + "\n" + fact + "\n"
        added = added + 1
    MEMORY_PATH.write_text(existing)
    return "Added " + str(added) + " facts to MEMORY.md."


def handle_command(user_id, session_id, message):
    command = message.strip()
    if command == "/help":
        return (
            "/memory shows AGENT.md and MEMORY.md.\n"
            "/compact consolidates MEMORY.md and reports the line count before and after.\n"
            "/dream adds useful facts from the recent conversation to MEMORY.md.\n"
            "/help explains these commands."
        )
    if command == "/memory":
        return "AGENT.md:\n" + load_markdown(AGENT_PATH) + "\nMEMORY.md:\n" + load_markdown(MEMORY_PATH)
    if command == "/compact":
        return compact_memory()
    if command == "/dream":
        return dream_memory(user_id, session_id)
    return None


def consolidation_required(text):
    # More than 40 fact lines, or the last consolidation was over 24 hours ago.
    if memory_fact_lines(text) > 40:
        return True
    when = last_consolidated_time()
    if when is None:
        return True
    age_seconds = (datetime.now() - when).total_seconds()
    if age_seconds > 24 * 60 * 60:
        return True
    return False


# Put the summary, recent messages, and facts into the list the model reads.
def build_prompt(recent_messages, session_summary, user_summary, episodes):
    system_text = "You help the user track open-source package vulnerabilities.\n"

    agent_text = load_markdown(AGENT_PATH)
    memory_text = load_markdown(MEMORY_PATH)
    if agent_text != "":
        system_text = system_text + "\nAGENT.md:\n" + agent_text + "\n"
    if memory_text != "":
        system_text = system_text + "\nMEMORY.md:\n" + memory_text + "\n"

    if user_summary is not None and user_summary.get("text"):
        system_text = system_text + "\nLifetime summary:\n" + user_summary["text"] + "\n"

    if session_summary is not None and session_summary.get("text"):
        system_text = system_text + "\nSession summary:\n" + session_summary["text"] + "\n"

    if len(episodes) > 0:
        system_text = system_text + "\nRelated facts:\n"
        for episode in episodes:
            system_text = system_text + episode.get("fact", "") + "\n"

    prompt = [{"role": "system", "content": system_text}]

    for doc in recent_messages:
        role = doc.get("role")
        if role == "user" or role == "assistant":
            prompt.append({"role": role, "content": doc.get("content", "")})

    return prompt


# After SUMMARIZE_EVERY_USER_MSGS user messages, save a session summary,
# then condense session summaries into a lifetime summary.
def maybe_summarize(user_id, session_id):
    user_turns = count_user_messages(user_id, session_id)

    if user_turns % SUMMARIZE_EVERY_USER_MSGS != 0:
        return

    recent = get_recent_messages(user_id, session_id, limit=SHORT_TERM_N)
    lines = ""
    for doc in recent:
        lines = lines + doc.get("role") + ": " + doc.get("content") + "\n"

    result = complete([
        {"role": "system", "content": "Summarize this conversation into concise bullets."},
        {"role": "user", "content": lines},
    ])
    save_summary(user_id, session_id, "session", result["content"].strip())

    older_texts = get_session_summary_texts(user_id)
    combined = ""
    for text in older_texts:
        combined = combined + text + "\n"

    lifetime = complete([
        {"role": "system", "content": "Condense these session summaries into concise bullets."},
        {"role": "user", "content": combined},
    ])
    # session_id is null for lifetime summary
    save_summary(user_id, None, "user", lifetime["content"].strip())


@router.post("/api/chat")
def chat(payload: ChatRequest):
    if payload.session_id:
        session_id = payload.session_id
    else:
        session_id = "default"

    command_reply = handle_command(payload.user_id, session_id, payload.message)
    if command_reply is not None:
        return {
            "reply": command_reply,
            "session_id": session_id,
        }

    started = time.perf_counter()

    try:
        # save user message
        save_message(payload.user_id, session_id, "user", payload.message)

        # save up to 3 facts from that message
        facts = extract_facts(payload.message)
        for fact, importance in facts:
            embedding = embed_text(fact)
            save_episode(payload.user_id, session_id, fact, importance, embedding)

        # load memory that will go into prompt
        recent_messages = get_recent_messages(payload.user_id, session_id, limit=SHORT_TERM_N)
        session_summary = get_session_summary(payload.user_id, session_id)
        user_summary = get_user_summary(payload.user_id)
        # --evict makes it so that we can leave the session summary out and keep the lifetime summary.
        if EVICT and user_summary is not None and user_summary.get("text"):
            session_summary = None
        message_embedding = embed_text(payload.message)
        episodes = get_relevant_episodes(payload.user_id, message_embedding, limit=EPISODE_TOP_K)

        # ask model and save reply  
        prompt = build_prompt(recent_messages, session_summary, user_summary, episodes)
        result = complete(prompt)
        reply = result["content"]
        save_message(payload.user_id, session_id, "assistant", reply)

        # write a summary when it is time
        maybe_summarize(payload.user_id, session_id)

    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error during chat.")
    except Exception:
        raise HTTPException(status_code=500, detail="Model error during chat.")

    # info on what memory this turn used in the memory_used field  
    summary_parts = []
    if user_summary is not None and user_summary.get("text"):
        summary_parts.append(user_summary["text"])
    if session_summary is not None and session_summary.get("text"):
        summary_parts.append(session_summary["text"])

    if len(summary_parts) == 0:
        long_term_summary = None
    else:
        long_term_summary = "\n".join(summary_parts)

    short_term_messages = []
    for doc in recent_messages:
        short_term_messages.append({
            "role": doc.get("role"),
            "content": doc.get("content"),
        })

    episodic_facts = []
    for doc in episodes:
        episodic_facts.append(doc.get("fact"))

    # For Part 3, record tokens and latency for this turn.
    primer_text = "Your task is to help the user track open-source package vulnerabilities.\nUse the memory below when it helps.\n"
    short_term_text = ""
    for doc in recent_messages:
        short_term_text = short_term_text + doc.get("content", "")
    fact_text = ""
    for fact in episodic_facts:
        if fact:
            fact_text = fact_text + fact

    prompt_tokens = result["input_tokens"]
    part_tokens = tokens_used_by_each_part(prompt_tokens, {
        "system_primer": primer_text,
        "long_term_summary": long_term_summary,
        "short_term_window": short_term_text,
        "episodic_facts": fact_text,
    })

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    save_turn_log({
        "session_id": session_id,
        "user_id": payload.user_id,
        "short_term_n": SHORT_TERM_N,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": result["output_tokens"],
        "system_primer_tokens": part_tokens["system_primer"],
        "long_term_summary_tokens": part_tokens["long_term_summary"],
        "short_term_window_tokens": part_tokens["short_term_window"],
        "episodic_facts_tokens": part_tokens["episodic_facts"],
        "latency_ms": latency_ms,
        "eviction": EVICT,
    })

    return {
        "reply": reply,
        "session_id": session_id,
        "memory_used": {
            "short_term_count": len(recent_messages),
            "short_term_messages": short_term_messages,
            "long_term_summary": long_term_summary,
            "episodic_facts": episodic_facts,
        },
    }

# For Part 3, load the probe questions from memory_probes.yaml
def load_probe_questions():
    questions = []
    for line in PROBES_PATH.read_text().splitlines():
        text = line.strip()
        if text.startswith("- question:"):
            question = text.split(":", 1)[1].strip().strip('"')
            questions.append(question)
    return questions


def run_probes(user_id, session_id):
    # Same idea as rag_pipeline.py reading questions.yaml.
    questions = load_probe_questions()
    for question in questions:
        print(question)
        result = chat(ChatRequest(
            user_id=user_id,
            session_id=session_id,
            message=question,
        ))
        print(result["reply"])
        print()


@router.get("/api/memory/{user_id}")
def get_memory(user_id: str):
    try:
        messages = get_user_messages(user_id, limit=16)
        episodes = get_recent_episodes(user_id, limit=20)
        session_summary = get_latest_session_summary(user_id)
        user_summary = get_user_summary(user_id)
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while reading memory.")

    message_list = []
    for doc in messages:
        message_list.append(serialize_message(doc))

    episode_list = []
    for doc in episodes:
        episode_list.append(serialize_episode(doc))

    if session_summary is None:
        session_summary_out = None
    else:
        session_summary_out = serialize_summary(session_summary)

    if user_summary is None:
        lifetime_summary_out = None
    else:
        lifetime_summary_out = serialize_summary(user_summary)

    return {
        "messages": message_list,
        "session_summary": session_summary_out,
        "lifetime_summary": lifetime_summary_out,
        "episodes": episode_list,
    }


@router.get("/api/aggregate/{user_id}")
def get_aggregate(user_id: str):
    try:
        daily_counts = get_daily_message_counts(user_id)
        summaries = get_recent_summaries(user_id, limit=5)
    except PyMongoError:
        raise HTTPException(status_code=500, detail="Database error while aggregating memory.")

    summary_list = []
    for doc in summaries:
        summary_list.append(serialize_summary(doc))

    return {
        "daily_message_counts": daily_counts,
        "recent_summaries": summary_list,
    }
