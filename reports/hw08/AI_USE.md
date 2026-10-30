# AI Use — HW8
### (1) What you used an AI assistant for and what you did yourself;
I used an AI assistant to help me understand the demo code to my  domain, and used it to assist me in writing the good code formats. 
I ran the commands myself, created the Docker containers and Kafka topics, started the separate processes, reviewed the terminal output, and captured the screenshots and run logs. I also checked that the actual topic names, correlation IDs, entity IDs, partitions, retries, and offsets appeared in the results to confirm that the code is running propertly.

### (2) One AI-produced output that was wrong/unsuitable, or one thing you independently verified;
The demo created `AIOKafkaProducer` and `AIOKafkaConsumer` objects inside the `KafkaRPC` constructor. That caused FastAPI to fail with an `aiokafka` error saying that the object must be created inside an async function. This demo code was not compatible with the installed environment, so I edited and created a folder to make it available.
I also independently checked that my assignment used the exact `correlation_id`, `reply_to`, `operation`, and `data` request structure.

### (3) How you detected the problem or verified the result;
I detected the FastAPI problem by reading the Docker traceback and seeing that the failure occurred while `KafkaRPC()` was being created during module import. After changing the startup code, I rebuilt the FastAPI image and confirmed that the service stayed running and printed the Kafka startup messages. The work was verified using the terminal output.

### (4) What you changed and why it works now;
I changed `KafkaRPC` so its Kafka clients are created inside the asynchronous `start()` method. I added the required `s4544` topic names, correlation ID handling, validation, idempotency, manual offset commits, bounded retries, dead-letter routing, and partition keys, and this allowed the code to work properly.