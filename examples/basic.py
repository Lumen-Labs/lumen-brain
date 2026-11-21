from lumen_brain import LumenBrain

with LumenBrain(pat="your-pat", brain_id="my-brain", region="europe-central2") as brain:
    accepted = brain.save("Ada joined the design team in Berlin in 2024.")
    brain.wait_for_task(accepted.task_id)

    context = brain.query(
        "Who is on the design team in Berlin?",
        as_of="2025-06-01T00:00:00Z",
    )
    print(context.text_context)

    hits = brain.search("design team")
    for hit in hits.hits:
        print(hit.score, hit.snippet)
