# Shared Kafka topic names for the HW8 three-agent pipeline that is used for Part 2
PREFIX = "s4544"

INBOX_TOPIC = f"{PREFIX}_inbox"
TASKS_TOPIC = f"{PREFIX}_tasks"
DRAFTS_TOPIC = f"{PREFIX}_drafts"
FINAL_TOPIC = f"{PREFIX}_final"
DEAD_LETTER_TOPIC = f"{PREFIX}_dead_letter"


PIPELINE = {
    "question": INBOX_TOPIC,
    "planner_output": TASKS_TOPIC,
    "writer_output": DRAFTS_TOPIC,
    "reviewer_output": FINAL_TOPIC,
}
