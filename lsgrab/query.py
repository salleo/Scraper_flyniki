class Query(object):

    def __init__(self, flight_from, flight_to, departure_date, arrival_date, oneway, adult, child, infant):
        self.flight_from = flight_from
        self.flight_to = flight_to
        self.departure_date = departure_date
        self.arrival_date = arrival_date
        self.oneway = oneway
        self.adult = adult
        self.child = child
        self.infant = infant

    def __str__(self):
        return '<Query - from: {}, to: {}, departure_time: {}, arrival_time: {}, onewway: {}, adult: {}, child: {}, infant: {}>'.format(
            self.flight_from, self.flight_to, self.departure_date, self.arrival_date, self.oneway,
            self.adult, self.child, self.infant,
        )
