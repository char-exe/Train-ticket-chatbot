# Built in imports
import calendar
import datetime as dt
import re

# SpaCy imports
import spacy
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span

# Project import
import db

today = dt.datetime.today()
dt_string = today.strftime("%d/%m/%Y %H:%M:%S")

nlp = spacy.load("en_core_web_sm")

phrase_matcher = PhraseMatcher(nlp.vocab)

station_names = db.get_station_data()
station_name_patterns = list(nlp.pipe(station_names[0]))
station_code_patterns = list(nlp.pipe(station_names[1]))
phrase_matcher.add("stationName", None, *station_name_patterns, *station_code_patterns)


# Defining the custom station NER pipeline
def identify_station_names(doc):
    matches = phrase_matcher(doc)
    # Creates a Span for each match and assigns them under the "STATION" label
    spans = [Span(doc, start, end, label="STATION") for match_id, start, end in matches]
    # Stores matching spans in doc.ents
    doc.ents = spans
    return doc


# Adding the custom component to the pipeline after the "ner" component
nlp.add_pipe(identify_station_names, after="ner")

# matches yes answer
yes_pattern = [
    {'LOWER': {'REGEX': '^(y|yes|yep|yeah|true|yh|ye)$'}}
]

# matches no answer
no_pattern = [
    {'LOWER': {'REGEX': '^(n|no|nah|nope|false)$'}}
]

# matches if user wants to book or check delays
service_pattern = [
    {'LOWER': {'REGEX': '^(book|booking|bookings|delay|delays)$'}}
]

# matches today, tomorrow or weekday keywords
day_pattern = [
    {'LOWER': {'REGEX': '^(today|tomorrow)$'}}
]

weekday_pattern = [
    {'LOWER': {'REGEX': '^(|monday|tuesday|wednesday|' +
                        'thursday|friday|saturday|sunday)$'}}
]

# matches date in sentence format e.g. 28th, 28th December, 28th December 2020
full_date_pattern = [
    {'LOWER': {'REGEX': '^((([0-2]\d|3[0-1])|\d)([stndrh]{2})?)$'}},
    {'LOWER': {'REGEX': '^(january|february|march|april|may|june|july' +
                        '|august|september|october|november|december)$'}, 'OP': '?'},
    {'POS': 'NUM', 'SHAPE': 'dddd', 'OP': '?'}
]

# matches following formats: dd/mm, dd/mm/yyyy, dd/mm/yy
numerical_date_pattern = [
    {'TEXT': {'REGEX': '^(([0-2]\d|3[0-1]|\d)[\/]((0[1-9]|1[0-2])|[1-9])' +
                       '([\/](\d{4}|\d{2}))?)$'}}
]

# matches following formats: dd-mm, dd-mm-yyyy
dashed_date_pattern = [
    {'TEXT': {'REGEX': '^(([0-2]\d|3[0-1]|\d))$'}},
    {'DEP': 'punct'},
    {'TEXT': {'REGEX': '^((0[1-9]|1[0-2])|[1-9])$'}},
    {'DEP': 'punct', 'OP': '?'},
    {'TEXT': {'REGEX': '^(\d{4}|\d{2})$'}, 'OP': '?'}
]

# matches military message-timestamp pattern e.g. 1300
military_time_pattern = [
    {'TEXT': {'REGEX': '^(24:00|([01]?\d|2[0-3]):([0-5]\d))$'}}
]

# matches casual message-timestamp pattern with minute specified e.g. 5:45am
casual_time_pattern = [
    {'LOWER': {'REGEX': '^(((1[0-2]|\d)|(1[0-2]|\d:[0-5]\d))([aApP][Mm]))$'}}
]

# matches casual message-timestamp pattern without minute specified e.g. 5am
casual_time_pattern2 = [
    {'LOWER': {'REGEX': '^(((1[0-2]|\d)|(1[0-2]|\d:[0-5]\d)))$'}},
    {'LOWER': {'REGEX': '^([aApP][Mm])$'}}
]

# matches 'quarter past/quarter to' message-timestamp format e.g. quarter past 5
quarter_past_to_pattern = [
    {'LOWER': 'quarter'},
    {'LOWER': {'REGEX': '^(past|to)$'}},
    {'TEXT': {'REGEX': '^([1][0-2]|\d)$'}},
    {'LOWER': 'in', 'OP': '?'},
    {'LOWER': 'the', 'OP': '?'},
    {'DEP': 'pobj', 'OP': '?'}
]

# matches 'half past' format e.g. half past 5
half_past_pattern = [
    {'LOWER': 'half'},
    {'LOWER': 'past'},
    {'TEXT': {'REGEX': '^([1][0-2]|\d)$'}},
    {'LOWER': 'in', 'OP': '?'},
    {'LOWER': 'the', 'OP': '?'},
    {'DEP': 'pobj', 'OP': '?'}
]

# Converts midday and midnight to 1200 and 0000 respectively
midday_midnight_pattern = [
    {'LOWER': {'REGEX': '^(midday|midnight)$'}}
]

