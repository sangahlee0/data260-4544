from email.policy import strict
import argparse, json, os, re, sys, time
from dataclasses import dataclass
from typing import List, Dict, Any, Iterable, Tuple

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from collections import Counter

from pathlib import Path


# To filter out noise
STOP = {
    "the", "and", "for", "that", "with", "this", "from", "into", "than", "your", "you",
    "are", "was", "were", "have", "has", "had", "use", "used", "using", "about", "how",
    "can", "will", "more", "less", "very", "over", "under", "their", "there", "then",
    "our", "out", "on", "in", "of", "to", "by", "a", "an", "is", "it", "as",
}

# -------------------------
# Text cleanup + extraction
# -------------------------

def strip_code_and_md(s: str) -> str:
    """
    TODO: Remove markdown/code artifacts from model output.
    Suggested:
      - remove fenced code blocks
      - remove inline backticks
      - normalize whitespace
    """
    # Placeholder implementation:
    s = re.sub(r"```[a-zA-Z]*\s*([\s\S]*?)\s*```", r"\1", s)
    s = s.replace("`", "")
    return " ".join(str(s).split())


def extract_json_block(text: str) -> str:
    """
    TODO: Extract the first JSON object from a text response.
    If none is present, wrap text like: {"message": "<cleaned text>"}.
    """
    text = str(text).strip()
    # Placeholder: assume it's already JSON
    # match is a regex to find the first JSON object in the text
    start = text.find("{")
    end = text.rfind("}")

    # If we found a JSON object, return it
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    else:
        # If no JSON found, wrap the text in a JSON object  
        cleaned_text = strip_code_and_md(text)
        return json.dumps({"message": cleaned_text})


def tokens(txt: str) -> List[str]:
    """
    TODO: Tokenize into lowercase words (optionally keep hyphens), filter junk, etc.
    """
    return re.findall(r"[a-z][a-z\-]+", str(txt).lower())


def ngrams(words: List[str], n: int) -> Iterable[Tuple[str, ...]]:
    """
    TODO: Yield word n-grams from a token list.
    """
    for i in range(max(0, len(words) - n + 1)):
        yield tuple(words[i:i + n])


def phrase_candidates(title: str, content: str, maxn: int = 12) -> List[str]:
    """
    TODO: Build tag candidates derived ONLY from title+content.
    Suggested approach:
      - tokenize + remove STOP words
      - gather bigrams/trigrams
      - rank by frequency
      - fall back to unigrams
      - return up to maxn
    """
    # Placeholder: students should implement
    candidates = []
    # trigram, bigram, unigram
    for n in range(3, 0, -1):
        ngram_list = list(ngrams(tokens(title + " " + content), n))
        freq = Counter()
        for ng in ngram_list:
            if any(word in STOP for word in ng):
                continue
            phrase = " ".join(ng)
            freq[phrase] += 1
        
        # Sort phrases by frequency and add to candidates
        sort_freq = [k for k, v in freq.most_common()]

        # Add unique phrases to candidates
        for phrase in sort_freq:
            if phrase not in candidates:
                candidates.append(phrase)
            if len(candidates) >= maxn:
                break

        if len(candidates) >= maxn:
            break
    return candidates[:maxn]

# -------------------------
# Output schema coercion
# -------------------------

def coerce_reply(raw_obj: Any, title: str, content: str, strict: bool) -> Dict[str, Any]:
    """
    TODO: Coerce arbitrary model output into the required schema:
      {
        "thought": str,
        "message": str (non-empty, <= 60 words),
        "data": {
          "tags": [str, str, str],        # exactly 3 topical tags
          "summary": str,                # <= 25 words, ends with '.'
          "issues": [str, ...]
        }
      }

    strict=True suggestion:
      - enforce at least two multi-word tags
    """
    # Placeholder minimal schema
    thought = str(raw_obj.get("thought", ""))
    message = str(raw_obj.get("message", "OK — proposal reviewed."))
    
    message_words = message.split()
    if len(message_words) > 60:
        message = " ".join(message_words[:60])

    # Data block
    data = raw_obj.get("data", raw_obj)
    # default to empty dict
    if not isinstance(data, dict):
        data = {}
    
    # Tags: ensure exactly 3 tags
    tags = data.get("tags", ["tag one", "tag two", "tag three"])
    if len(tags) < 3 or not isinstance(tags, list):
        tags = ["tag one", "tag two", "tag three"]

    # Ensure tags are strings
    tags = [str(t) for t in tags]

    # Handle strict mode: enforce at least two multi-word tags
    if strict:
        multi_word_tags = sum(1 for t in tags if len(t.split()) > 1)
        if multi_word_tags < 2:
            added_multi_word = False
            # Replace some tags with multi-word candidates
            candidates = phrase_candidates(title, content, maxn=12)

            # Loop to find valid multi-word candidates
            for candidate in candidates:
                if len(candidate.split()) > 1 and candidate not in tags:
                    tags.append(candidate)
                    added_multi_word = True
                    if len(tags) >= 3:
                        break

            # Safety: if still not enough multi-word tags, add a placeholder
            if not added_multi_word and len(tags) < 3:
                tags.append("multi word tag")
            # Ensure we have exactly 3 tags
            tags = tags[:3]


    # Summary: ensure <= 25 words
    summary = data.get("summary", "Short summary.")
    summary_words = summary.split()
    if len(summary_words) > 25:
        summary = " ".join(summary_words[:25])

    if not summary.endswith("."):
        summary += "."

    return {
        "thought": thought,
        "message": message,
        "data": {"tags": tags, "summary": summary, "issues": []},
    }

