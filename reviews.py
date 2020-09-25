from dateutil.parser import isoparse
from datetime import datetime, timezone
from deta import Deta

""" schema
{
    key: str, // randomly_generated
    reviewer: str, // reviewer
    pull_request: int, // pull request number 
    requested_at : int, // posix timestamp of request
    submitted_at : int, // posix timestamp of review submission
    submitted: bool, // if the review has been submitted
    crt: int // code review turnaround
}
"""

# manages storing, fetching and updating review requests information
class ReviewRequestStore:
    def __init__(self):
        self.db = Deta().Base("code_reviews")
    
    # get review req from pull request number and reviewer
    def __get_review_req(self, pr_num:int, reviewer:str):
        # generator
        review_reqs_gen = next(self.db.fetch({
            "submitted": False,
            "pull_request": pr_num,
            "reviewer": reviewer
        }))

        review_reqs = []
        for r in review_reqs_gen:
            review_reqs.append(r)

        # there should be only one corresponding unsubmitted review request
        if len(review_reqs) == 0:
            raise Exception("No corresponding review request found")

        if len(review_reqs) > 1: 
            raise Exception("Found multiple imcomplete reviews for same pull request and reviewer")

        return review_reqs[0]

    # store review request
    def store(self, payload:dict):
        # POSIX timestamp
        current_time = int(datetime.now(timezone.utc).timestamp())
        item = {
            "reviewer": payload["requested_reviewer"]["login"],
            "pull_request": payload["pull_request"]["number"],
            "requested_at": current_time,
            "submitted": False
        }

        self.db.put(item)

    # mark review request complete
    def mark_complete(self, payload:dict):
        submission_time = int(isoparse(payload["review"]["submitted_at"]).timestamp())

        pr_num = payload["pull_request"]["number"]
        reviewer = payload["review"]["user"]["login"]
        review_req = self.__get_review_req(pr_num, reviewer)

        # updates to the review request 
        updates = {
            "submitted": True,
            "submitted_at": submission_time,
            "crt": submission_time-review_req["requested_at"]
        } 

        self.db.update(updates, review_req["key"]) 
        return

    # delete review request
    def delete(self, payload:dict):
        pr_num = payload["pull_request"]["number"]
        reviewer = payload["requested_reviewer"]["login"]

        review_req = self.__get_review_req(pr_num, reviewer)
        self.db.delete(review_req["key"])
    
    # get review requests created since date
    def get(self, created_since:str):
        since = int(isoparse(created_since).timestamp())

        review_reqs_since_gen = next(self.db.fetch({
            "requested_at?gte": since,
            "submitted": True
        }))

        review_reqs_since = []
        for req in review_reqs_since_gen:
            review_reqs_since.append(req)

        return review_reqs_since

rev_req_store = ReviewRequestStore()