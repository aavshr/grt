from fastapi import FastAPI, Request

from code_reviews import ReviewRequestStore

# FastAPI app
app = FastAPI()

# review request store
rev_req_store = ReviewRequestStore()

@app.post("/webhook_events")
async def webhook_handler(request: Request):
    payload = await request.json() 

    event_type = request.headers.get("X-Github-Event") 

    if event_type == "pull_request": 
        action = payload.get("action")
        if action == "review_requested":
            rev_req_store.store(payload)
        elif action == "review_request_removed":
            rev_req_store.delete(payload)
        return "ok"

    if event_type == "pull_request_review" and payload.get("action") == "submitted":
        rev_req_store.mark_complete(payload)
        return "ok"

    #ignore other events
    return "ok"