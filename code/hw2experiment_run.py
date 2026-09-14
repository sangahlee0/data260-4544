import json
import time
import argparse

from workflow import build_workflow

def initial_state_set(schema_load):
    return {
        "title": schema_load["vulnerability_name"],
        "content": schema_load["issue_description"],
         "email": schema_load["reporter_email"],
        "strict": False,
        "task": (
            f"Generate exactly 3 topical tags and a summary for this vulnerability. "
            f"Package: {schema_load['package_name']}. "
            f"Vulnerability: {schema_load['vulnerability_name']}. "
            f"Severity: {schema_load['severity']}."
        ),
        "planner_proposal": {},
        "reviewer_feedback": {},
        "validation_error": "",
        "turn_count": 0,
        }

def run_experiment(input_file, run_count, output_file):
    # Build the compiled LangGraph
    with open(input_file, "r") as f:
        schema_load = json.load(f)

    results = []

    # Run graph based on the run_count times
    for i in range(run_count):
        print(f"--- RUN {i+1} ---")
        graph = build_workflow()

        initial_state = initial_state_set(schema_load)

        
        planner_attempts = 0
        turn_count = 0
        hit_turn_ceiling = False
        start_time = time.perf_counter() # perf_counter is more precise than time.time() for measuring elapsed time

        for event in graph.stream(initial_state):
            print(event)

            if "planner" in event:
                planner_attempts += 1

            if "supervisor" in event:
                turn_count = event["supervisor"]["turn_count"]
                if turn_count >= 10:
                    hit_turn_ceiling = True

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        retries = planner_attempts - 1

        if hit_turn_ceiling:
            outcome = "abandoned at the ceiling"
        elif retries == 0:
            outcome = "valid first attempt"
        elif retries == 1:
            outcome = "valid after one retry"
        else:
            outcome = "valid after two or more retries"

        results.append({
            "run": i + 1,
            "outcome": outcome,
            "latency_ms": latency_ms,
        })

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)



### Experiment for Part 4 Question 4; compare turn ceilings of 2 and 10 over 20 runs each
def run_turn_ceiling_experiment(turn_ceiling: int, num_runs: int = 20):
    results = []
    with open("../reports/hw02/cases/schema_input.json", "r") as f:
        schema_load = json.load(f)

    for i in range(num_runs):
        print(f"--- RUN {i+1} with turn ceiling {turn_ceiling} ---")
        graph = build_workflow()
        initial_state = initial_state_set(schema_load)
        initial_state["turn_ceiling"] = turn_ceiling

        hit_turn_ceiling = False
        start_time = time.perf_counter()

        # Run to check it reaches turn ceiling
        for event in graph.stream(initial_state):
            print(event)

            # Check if the supervisor node has updated the turn count and compare it to the turn ceiling
            if "supervisor" in event:
                turn_count = event["supervisor"]["turn_count"]

                # Check if the turn count has reached the specified turn ceiling
                if turn_count >= turn_ceiling:
                    hit_turn_ceiling = True

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        results.append({
            "run": i + 1,
            "successful completion": not hit_turn_ceiling,
            "latency_ms": latency_ms,
        })

    # Calculate completion rate and mean latency for the runs so far
    successful_runs = sum(1 for r in results if r["successful completion"])
    completion_rate = successful_runs / len(results)
    mean_latency_ms = sum(r["latency_ms"] for r in results) / len(results)

    # Print the results for this turn ceiling for RUN_LOG.txt
    print(f"Turn ceiling {turn_ceiling}: "
          f"completion rate = {completion_rate * 100:.1f}%, "
          f"mean latency = {mean_latency_ms:.2f} ms"
          )
    
    return{
        "turn_ceiling": turn_ceiling,
        "completion_rate": completion_rate,
        "mean_latency_ms": mean_latency_ms,
        "runs": results,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--experiment",
        type=int,
        choices=[3, 4, 5],
        required=True
    )

    args = parser.parse_args()

    if args.experiment == 3:
        run_experiment(
            "../reports/hw02/cases/schema_input.json",
            30,
            "../reports/hw02/raw/schema_experiment_results.json"
        )

    elif args.experiment == 4:
        ceiling_2_results = run_turn_ceiling_experiment(2, 20)
        ceiling_10_results = run_turn_ceiling_experiment(10, 20)

        with open("../reports/hw02/raw/ceiling_comparison_results.json", "w") as f:
            json.dump({
                "ceiling_2": ceiling_2_results,
                "ceiling_10": ceiling_10_results,
            }, f, indent=2)

    elif args.experiment == 5:
        run_experiment(
            "../reports/hw02/cases/adversarial_input.json",
            5,
            "../reports/hw02/raw/adversarial_results.json"
        )