midday_midnight_pattern2 = [
    {'LOWER': {'REGEX': '^(mid)$'}},
    {'LOWER': {'REGEX': '^(day|night)$'}}
]

# matches outgoing station name
outgoing_station_pattern = [
    {'LOWER': 'from'},
    {'ENT_TYPE': 'STATION', 'OP': '+'}
]

# matches destination/return station name
destination_station_pattern = [
    {'LOWER': 'to'},
    {'ENT_TYPE': 'STATION', 'OP': '+'}
]

# matches station names (useful for if outgoing/destination station is not
# specified, then can be determined by match order)
station_name_pattern = [
    {'ENT_TYPE': 'STATION'}
]

# matches any mention of minutes (used for delay PM)
minute_pattern = [
    {'LOWER': {'REGEX': '^(\d+(minute[s]?|min[s]?))$'}}
]

minute_pattern2 = [
    {'LOWER': {'REGEX': '^(\d+)$'}},
    {'LOWER': {'REGEX': '^(minutes|minute|mins|min)$'}}
]

# adds matchers and searches through input text for matches
matcher = Matcher(nlp.vocab)
matcher.add("true", None, yes_pattern)
matcher.add("false", None, no_pattern)
matcher.add("service", None, service_pattern)
matcher.add("day", None, day_pattern)
matcher.add("weekday", None, weekday_pattern)
matcher.add("fullDate", None, full_date_pattern)
matcher.add("numericalDate", None, numerical_date_pattern, dashed_date_pattern)
matcher.add("militaryTime", None, military_time_pattern)
matcher.add("casualTime", None, casual_time_pattern, casual_time_pattern2)
matcher.add("quarterHalfTime", None, quarter_past_to_pattern, half_past_pattern)
matcher.add("middayMidnightTime", None, midday_midnight_pattern,
            midday_midnight_pattern2)
matcher.add("fromStation", None, outgoing_station_pattern)
matcher.add("toStation", None, destination_station_pattern)
matcher.add("stationName", None, station_name_pattern)
matcher.add("minute", None, minute_pattern, minute_pattern2)


def weekday_converter(string):
    string = string.lower()
    todays_weekday = today.weekday()
    weekdays = [day.lower() for day in list(calendar.day_name)]
    day_no = weekdays.index(string)

    if todays_weekday == 6:
        travel_date = today + dt.timedelta(days=day_no + 1)
    elif todays_weekday == 0:
        travel_date = today + dt.timedelta(days=day_no)
    elif todays_weekday < day_no:
        travel_date = today + dt.timedelta(days=day_no - todays_weekday)
    elif todays_weekday > day_no:
        travel_date = today + dt.timedelta(days=((7 - todays_weekday) + day_no))
    else:
        travel_date = today + dt.timedelta(days=7)

    return travel_date.strftime("%d%m") + travel_date.strftime("%Y")[-2:]


def full_date_converter(string):
    this_year = int(today.strftime("%Y"))
    date_input = string.lower().split(' ')
    day, month, year = '', '', ''
    months = [month.lower() for month in list(calendar.month_name)]

    # returns nothing if just a number has been captured (just a number is too ambiguous)
    if len(date_input) == 1 and date_input[0].isdecimal():
        return None

    # removes number suffixes eg st, nd, rd from day
    date_input[0] = re.sub('[\D]', '', date_input[0])

    if len(date_input) == 2:
        day, month = date_input
    elif len(date_input) == 1:
        day = date_input[0]
        month = months[int(today.strftime("%m"))]
    else:
        day, month, year = date_input
    if month == '': month = today.strftime("%m")
    if year == '':
        # if date has already been passed in this year, assume user means next year
        if dt.datetime.strptime(day + '/' + str(months.index(month)) + '/' +
                                str(this_year), "%d/%m/%Y").date() < today.date():
            year = str(this_year + 1)
        else:
            year = today.strftime("%Y")

    # checks if day is less than two digits and adds a 0 to the front if true
    if len(day) < 2:
        day = '0' + day[0]

    month = str(months.index(month))
    if len(month) < 2: month = '0' + month

    return day + month + (year[-2:])


def numerical_date_converter(string):
    this_year = int(today.strftime("%Y"))
    if '/' in string:
        numerical_date = string.split('/')
        mode = '/'
    elif '-' in string:
        numerical_date = string.split('-')
        mode = '-'

    # making sure one digit dates have a '0' in front of them
    for i, digit in enumerate(numerical_date):
        if len(numerical_date[i]) < 2:
            numerical_date[i] = '0' + digit

    # if the year has been specified
    if len(numerical_date) == 3:

        if len(numerical_date[2]) > 2:
            numerical_date[2] = numerical_date[2][-2:]

        return ''.join(numerical_date)
    else:
        temp = ''.join(numerical_date)
        # if date has already been passed in this year, assume user means next year
        try:
            if dt.datetime.strptime(string + mode + str(this_year),
                                    "%d" + mode + "%m" + mode + "%Y").date() < today.date():
                return temp + str(this_year + 1)[-2:]
            return temp + today.strftime("%Y")[-2:]
        # if invalid date has been inputted e.g. 31st february, return nothing
        except:
            return None


