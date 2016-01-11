from collections import namedtuple


class Quote(object):

    def __init__(self, price, currency):
        self._legs = []
        self._currency = currency
        self._price = price

    def __str__(self):
        return '<{} - price: {}, legs: {}>'.format(self.__class__.__name__,
                                                   self.price, self._legs)

    def __repr__(self):
        return str(self)

    @property
    def price(self):
        """
        :return: Price
        """
        price = Price(sum(self._price), self._currency)

        return price

    @property
    def legs(self):
        return self._legs

    def add_leg(self, leg):
        self._legs.append(leg)


class Leg(object):

    def __init__(self, price, flightid):
        self.price = price
        self._segments = []
        self.flightid = flightid

    def __str__(self):
        return '<{} - price: {}, segments: {}, flightid: {}>'.format(self.__class__.__name__,
                                                       self.price, self._segments, self.flightid)

    def __repr__(self):
        return str(self)

    @property
    def segments(self):
        return self._segments

    def add_segment(self, segment):
        self._segments.append(segment)


class Segment(object):

    def __init__(self, from_place, to_place, departure_datetime, arrival_datetime, airline_code, flight_number):
        self.from_place = from_place
        self.to_place = to_place
        self.departure_datetime = departure_datetime  # datetime with only time part
        self.arrival_datetime = arrival_datetime  # too
        self.airline_code = airline_code
        self.flight_number = flight_number

    def __str__(self):
        return '<{} -  from_place: {}, departure_datetime: {}, to_place: {}, arrival_datetime: {}, airline_code: {}, flight_number: {}>'.format(
                self.__class__.__name__, self.from_place, self.departure_datetime, self.to_place, self.arrival_datetime, self.airline_code, self.flight_number,
        )

    def __repr__(self):
        return str(self)


Price = namedtuple('Price', ['value', 'currency'])
