from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse

import utils
from reviews import rev_req_store
from insights import Chart

# FastAPI app
app = FastAPI()

# chart
chart = Chart()

## cache generated charts
CACHE_MAX_AGE = 300


@app.post("/webhook_events")
async def webhook_handler(request: Request):
    # verify webhook signature
    raw = await request.body()
    signature = request.headers.get("X-Hub-Signature")
    if signature != utils.calc_signature(raw):
        raise HTTPException(status_code=401, detail="Unauthorized")

    # handle events
    payload = await request.json()
    event_type = request.headers.get("X-Github-Event")

    # reviews requested or removed
    if event_type == "pull_request":
        action = payload.get("action")
        if action == "review_requested":
            rev_req_store.store(payload)
        elif action == "review_request_removed":
            rev_req_store.delete(payload)
        return "ok"

    # review submitted
    if event_type == "pull_request_review" and payload.get("action") == "submitted":
        rev_req_store.mark_complete(payload)
        return "ok"

    # ignore other events
    return "ok"


# get average turnaround insights
# last: for last 'x', 'x' is only one of 'week' or 'month' currently
# period: 'period to calculate average of, currently 'day' or 'week'
# plot: whether to generate a plot or not, returns json if plot is False
@app.get("/turnarounds/")
def get_turnarounds(last: str = "week", period: str = "day", plot: bool = True):
    try:
        if not plot:
            return chart.get_json(last, period)

        html_chart = chart.get_chart(last, period)
        return HTMLResponse(
            content=html_chart, headers={"Cache-Control": f"max-age={CACHE_MAX_AGE}"}
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad duration or period")


@app.get("/")
def index():
    return "ok"
