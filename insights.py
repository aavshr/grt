from datetime import datetime, timedelta
from dateutil.parser import isoparse
from statistics import mean
from math import isnan, nan

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.models import HoverTool

from code_reviews import rev_req_store

class Chart:
    def __init__(self):
        # maps durations to number of days
        self.__durations = {
            "week": 7, #number of days
            "month": 30, #number of days
        }

        # maps periods to number of seconds
        self.__periods = {
            "day":60*60*24, 
            "week": 60*60*24*7,
        }

    def __get_insights(self, duration:str, period:str):
        if not self.__durations[duration] or not self.__periods[period]:
            raise ValueError("bad duration or period")
    
        since = self.__get_since(self.__durations[duration])
        submitted_reviews = rev_req_store.get(since)
        return self.__bucket_submissions(since, period, submitted_reviews)
       
           
    def __get_since(self, days:int):
        since = datetime.now() - timedelta(days=days)
        return since.isoformat()
    
    def __bucket_submissions(self, since:str, period:str, submitted_reviews:list): 
        now_posix = int(datetime.now().timestamp())
        since_posix = int(isoparse(since).timestamp())
        
        buckets = {}
        average_buckets = {}
        separators = []
        start = since_posix+self.__periods[period]
        for start in range(since_posix, now_posix+1, self.__periods[period]):
            buckets[start] = []
            separators.append(start)

        for rev in submitted_reviews:
            for separator in separators:
                if separator > rev["requested_at"]:
                    buckets[separator].append(rev["crt"])
                    break
                
        for separator in buckets:
            date = datetime.fromtimestamp(separator)
            crts = buckets[separator]
            average_buckets[date] = nan
            if len(crts) != 0:
                average_buckets[date] = round(mean(buckets[separator])/60, 2)
            
        return average_buckets

    def __generate_chart(self, buckets:dict):
        print(buckets)
        p = figure(title="Average code review turnarounds", 
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

    def get_chart(self, duration:str, period:str):
        buckets = self.__get_insights(duration, period)
        return self.__generate_chart(buckets)
    
    def get_json(self, duration:str, period:str):
        buckets = self.__get_insights(duration, period)
        for date in buckets:
            if isnan(buckets[date]): buckets[date] = 0 
        print(buckets)
        return buckets