import json
from workflow import build_workflow


def main():
    # Build the compiled LangGraph
    graph = build_workflow()

    # Initial shared state
    initial_state = {
        "title": "Testing Vulnerability",
        "content": "A package contains a SQL injection vulnerability.",
        "email": "test@example.com",
        "strict": False,
        "task": (
            "Generate exactly 3 topical tags and a summary "
            "for this vulnerability."
        ),
        "planner_proposal": {},
        "reviewer_feedback": {},
        "turn_count": 0,
    }

    results = []

    # Invoke the graph with the initial state and use .stream() method to see the output of each step
    for event in graph.stream(initial_state):
        print(event)
        results.append(event)

    
    # Save for the json report for machine-readable verification
    with open("../reports/hw02/raw/step6_test.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()