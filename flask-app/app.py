__author__ = 'aouyang1'

from flask import Flask, render_template, redirect, url_for, request, jsonify, json
from cassandra.cluster import Cluster
import csv
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time

app = Flask(__name__)
cluster = Cluster(['54.215.184.69'])
session = cluster.connect('puppy')


county_code_file = open('county_codes.csv','rb')
wr = csv.reader(county_code_file)
codes = [code for code in wr][0]

county_name_file = open('county_names.csv','rb')
wr = csv.reader(county_name_file)
names = [name for name in wr][0]

county_code_dict = {}
for name, code in zip(names, codes):
    county_code_dict[name] = code

code_county_dict = {code: name for name, code in county_code_dict.items()}

@app.route('/')
def main_page():

    county = "Denton County"
    state = "TX"


    county_month = session.execute("SELECT * FROM by_county_month WHERE state = '" + state + "' AND county = '" + county + "'")

    def date_to_milli(time_tuple):
        epoch_sec = time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0))
        return 1000*int(time.mktime(time_tuple) - epoch_sec)

    historical_data = []
    for row in county_month:
        curr_date = row.date
        year = curr_date/100
        month = curr_date - year*100
        historical_data.append([date_to_milli((year, month, 0, 0, 0, 0, 0, 0, 0)), row.count])

    return render_template('index.html', state=state, county=county, historical_data=historical_data)


@app.route('/new_messages/<county_code>/')
def update_messages(county_code):
    # query cassandra for top 5 recent messages from a county
    # format into "timestamp user: message"

    county = code_county_dict[county_code]
    county_state = [county_attr.strip() for county_attr in county.split(",")]

    county = county_state[0]
    state = county_state[1]

    curr_time = datetime.utcnow()

    fetch_date = str(curr_time.year) + "%02d" % curr_time.month + "%02d" % curr_time.day
    fetch_time_to = "%02d" % curr_time.hour + "%02d" % curr_time.minute + "%02d" % curr_time.second

    fetch_time_from = "%02d" % curr_time.hour + "%02d" % curr_time.minute + "%02d" % max(curr_time.second-30, 0)


    # Test access to by_couny_msgs table in Cassandra
    test_query = session.execute("SELECT * FROM by_couny_msgs WHERE state='{}' AND county='{}' LIMIT 5".format(state, county))
    print test_query


    query = "SELECT * FROM by_couny_msgs WHERE state='{}' AND county='{}' AND date={} AND time>{} AND time<={}".format(state, county, fetch_date, fetch_time_from, fetch_time_to)

    messages_rt = session.execute(query)
    print county_code, query                                       
   

    if len(messages_rt)>=5:
        recent_messages = messages_rt[-6:-1]
        recent_messages.reverse()
    else:
        messages_rt.reverse()
        recent_messages = messages_rt

    message_list = map(parse_jobject_string_to_message, recent_messages)
    for msg in message_list:
        print msg
    return jsonify(msg=message_list, county=county, state=state)


@app.route('/update_map/')
def update_map():
    county_rt = session.execute("SELECT * FROM by_county_rt")
   
    # example format [{"code":"us-al-001","name":"Autauga County, AL","value":6.3},...]

    rt_data = []
    for county in county_rt:
        if county.county == 'District of Columbia':
	    county_name_in_dict = county.county
	else:
            county_name_in_dict = "{}, {}".format(county.county, county.state)

        county_code = county_code_dict[county_name_in_dict]
        rt_data.append({"code": county_code, "name": county_name_in_dict, "value": county.count})

    return jsonify(rt_data=rt_data)


@app.route('/update_chart/<interval>/<county_code>/')
def update_chart(interval, county_code):

    county = code_county_dict[county_code]
    county_state = [county_attr.strip() for county_attr in county.split(",")]

    county = county_state[0]
    state = county_state[1]

    county_month = session.execute("SELECT * FROM by_county_" + interval + " WHERE state = '" + state + "' AND county = '" + county + "'")

    def date_to_milli(time_tuple):
        epoch_sec = time.mktime((1970, 1, 1, 0, 0, 0, 0, 0, 0))
        return 1000*int(time.mktime(time_tuple) - epoch_sec)

    historical_data = []
    for row in county_month:
        curr_date = row.date
        if interval=="month":
            year = curr_date/100
            month = curr_date - year*100
            day = 0
            hour = 0
        elif interval=="day":
            year = curr_date/10000
            month = (curr_date - year*10000)/100
            day = (curr_date - year*10000 - month*100)
            hour = 0
        elif interval=="hour":
            year = curr_date/1000000
            month = (curr_date - year*1000000)/10000
            day = (curr_date - year*1000000 - month*10000)/100
            hour = (curr_date - year*1000000 - month*10000 - day*100)

        historical_data.append([date_to_milli((year, month, day, hour, 0, 0, 0, 0, 0)), row.count])

    return jsonify(state=state, county=county, historical_data=historical_data)


def parse_jobject_string_to_message(jobj):
    stripped_msgs = jobj.message.replace("JObject","").replace("JInt","").replace("JString","").replace("JArray","").replace("(","").replace(")","").replace("List","")

    message_list = [keyval.strip() for keyval in stripped_msgs.split(",")]
    message_list = map(lambda x: str(x), message_list)

    county = message_list[1]
    state = message_list[3]
    creatorID = message_list[5]
    messageID = message_list[7]
    timestamp = message_list[10] + '/' + message_list[11] + '/' + message_list[9] + ' ' + message_list[12] + ':' + message_list[13] + ':' + message_list[14]
    message = message_list[16]
    senderID = message_list[18]
    rank = message_list[20]
    return "{} {}: {}".format(timestamp, creatorID, message)




if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
