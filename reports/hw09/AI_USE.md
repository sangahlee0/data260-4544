# AI Use — HW9

### (1) What you used an AI assistant for and what you did yourself;
I used an AI assistant to help organize the connection between HW8 and HW9, and to draft the queries/questions so that they are corrrect.
I ran the commands myself, started Redis and Ollama, reviewed the terminal output, ran the threshold sweep and Part 4 tests, wrote the written explanations, and captured the screenshots and run logs.

### (2) One AI-produced output that was wrong/unsuitable, or one thing you independently verified;
After asking for an example of how the results would look like, the first threshold-sweep implementation seeded all 40 cached queries at the same time, which produced an invalid false-hit example. I also independently verified that the first Part 3.3 report was wrong because its cached and incoming queries were identical.

### (3) How you detected the problem or verified the result;
I reviewed the generated false-hit report and compared it with `cache_cases.yaml`. The report labeled both queries as vulnerability ID 2 even though the selected case was supposed to compare ID 1 with ID 2. I corrected the sweep to isolate one cached query per case, reran it, and replaced the threshold results with the corrected CSV values.
I also verified the 40 cache cases by category, the Part 4 validation counts, the two-attempt repair sequence, and the lesson reuse count in the terminal output and report files.

### (4) What you changed and why it works now;
The threshold sweep now clears the HW9 sweep namespace and seeds only the cached query belonging to the current case before testing its incoming query. This prevents cross-case contamination. The false-hit demonstration now uses a controlled ID 1 versus ID 2 comparison and records the measured similarity score. The Part 4 combined runner separately demonstrates evaluator repair, lesson reuse, validation, and the four final variants.

The AI assistant helped with debugging, but I reviewed the outputs, selected the explanations, and verified the final evidence myself.
