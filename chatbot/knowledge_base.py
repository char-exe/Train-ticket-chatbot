import dateutil.parser
from datetime import datetime, timedelta
from experta import *

from prediction_model import predict
from web_scrape import Ticket
from __main__ import Message

today = datetime.today()


class Booking(KnowledgeEngine):

    @DefFacts()
    def _initial_action(self):

        # Reset KB on first page load
        if 'reset' in self.dictionary:
            if self.dictionary.get('reset') == 'true':
                self.dictionary['service'] = 'chat'
                self.knowledge = {}

        # Get Service, reset KB if service is either 'book' or 'predict'
        service = self.dictionary.get('service')
        if 'service' in self.knowledge:
            if service != 'chat':  # Ensures service doesn't go back to 'chat'
                self.knowledge = {'service': service}  # CREATES A NEW DICTIONARY
        else:
            self.knowledge['service'] = service  # Should always start by being 'chat'
        yield Fact(service=self.knowledge.get('service'))

        # Create initial knowledge for KB
        if 'question' not in self.knowledge:
            self.knowledge['question'] = ""
        if 'from_location' in self.knowledge:
            yield Fact(from_location=self.knowledge.get('from_location'))
        if 'to_location' in self.knowledge:
            yield Fact(to_location=self.knowledge.get('to_location'))
        if 'departure_date' in self.knowledge:
            yield Fact(departure_date=self.knowledge.get('departure_date'))
        if 'departure_time' in self.knowledge:
            yield Fact(departure_time=self.knowledge.get('departure_time'))
        if 'is_return' in self.knowledge:
            yield Fact(is_return=self.knowledge.get('is_return'))
        if 'return_date' in self.knowledge:
            yield Fact(return_date=self.knowledge.get('return_date'))
        if 'return_time' in self.knowledge:
            yield Fact(return_time=self.knowledge.get('return_time'))
        if 'ticket_found' in self.knowledge:
            yield Fact(ticket_found=self.knowledge.get('ticket_found'))

        if 'p_from_location' in self.knowledge:
            yield Fact(p_from_location=self.knowledge.get('p_from_location'))
        if 'p_to_location' in self.knowledge:
            yield Fact(p_to_location=self.knowledge.get('p_to_location'))
        if 'p_dep_time' in self.knowledge:
            yield Fact(p_dep_time=self.knowledge.get('p_dep_time'))
        if 'travel_hour' in self.knowledge:
            yield Fact(travel_hour=self.knowledge.get('travel_hour'))
        if 'off_peak' in self.knowledge:
            yield Fact(off_peak=self.knowledge.get('off_peak'))
        if 'p_current_delay' in self.knowledge:
            yield Fact(p_current_delay=self.knowledge.get('p_current_delay'))
        if 'predict_delay' in self.knowledge:
            yield Fact(predict_delay=self.knowledge.get('predict_delay'))
        if 'prediction_info_ready' in self.knowledge:
            yield Fact(prediction_info_ready=self.knowledge.get('prediction_info_ready'))
        if 'restart_conversation' in self.knowledge:
            yield Fact(restart_conversation=self.knowledge.get('restart_conversation'))

    # Ask if the user is booking or finding delays (obtain the 'service')
    @Rule(Fact(service='chat'),
          salience=98)
    def ask_service(self):
        if self.knowledge['question'] == 'ask_service':
            Message.emit_feedback('display received message', 'error_message')
        else:
            self.knowledge['question'] = 'ask_service'
        Message.emit_feedback('display received message', 'ask_service')

    # Ask where they are travelling from (can also input both 'from' and 'to' stations together)
    @Rule(Fact(service='book'),
          NOT(Fact(from_location=W())),  # from_location must not have a value
          NOT(Fact(to_location=W())),  # to_location must not have a value
          NOT(Fact(is_question=W())),  # is_question must not have a value
          salience=97)
    def ask_from(self):
        if 'station_names' in self.dictionary:
            location = self.dictionary.get('station_names')
            self.declare(Fact(from_location=location[0]))
            self.knowledge['from_location'] = location[0]
        else:
            if self.knowledge['question'] == 'ask_from':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_from'
            Message.emit_feedback('display received message', 'ask_from')
            self.declare(Fact(is_question=True))

    # Ask where they are travelling to
    # Not necessary if the user already typed two stations (e.g. 'Norwich to Ely')
    @Rule(Fact(service='book'),
          Fact(from_location=MATCH.from_location),
          NOT(Fact(to_location=W())),
          NOT(Fact(is_question=W())),
          salience=96)
    def ask_to(self):
        # User types in two or more stations (anything after the second station name is ignored)
        if 'station_names' in self.dictionary and len(self.dictionary.get('station_names')) >= 2:
            location = self.dictionary.get('station_names')
            # Prevents the station names from being identical
            if self.knowledge['from_location'] == location[1]:
                if self.knowledge['question'] == 'ask_from':  # Ensures error message is not sent when first asked
                    Message.emit_feedback('display received message', 'same_station_name')
                self.knowledge['question'] = 'ask_from'
                Message.emit_feedback('display received message', 'ask_from')
                self.declare(Fact(is_question=True))
            else:
                self.declare(Fact(to_location=location[1]))
                self.knowledge['to_location'] = location[1]
        # User only types one station
        elif 'station_names' in self.dictionary and len(self.dictionary.get('station_names')) == 1:
            location = self.dictionary.get('station_names')
            # Prevents the station names from being identical
            if self.knowledge['from_location'] == location[0]:
                if self.knowledge['question'] == 'ask_to':  # Ensures error message is not sent when first asked
                    Message.emit_feedback('display received message', 'same_station_name')
                self.knowledge['question'] = 'ask_to'
                Message.emit_feedback('display received message', 'ask_to')
                self.declare(Fact(is_question=True))
            else:
                self.declare(Fact(to_location=location[0]))
                self.knowledge['to_location'] = location[0]
        # User does not type in any stations (or the station they typed is not recognised)
        else:
            if self.knowledge['question'] == 'ask_to':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_to'
            Message.emit_feedback('display received message', 'ask_to')
            self.declare(Fact(is_question=True))

    # Ask for the departure date
    @Rule(Fact(service='book'),
          NOT(Fact(departure_date=W())),
          Fact(from_location=MATCH.from_location),
          Fact(to_location=MATCH.to_location),
          NOT(Fact(is_question=W())),
          salience=95)
    def ask_depart_date(self):
        departure_date = 'false'
        time_error = False
        if 'date' in self.dictionary:
            departure_date = self.dictionary.get('date')
            if dateutil.parser.parse(departure_date).date() < today.date():  # departure_date -> parserInfo object
                Message.emit_feedback('display received message', 'past_date')
                time_error = True
            else:
                self.declare(Fact(departure_date=departure_date))
                self.knowledge['departure_date'] = departure_date

        if self.knowledge['question'] == 'ask_depart_date' and departure_date == 'false' and not time_error:
            Message.emit_feedback('display received message', 'wrong_date')
        else:
            self.knowledge['question'] = 'ask_depart_date'

        if departure_date == 'false' or time_error:
            Message.emit_feedback('display received message', 'ask_depart_date')
            self.declare(Fact(is_question=True))

    # Ask for the departure message-timestamp
    @Rule(Fact(service='book'),
          NOT(Fact(is_question=W())),
          NOT(Fact(departure_time=W())),
          Fact(from_location=MATCH.from_location),
          Fact(to_location=MATCH.to_location),
          salience=94)
    def ask_depart_time(self):
        if 'message-timestamp' in self.dictionary:
            departure_time = self.dictionary.get('message-timestamp')
            self.declare(Fact(departure_time=departure_time))
            self.knowledge['departure_time'] = departure_time
        else:
            if self.knowledge['question'] == 'ask_depart_time':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_depart_time'
            Message.emit_feedback('display received message', 'ask_depart_time')
            self.declare(Fact(is_question=True))

    # Ask if they want a return ticket
    @Rule(Fact(service='book'),
          NOT(Fact(is_return=W())),
          NOT(Fact(is_question=W())),
          salience=93)
    def ask_is_return(self):
        if 'answer' in self.dictionary:
            answer = self.dictionary.get('answer')
            self.declare(Fact(is_return=answer))
            self.knowledge['is_return'] = answer
        else:
            if self.knowledge['question'] == 'ask_is_return':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_is_return'
            Message.emit_feedback('display received message', 'ask_is_return')
            self.declare(Fact(is_question=True))

    # If they want a return, ask for the return date
    @Rule(Fact(service='book'),
          Fact(is_return='true'),
          NOT(Fact(return_date=W())),
          NOT(Fact(is_question=W())),
          salience=92)
    def ask_return_date(self):
        return_date = 'false'
        time_error = False
        if 'date' in self.dictionary:
            return_date = self.dictionary.get('date')
            # Return date must not be before the departure date
            if dateutil.parser.parse(return_date) < dateutil.parser.parse(self.knowledge.get('departure_date')):
                Message.emit_feedback('display received message', 'past_depart_date')
                time_error = True
            else:
                self.declare(Fact(return_date=return_date))
                self.knowledge['return_date'] = return_date

        if self.knowledge['question'] == 'ask_return_date' and return_date == 'false' and not time_error:
            Message.emit_feedback('display received message', 'wrong_date')
        else:
            self.knowledge['question'] = 'ask_return_date'

        if return_date == 'false' or time_error:
            Message.emit_feedback('display received message', 'ask_return_date')
            self.declare(Fact(is_question=True))

    # If they want a return, ask for the return message-timestamp
    @Rule(Fact(service='book'),
          Fact(is_return='true'),
          NOT(Fact(return_time=W())),
          NOT(Fact(is_question=W())),
          salience=91)
    def ask_return_time(self):
        if 'message-timestamp' in self.dictionary:
            return_time = self.dictionary.get('message-timestamp')
            self.declare(Fact(return_time=return_time))
            self.knowledge['return_time'] = return_time
        else:
            if self.knowledge['question'] == 'ask_return_time':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_return_time'
            Message.emit_feedback('display received message', 'ask_return_time')
            self.declare(Fact(is_question=True))

    # Show the single ticket, if it is a single
    @Rule(Fact(service='book'),
          NOT(Fact(ticket_found=W())),
          Fact(is_return='false'),
          Fact(from_location=MATCH.from_location),
          Fact(to_location=MATCH.to_location),
          Fact(departure_date=MATCH.departure_date),
          Fact(departure_time=MATCH.departure_time),
          salience=90)
    def show_single_ticket(self, from_location, to_location, departure_date, departure_time):
        if 'ticket_found' not in self.knowledge:
            ticket = Ticket.get_ticket_single(from_location, to_location, departure_date, departure_time)
            if not ticket:
                Message.emit_feedback('display received message', 'ticket_error')
                Message.emit_feedback('display received message', 'restart_the_conversation')
                self.declare(Fact(ticket_found=False))
                self.knowledge['ticket_found'] = False
            else:
                Message.emit_feedback('display received message', 'ticket_found_single')
                Message.emit_ticket('display ticket', ticket)
                self.knowledge['url'] = ticket.get('url')
                self.declare(Fact(ticket_found=True))
                self.knowledge['ticket_found'] = True

    # Show the return ticket, if it is a return
    @Rule(Fact(service='book'),
          NOT(Fact(ticket_found=W())),
          Fact(is_return='true'),
          Fact(from_location=MATCH.from_location),
          Fact(to_location=MATCH.to_location),
          Fact(departure_date=MATCH.departure_date),
          Fact(departure_time=MATCH.departure_time),
          Fact(return_date=MATCH.return_date),
          Fact(return_time=MATCH.return_time),
          salience=89)
    def show_return_ticket(self, from_location, to_location, departure_date, departure_time, return_date, return_time):
        if not 'ticket_found' in self.knowledge:
            ticket = Ticket.get_ticket_return(from_location, to_location, departure_date, departure_time, return_date,
                                              return_time)
            if not ticket:
                Message.emit_feedback('display received message', 'ticket_error')
                Message.emit_feedback('display received message', 'restart_the_conversation')
                self.declare(Fact(ticket_found=False))
                self.knowledge['ticket_found'] = False
            else:
                Message.emit_feedback('display received message', 'ticket_found_return')
                Message.emit_ticket('display ticket', ticket)
                self.knowledge['url'] = ticket.get('url')
                self.declare(Fact(ticket_found=True))
                self.knowledge['ticket_found'] = True

    # Ask if they wish to proceed with this ticket
    @Rule(Fact(service='book'),
          Fact(ticket_found=True),
          salience=88)
    def confirm_booking(self):
        # Prevents 'no' from asking for a single ticket being used to prevent booking confirmation
        if 'answer' in self.dictionary and self.knowledge['question'] == 'confirm_booking':
            if self.dictionary.get('answer') == 'true':
                Message.queue_feedback('url')
                Message.emit_message('display received message',
                                     '<a href="' + self.knowledge.get('url') + '">' + self.knowledge.get(
                                         'url') + '</a>')
            Message.queue_feedback('thank_you')
            self.knowledge['ticket_found'] = False
            self.declare(Fact(restart_conversation=True))
            self.knowledge['restart_conversation'] = True
        else:
            if self.knowledge['question'] == 'confirm_booking':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'confirm_booking'
            Message.emit_feedback('display received message', 'confirm_booking')

    # Ask for the last station visited
    @Rule(Fact(service='predict'),
          NOT(Fact(p_from_location=W())),  # predicted from location must be empty
          NOT(Fact(p_to_location=W())),  # predicted to location must be empty
          NOT(Fact(is_question=W())),
          salience=87)
    def ask_predict_last_station(self):
        if 'station_names' in self.dictionary and len(self.dictionary.get('station_names')) >= 2:
            location = self.dictionary.get('station_names')
            if location[0] == location[1]:
                if self.knowledge['question'] == 'ask_predict_last_station':
                    Message.emit_feedback('display received message', 'same_station_name')
                else:
                    self.knowledge['question'] = 'ask_predict_last_station'
                Message.emit_feedback('display received message', 'ask_predict_last_station')
                self.declare(Fact(is_question=True))
            else:
                self.declare(Fact(p_from_location=location[0]))
                self.knowledge['p_from_location'] = location[0]
                self.declare(Fact(p_to_location=location[1]))
                self.knowledge['p_to_location'] = location[1]
        elif 'station_names' in self.dictionary and len(self.dictionary.get('station_names')) == 1:
            location = self.dictionary.get('station_names')
            self.declare(Fact(p_from_location=location[0]))
            self.knowledge['p_from_location'] = location[0]
        else:
            if self.knowledge['question'] == 'ask_predict_last_station':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_predict_last_station'
            Message.emit_feedback('display received message', 'ask_predict_last_station')
            self.declare(Fact(is_question=True))

    # Ask for the expected departure message-timestamp of that station
    @Rule(Fact(service='predict'),
          Fact(p_from_location=MATCH.p_from_location),
          NOT(Fact(p_to_location=W())),  # predicted to location must be empty
          NOT(Fact(p_dep_time=W())),  # current delay must be empty
          NOT(Fact(is_question=W())),
          salience=86)
    def ask_predicted_departure(self, p_from_location):
        if 'message-timestamp' in self.dictionary:
            p_dep_time = self.dictionary.get('message-timestamp')
            travel_hour = int(p_dep_time[0:2])
            if travel_hour > 23:
                travel_hour = int(travel_hour / 10)
            off_peak = 1
            if (6 <= travel_hour <= 9) or (16 <= travel_hour <= 18):
                off_peak = 0

            self.declare(Fact(p_dep_time=p_dep_time))
            self.knowledge['p_dep_time'] = p_dep_time

            self.declare(Fact(travel_hour=travel_hour))
            self.knowledge['travel_hour'] = travel_hour

            self.declare(Fact(off_peak=off_peak))
            self.knowledge['off_peak'] = off_peak
        else:
            if self.knowledge['question'] == 'ask_predicted_departure':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_predicted_departure'
            Message.emit_feedback('display received message', 'ask_p_departure_time', p_from_location)
            self.declare(Fact(is_question=True))

    # Ask how late the user departed the last station
    @Rule(Fact(service='predict'),
          NOT(Fact(p_current_delay=W())),  # current delay must be empty
          Fact(p_from_location=MATCH.p_from_location),
          NOT(Fact(is_question=W())),
          salience=85)
    def ask_current_delay(self, p_from_location):
        if 'minute' in self.dictionary:
            p_current_delay = self.dictionary.get('minute')
            self.declare(Fact(p_current_delay=p_current_delay))
            self.knowledge['p_current_delay'] = p_current_delay
            if 'p_to_location' in self.knowledge:  # We have all the info we need, no need to ask destination station
                self.declare(Fact(prediction_info_ready=True))
                self.knowledge['prediction_info_ready'] = True
        else:
            if self.knowledge['question'] == 'ask_current_delay':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_current_delay'
            Message.emit_feedback('display received message', 'ask_current_delay', p_from_location)
            self.declare(Fact(is_question=True))

    # Ask for the destination station
    @Rule(Fact(service='predict'),
          NOT(Fact(p_to_location=W())),  # predicted to location must be empty
          NOT(Fact(is_question=W())),
          salience=84)
    def ask_predict_destination(self):
        if 'station_names' in self.dictionary:
            location = self.dictionary.get('station_names')
            if self.knowledge.get('p_from_location') == location[0]:
                if self.knowledge['question'] == 'ask_predict_destination':
                    Message.emit_feedback('display received message', 'same_station_name')
                else:
                    self.knowledge['question'] = 'ask_predict_destination'
                Message.emit_feedback('display received message', 'ask_predict_destination')
                self.declare(Fact(is_question=True))
            else:
                self.declare(Fact(p_to_location=location[0]))
                self.knowledge['p_to_location'] = location[0]
                self.declare(Fact(prediction_info_ready=True))
                self.knowledge['prediction_info_ready'] = True
        else:
            if self.knowledge['question'] == 'ask_predict_destination':
                Message.emit_feedback('display received message', 'error_message')
            else:
                self.knowledge['question'] = 'ask_predict_destination'
            Message.emit_feedback('display received message', 'ask_predict_destination')
            self.declare(Fact(is_question=True))

    # Predict the arrival delay
    @Rule(Fact(service='predict'),
          Fact(prediction_info_ready=True),
          Fact(p_from_location=MATCH.p_from_location),
          Fact(p_to_location=MATCH.p_to_location),
          Fact(p_current_delay=MATCH.p_current_delay),
          Fact(off_peak=MATCH.off_peak),
          Fact(travel_hour=MATCH.travel_hour),
          salience=83)
    def predict_delay(self, p_from_location, p_to_location, p_current_delay, off_peak, travel_hour):

        prediction_data = predict(p_current_delay, off_peak, travel_hour, p_from_location, p_to_location)

        if prediction_data is not None:
            Message.emit_feedback('display received message', 'prediction', str(prediction_data))
        else:
            Message.emit_feedback('display received message', 'prediction_error')
        self.knowledge['prediction_info_ready'] = False
        self.declare(Fact(restart_conversation=True))
        self.knowledge['restart_conversation'] = True

    # Loop the conversation back to the beginning
    @Rule(Fact(restart_conversation=True),
          salience=82)
    def restart_the_conversation(self):
        if self.knowledge['question'] == 'restart_the_conversation':
            Message.emit_feedback('display received message', 'error_message')
        else:
            self.knowledge['question'] = 'restart_the_conversation'
        Message.emit_feedback('display received message', 'restart_the_conversation')


# Obtain the dictionary output from the NLPU, give it to the KB and run it
def get_nlpu_info(dictionary):
    engine.dictionary = dictionary
    engine.reset()
    engine.run()


# Initialize the engine with no knowledge
engine = Booking()
engine.knowledge = {}
