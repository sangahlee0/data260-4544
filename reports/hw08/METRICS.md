| Failure scenario | Before fix | After fix |
|---|---|---|
| Duplicate delivery | The same message could create more than one draft. | The Writer detected the repeated `correlation_id` and ignored the duplicate. |
| Consumer killed mid-work | Automatic commits could lose the message after failure. | Manual commits allowed Kafka to redeliver the uncommitted message after restart. |
| Poison message | A bad message could repeatedly fail and block later messages. | The message was retried three times, moved to `s4544_dead_letter`, and later messages continued. |
| Two partitions/two consumers | Related messages could be processed by different consumers and partitions. | Using the entity as the Kafka key kept related messages in one partition and preserved their order. |

## Ordering Results

| Run | Message key | Partitions observed | Processing order | Result |
|---|---|---|---|---|
| Unkeyed | None | Partitions 0 and 1 | Messages were distributed between two Writer instances; the combined log was not globally ordered. | Ordering was not guaranteed across partitions |
| Keyed | `related-entity-4544` | Partition 0 | Sequence 1 through 20 | All related messages stayed in one partition and preserved order |

Test configuration:

- Topic: `s4544_tasks`
- Partitions: 2
- Consumers: 2 Writer instances
- Consumer group: `s4544-writer-group`
- Messages per run: 20

## HW2 In-Process Graph vs. HW8 Kafka Pipeline

In HW2, `build_workflow()` created an in-process graph, and `graph.stream(initial_state)` directly passed state from one step to the next.
The agents did not need Kafka topics, correlation IDs, consumer groups, or offset management. In HW8, the agents became separate processes and Kafka topics carried the messages between them.

### Two benefits gained from Kafka
1. **Independent scaling:** Planner, Writer, and Reviewer can run as separate
   processes and can be scaled independently.
2. **Failure isolation:** One agent can restart without requiring direct function
   calls from the other agents.

### Two new responsibilities
1. **Message ordering and duplicate delivery:** The application must choose keys
   and partitions carefully and handle repeated messages with idempotency.
2. **Offset and failure management:** The application must manage commits,
   retries, redelivery, and dead-letter messages.
