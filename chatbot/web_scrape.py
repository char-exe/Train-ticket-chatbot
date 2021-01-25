import json
import requests
from __main__ import custom_to_date
from bs4 import BeautifulSoup


class Ticket(object):
    url = ""

    # Obtain contents of the whole page, needs to be filtered so that only necessary ticket info is used
    @staticmethod
    def get_page_contents(url):
        Ticket.url = url
        r = requests.get(url)
        return BeautifulSoup(r.text, 'html.parser')

    # Filter information from parsed HTML and return the single ticket information in a dictionary
    @staticmethod
    def get_ticket_single(from_location, to_location, depart_date, depart_time):
        url = ('http://ojp.nationalrail.co.uk/service/timesandfares/' + from_location + '/' + to_location
               + '/' + depart_date + '/' + depart_time + '/dep')
        html = Ticket.get_page_contents(url)
        return Ticket.get_cheapest_ticket(html, False, depart_date, None)

    # Filter information from parsed HTML and return the return ticket information in a dictionary
    @staticmethod
    def get_ticket_return(from_location, to_location, depart_date, depart_time, return_date, return_time):
        url = ('http://ojp.nationalrail.co.uk/service/timesandfares/' + from_location + '/' + to_location
               + '/' + depart_date + '/' + depart_time + '/dep/' + return_date + '/' + return_time + '/dep')
        html = Ticket.get_page_contents(url)
        return Ticket.get_cheapest_ticket(html, True, depart_date, return_date)

    # Find the cheapest ticket and add this information to a ticket dictionary to be returned
    @staticmethod
    def get_cheapest_ticket(page_contents, is_return, depart_date, return_date):

        if not page_contents:
            return None
        try:

            # Note: 'page_contents.find' might return None
            for x in page_contents.find('script', {'type': 'application/json'}):
                info = json.loads(str(x).strip())
                if not info:
                    return None

            ticket = {'url': Ticket.url, 'isReturn': is_return, 'departDate': custom_to_date(depart_date, '%d-%b-%Y'),
                      'departureStationName': str(info['jsonJourneyBreakdown']['departureStationName']),
                      'arrivalStationName': str(info['jsonJourneyBreakdown']['arrivalStationName']),
                      'departureTime': str(info['jsonJourneyBreakdown']['departureTime']),
                      'arrivalTime': str(info['jsonJourneyBreakdown']['arrivalTime'])}

            duration_hours = str(info['jsonJourneyBreakdown']['durationHours'])
            duration_minutes = str(info['jsonJourneyBreakdown']['durationMinutes'])
            ticket['duration'] = (duration_hours + 'h ' + duration_minutes + 'm')
            ticket['changes'] = str(info['jsonJourneyBreakdown']['changes'])

            if is_return:
                ticket['returnDate'] = custom_to_date(return_date, '%d-%b-%Y')
                ticket['fareProvider'] = info['returnJsonFareBreakdowns'][0]['fareProvider']
                ticket['returnTicketType'] = info['returnJsonFareBreakdowns'][0]['ticketType']
                ticket['ticketPrice'] = info['returnJsonFareBreakdowns'][0]['ticketPrice']
            else:
                ticket['fareProvider'] = info['singleJsonFareBreakdowns'][0]['fareProvider']
                ticket['ticketPrice'] = info['singleJsonFareBreakdowns'][0]['ticketPrice']

            return ticket

        except:
            return False
