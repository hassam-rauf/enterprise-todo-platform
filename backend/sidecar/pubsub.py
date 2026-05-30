# Stub - Dapr pubsub disabled for Vercel deployment
def build_task_event(action: str, task) -> dict:
    return {"action": action, "task_id": str(task.id)}

def _publish_sync(topic: str, data: dict) -> None:
    pass  # No-op without Dapr
