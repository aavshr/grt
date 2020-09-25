from datetime import datetime, timedelta
from dateutil.parser import isoparse
from statistics import mean
from math import isnan, nan

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import HoverTool

from reviews import rev_req_store


class Chart:
    def __init__(self):
        # maps durations to number of days
        self.__durations = {
            "week": 7,  # number of days
            "month": 30,  # number of days
        }

        # maps periods to number of seconds
        self.__periods = {
            "day": 60 * 60 * 24,
            "week": 60 * 60 * 24 * 7,
        }

    # get submitted reviews bucketed by preiods based on duration
    def __get_insights(self, duration: str, period: str):
        if not self.__durations[duration] or not self.__periods[period]:
            raise ValueError("bad duration or period")

        since = self.__get_since(self.__durations[duration])
        submitted_reviews = rev_req_store.get(since)
        return self.__bucket_submissions(since, period, submitted_reviews)

    # convert duration into iso 8601 date format
    def __get_since(self, days: int):
        since = datetime.now() - timedelta(days=days)
        return since.isoformat()

    # bucket submitted reviews based on submission timestamp since date averaged by period
    def __bucket_submissions(self, since: str, period: str, submitted_reviews: list):
        now_posix = int(datetime.now().timestamp())
        since_posix = int(isoparse(since).timestamp())

        buckets = {}
        average_buckets = {}
        separators = []

        # separators are calculated based on period
        # for eg. if period is "day", separators are distanced by 86400 seconds
        start = since_posix + self.__periods[period]
        for start in range(since_posix, now_posix + 1, self.__periods[period]):
            buckets[start] = []
            separators.append(start)

        # fill the buckets
        for rev in submitted_reviews:
            for separator in separators:
                # the separaotrs are sorted in increasing order
                # so a simple comparision suffices here
                if separator > rev["requested_at"]:
                    buckets[separator].append(rev["crt"])
                    break

        # compute average for each bucket
        for separator in buckets:
            date = datetime.fromtimestamp(separator)
            crts = buckets[separator]
            average_buckets[date] = nan  # nan here to denote missing data for the chart
            if len(crts) != 0:
                average_buckets[date] = round(mean(buckets[separator]) / 60, 2)

        return average_buckets

    # generate html chart with bokeh
    def __generate_chart(self, buckets: dict):
        p = figure(
            title="Average code review turnarounds",
            x_axis_type="datetime",
            x_axis_label="date",
            y_axis_label="average turnaround (mins)",
            plot_height=800,
            plot_width=800,
        )
        x = list(buckets.keys())
        y = list(buckets.values())
        p.scatter(x, y, color="red")
        p.line(x, y, color="red", legend_label="moving average code review turnaround")
        return file_html(p, CDN, "Average code review turnarounds")

    # get html chart
    def get_chart(self, duration: str, period: str):
        buckets = self.__get_insights(duration, period)
        return self.__generate_chart(buckets)

    # get json of average values
    def get_json(self, duration: str, period: str):
        buckets = self.__get_insights(duration, period)
        for date in buckets:
            if isnan(buckets[date]):
                buckets[date] = 0
        return buckets