def parse_and_coerce(text: str, title: str, content: str, strict: bool) -> Dict[str, Any]:
    """
    TODO:
      - extract_json_block()
      - json.loads()
      - coerce_reply()
      - handle JSON parse failures gracefully
    """
    try:
        obj = json.loads(extract_json_block(text))
    except Exception:
        obj = {"message": strip_code_and_md(text)}
    return coerce_reply(obj, title, content, strict)

# -------------------------
# Agent wrapper
# -------------------------

@dataclass
class SimpleAgent:
    name: str
    system: str
    model: Any  # LangChain ChatModel

    def respond(
        self,
        conversation: List[Dict[str, str]],
        task: str,
        title: str,
        content: str,
        strict: bool,
    ) -> Dict[str, Any]:
        """
        TODO:
          - Build a ChatPromptTemplate with system + human instructions
          - Inject task + conversation history
          - Run chain: prompt | model | StrOutputParser()
          - parse_and_coerce() the output into the required schema
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system),
            ("human",
             "Task:\n{task}\n\nConversation so far:\n{history}\n\n"
             "Return ONLY one JSON object (no code fences, no markdown, no explanations). "
             "Keys: thought (string), message (non-empty, <=60 words, no code), "
             "data.tags (array of exactly 3 topical tags), "
             "data.summary (<=25 words, no ellipses), data.issues (array).\n"
             "Do not add extra text outside JSON."
            ),
        ])

        history_text = "\n".join([f'{m["role"]}: {m["content"]}' for m in conversation]) or "(empty)"
        chain = prompt | self.model | StrOutputParser()

        raw = chain.invoke({"task": task, "history": history_text})
        return parse_and_coerce(raw, title, content, strict)

def run_pipeline(planner, reviewer, finalizer, task, title, content, strict):
    """3-agent pipeline run planner -> reviewer -> finalizer and returns the final output and transcript."""
    transcript = []
    
    a = planner.respond(transcript, task, title, content, strict)
    transcript.append({"role": "Planner", "content": a.get("message", "")})
    
    b = reviewer.respond(transcript, task, title, content, strict)
    transcript.append({"role": "Reviewer", "content": b.get("message", "")})
    
    final = finalizer.respond(transcript, task, title, content, strict)
    return final, transcript

# Experiment Runs
def measure_nondeterminism(model_name: str, base_url: str, strict: bool = False) -> List[Dict[str, Any]]:
    """Runs 40 benchmark iterations (20 at temp=0.7, 20 at temp=0.0) and returns results with tags, summary, and latency."""
    # Domain-relevant input
    input_path = Path("reports/hw01/cases/nondeterminism_input.json")
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []

    # Capture time for the logs
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting 40-run non-determinism benchmark...")

    task = (
            f'Given vulnerability name "{data["title"]}" and description "{data["content"]}", produce exactly 3 topical tags '
            f'and a one-sentence summary in your own words.'
    )
    
    # Run 20 times at temperature 0.7
    # Run 20 times at temperature 0.0
    for temp in [0.7, 0.0]:
        print(f"\n[{time.strftime('%H:%M:%S')}] Running 20 iterations at temperature={temp} ---")

        llm = ChatOllama(model=model_name, temperature=temp, base_url=base_url, num_ctx=2048)
        planner = SimpleAgent(name="Planner", system="Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the vulnerability.", model=llm)
        reviewer = SimpleAgent(name="Reviewer", system="Validate: tags topical and not generic; summary ≤ 25 words; no code or markdown. ", model=llm)
        finalizer = SimpleAgent(name="Finalizer", system="Use reviewer feedback to finalize. Output exactly 3 tags in data.tags and the final summary in data.summary.", model=llm)

        for i in range(1, 21):
            # Time to calculate the latency
            start = time.time()

            try:
                final, _ = run_pipeline(planner, reviewer, finalizer, task, data["title"], data["content"], strict)
                output = final.get("data", {})
    
                latency = (time.time() - start) * 1000  # in ms

                tags = (output.get("tags", []) if isinstance(output, dict) else output)
                results.append({
                    "temperature": temp, 
                    "run": i, 
                    "latency_ms": latency, 
                    "tags": sorted(list(set(tags)))
                })
                timestamp = time.strftime('%H:%M:%S')
                print(f"[{timestamp}] {i}/20 Completed ({latency:.1f}ms)")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Error occurred on run {i}: {e}")
                continue
                            
    # Raw results save
    results_path = Path("reports/hw01/raw/nondeterminism_results.json")

    # Create file
    results_path.parent.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Saved raw results to {results_path}")


# -------------------------
# CLI entrypoint
# -------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Your Vulnerability Name Here")
    ap.add_argument("--content", default="Your vulnerability description goes here.")
    ap.add_argument("--email", default="student@example.com")
    ap.add_argument("--model", default=os.environ.get("SMOL_MODEL", "your-ollama-model-tag"))
    ap.add_argument("--base_url", default=os.environ.get("OLLAMA_URL", "http://localhost:11434"))
    ap.add_argument("--turns", type=int, default=1)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--experiment", action="store_true", help="Run the 40-run non-determinism benchmark.")
    args = ap.parse_args()

    # Run the 40-run non-determinism benchmark if --experiment is specified
    if args.experiment:
        measure_nondeterminism(model_name=args.model, base_url=args.base_url, strict=args.strict)
        return
    
    # Initialize Ollama chat model (students can adjust params)
    try:
        llm = ChatOllama(
            model=args.model,
            temperature=0.0,
            base_url=args.base_url,
            num_ctx=2048,
            #format="json",  # asks Ollama to produce JSON when supported
        )
    except Exception:
        print(
            "Failed to initialize ChatOllama. Is Ollama running and the model available?\n"
            "Try: `ollama serve` and `ollama pull <your-model-tag>`.",
            file=sys.stderr,
        )
        raise

    # Define three agents (Planner -> Reviewer -> Finalizer)
    planner = SimpleAgent(
        name="Planner",
        system="Propose exactly 3 distinct, topical tags (prefer multi-word phrases) and a one-line summary for the vulnerability.",
        model=llm,
    )
    reviewer = SimpleAgent(
        name="Reviewer",
        system=(
            "Validate: tags topical and not generic; summary ≤ 25 words; no code or markdown. "
            "If issues, list in data.issues; otherwise echo cleaned tags/summary."
        ),
        model=llm,
    )
    finalizer = SimpleAgent(
        name="Finalizer",
        system=(
            "Use reviewer feedback to finalize. Output exactly 3 tags in data.tags and the final summary in data.summary. "
            "Set data.issues to []."
        ),
        model=llm,
    )

    task = (
        f'Given vulnerability name "{args.title}" and description "{args.content}", produce exactly 3 topical tags '
        f'and a one-sentence summary in your own words. Email is {args.email}.'
    )

    transcript: List[Dict[str, str]] = []

    # Planner
    t0 = time.time()
    a = planner.respond(transcript, task, args.title, args.content, args.strict)
    t1 = time.time()
    transcript.append({"role": "Planner", "content": a.get("message", "")})
    print(f"\n--- Planner ({int((t1 - t0) * 1000)} ms) ---\n{json.dumps(a, indent=2)}")

    # Reviewer
    t0 = time.time()
    b = reviewer.respond(transcript, task, args.title, args.content, args.strict)
    t1 = time.time()
    transcript.append({"role": "Reviewer", "content": b.get("message", "")})
    print(f"\n--- Reviewer ({int((t1 - t0) * 1000)} ms) ---\n{json.dumps(b, indent=2)}")

    # Finalizer
    final = finalizer.respond(transcript, task, args.title, args.content, args.strict)
    print(f"\n Finalized Output \n{json.dumps(final, indent=2)}")

    # Publish package
    package = {
        "title": args.title,
        "email": args.email,
        "content": args.content,
        "agents": {"transcript": transcript, "final": final.get("data", {})},
        "submissionDate": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print(f"\n Publish Package \n{json.dumps(package, indent=2)}")


if __name__ == "__main__":
    main()

    