def casual_time_converter(string):
    casual_time = string

    # Checks to see if minute is specified, if not '00' is injected as minutes
    if 'am' in casual_time:
        if not casual_time[1].isnumeric(): casual_time = '0' + casual_time
        if ':' in casual_time:
            return casual_time[:-2].replace(':', '')

    # Else 'pm' is in casual_time, adds 12 hours and removes 'pm'
    else:
        if not casual_time[1].isnumeric(): casual_time = '0' + casual_time
        hour = int(casual_time[0:2]) + 12
        hour = str(hour)
        casual_time = casual_time.replace(casual_time[0:2], hour)
        if ':' in casual_time:
            return casual_time[:-2].replace(':', '')

    casual_time = casual_time[:-2]
    return casual_time + '00'


def quarter_half_time_converter(string):
    temp = string
    temp = temp.split(' ')
    hour = int(temp[2])

    # time frame has been specified and captured e.g. 'in the morning'
    if len(temp) > 3:
        if "afternoon" in temp[5] or "evening" in temp[5]:
            hour = hour + 12
    # if time frame has not been specified then assume 'am' or 'pm' based on local time
    else:
        if today.hour >= 12:
            hour = hour + 12

    if "quarter" in temp[0]:
        if "to" in temp[1]:
            if hour <= 10:
                return '0' + str(hour - 1) + '45'
            return str(hour - 1) + '45'
        elif "past" in temp[1]:
            if hour < 10:
                return '0' + str(hour) + '15'

            return str(hour) + '15'

    # "half" is in temp [0] instead
    else:
        if hour < 10:
            return '0' + str(hour) + '30'

        return str(hour) + '30'


# Gets rid of 'to' or 'from' keywords if present
def station_converter(string):
    if len(string.split(' ')) > 1:
        return " ".join(string.split(' ')[1:])
    else:
        return string


def get_entities(json):
    journey_info = {}
    message = json['message']  # input text

    doc = nlp(message)  # Process the message text, creates doc object

    with doc.retokenize() as retokenizer:  # Merges multiple worded station names together into one token
        for entity in doc.ents:
            retokenizer.merge(doc[entity.start:entity.end])

    all_matches = matcher(doc)

    results = {'service': 'chat'}

    # puts all matched raw text and match IDs into a dict, also adds any station names into the results dict as a list
    for match_id, start, end in all_matches:
        match_id_string = nlp.vocab.strings[match_id]
        match = doc[start:end].text
        if match_id_string == "stationName":
            if "station_names" not in results:
                results["station_names"] = [match]
            else:
                results["station_names"].append(match)

        journey_info[match_id_string] = match

    # processes raw text in dict into a readable format by the KB e.g. 'quarter to 3 in the morning' will be
    # processed into 0245
    for match_id in journey_info:
        value = journey_info[match_id]

        if match_id == "true":
            results["answer"] = 'true'

        elif match_id == "false":
            results["answer"] = 'false'

        elif match_id == "service":
            # if user said booking keyword
            if value[0] == 'b':
                results["service"] = "book"
            # else user said delay keyword
            else:
                results["service"] = "predict"

        elif match_id == "day":
            if value == "today":
                todays_date = today.strftime("%d%m%Y")
                results["date"] = todays_date[:-4] + todays_date[-2:]
            else:
                tomorrows_date = (today + dt.timedelta(days=1)).strftime("%d%m%Y")
                results["date"] = tomorrows_date[:-4] + tomorrows_date[-2:]

        elif match_id == "weekday":
            results["date"] = weekday_converter(value)

        elif match_id == "fullDate":
            temp = full_date_converter(value)
            if temp is not None:
                results["date"] = temp

        elif match_id == "numericalDate":
            temp = numerical_date_converter(value)
            if temp is not None:
                results["date"] = temp

        elif match_id == "militaryTime":
            results["message-timestamp"] = value.replace(':', '')

        elif match_id == "casualTime":
            results["message-timestamp"] = casual_time_converter(value.lower())

        elif match_id == "quarterHalfTime":
            results["message-timestamp"] = quarter_half_time_converter(value.lower())

        elif match_id == "middayMidnightTime":
            if 'day' in value:
                results["message-timestamp"] = "1200"
            else:
                results["message-timestamp"] = "0000"

        elif match_id == "fromStation":
            results["fromStation"] = station_converter(value)

        elif match_id == "toStation":
            results["toStation"] = station_converter(value)

        elif match_id == "minute":
            results["minute"] = re.sub('\D', '', value)

    return results


# Input tests
"""
# Function testing - much easier this way
json_test = {'message': 'today'}
get_entities(json_test)
json_test = {'message': 'tomorrow'}
get_entities(json_test)
json_test = {'message': "2021-01-05"}
get_entities(json_test)
json_test = {'message': "15 mins, 15mins. 5 minutes, 1 minute, five minutes"}
get_entities(json_test)
"""
