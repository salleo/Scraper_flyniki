# coding: utf-8

from datetime import datetime
import json
import lxml.html
import requests

import lscache
from lsgrab.query import *
from lsgrab.quote import *


class PriceTable(object):

    def __init__(self, client, query):
        self._client = client
        self._in_fl_id = ''
        # self._query = query
        self._outbound_list = []
        self._inbound_list = []
        self.fare_index_table = {}
        self._setup()

    def __str__(self):
        return '<{} - '.format(self.__class__.__name__)

    def _setup(self):
        # search for outbound flight id of the selected leg
        res = self._client.doc.xpath('//*[@'
                        'class="flightrow selected"]/td[5]')
        out_fl_id = res[0].getchildren()[2].value

        # search for fare index of the selected leg
        res = self._client.doc.xpath('//*[@class="flightrow selected"]/td[5]/label')
        fare_index = res[0].getchildren()[0].values()[3]
        if fare_index == '':
            fare_index = '0'

        # request server for information
        result = self._client.server_request('outbound', fare_index, out_fl_id)

        result_inbound = result.json()['data']['getFareList']['return']
        result_outbound = result.json()['data']['getFareList']['outbound']

        # search for inbound flight id for the fare index
        for item in result_inbound:
            if item['fareIndex'] == fare_index:
                self._in_fl_id = item['flightId']
        self.fare_index_table[(out_fl_id, self._in_fl_id)] = {'fareIndex': fare_index}

        # filling the first row and the first column in fare index table for outbound and return flight ids

        for item in result_outbound:
            if item['fareType'] == 'EASY':
                self.fare_index_table[(item['flightId'], self._in_fl_id)] = {'fareIndex': item['fareIndex']}
                self._outbound_list.append(item['flightId'])
        for item in result_inbound:
            if item['fareType'] == 'EASY':
                self.fare_index_table[(out_fl_id, item['flightId'])] = {'fareIndex': item['fareIndex']}
                self._inbound_list.append(item['flightId'])

    def get_price_doc(self):

        # filling the fare index table
        for i in self._outbound_list:

            result = self._client.server_request('outbound', self.fare_index_table[(i, self._in_fl_id)]['fareIndex'], i)
            res_inbound = result.json()['data']['getFareList']['return']

            for ii in res_inbound:
                if ii['fareType'] == 'EASY':
                    self.fare_index_table[(i, ii['flightId'])] = {'fareIndex': ii['fareIndex']}

        for i in self._outbound_list:
            for ii in self._inbound_list:
                try:
                    result = self._client.server_request('return', self.fare_index_table[(i, ii)]['fareIndex'], ii)
                    result = result.json()['templates']['priceoverview']
                    result = lxml.html.document_fromstring(result)

                    prices = result.xpath('//*[@class="totalPerPaxType"]/td')
                    pricelist = []
                    for x in xrange(3):
                        pricelist.append(prices[x+1].text[2:])
                        if pricelist[x][-3] == ',':
                            pricelist[x] = pricelist[x].replace('.', '').replace(',', '.')
                        else:
                            pricelist[x] = pricelist[x].replace(',', '')
                    self.fare_index_table[(i, ii)]['priceadult'] = float(pricelist[0])

                    if query.child != '0':
                        self.fare_index_table[(i, ii)]['pricechild'] = float(pricelist[1])
                        if query.infant != '0':
                            self.fare_index_table[(i, ii)]['priceinfant'] = float(pricelist[2])
                        else:
                            self.fare_index_table[(i, ii)]['priceinfant'] = 0
                    else:
                        self.fare_index_table[(i, ii)]['pricechild'] = 0
                        if query.infant != '0':
                            self.fare_index_table[(i, ii)]['priceinfant'] = float(prices[1])
                        else:
                            self.fare_index_table[(i, ii)]['priceinfant'] = 0
                    self.fare_index_table[(i, ii)]['price_error'] = False
                except KeyError:
                    self.fare_index_table[(i, ii)] = {'price_error': True}

            print 'iter=', i
        return self.fare_index_table





class Client(object):

    def __init__(self, locale, query):
        self._query = query
        self.locale = locale

        self._session = None
        self._session_url = None
        self._airport_name_from = None
        self._airport_name_to = None
        self._opendateoverview = ''

        self.doc = None


        self._setup()

    def __str__(self):
        return '<{} - _session_url>: {}, _airport_name_from: {}, _airport_name_to: {}, '.format(
                self.__class__.__name__, self._session_url, self._airport_name_from, self._airport_name_to)

    def _setup(self):

        self._airport_name_from = self._get_airport_name(self._query.flight_from)
        self._airport_name_to = self._get_airport_name(self._query.flight_to)

        self._query.departure_date = self._query.departure_date.strftime('%Y-%m-%d')
        self._query.arrival_date = self._query.arrival_date.strftime('%Y-%m-%d')
        self._query.adult = str(self._query.adult)
        self._query.child = str(self._query.child)
        self._query.infant = str(self._query.infant)
        if self._query.oneway:
            self._query.oneway = 'on'
        else:
            self._query.oneway = ''

        url = self._get_base_url() + '/booking/flight/vacancy.php'

        self._session = requests.Session()

        res = self._session.get(url, data={
            'departure': self._airport_name_from,
            'destination': self._airport_name_to,
            'outboundDate': query.departure_date,
            'returnDate': query.arrival_date,
            'oneway': query.oneway,
            'openDateOverview': self._opendateoverview,
            'adultCount': query.adult,
            'childCount': query.child,
            'infantCount': query.infant,
        })

        self._session_url = res.url
        print self._session_url

    def _get_base_url(self):
        return 'http://www.flyniki.com/' + self.locale

    def _get_airport_name(self, code):
        """Return airport name by airport code."""
        url = self._get_base_url() + '/site/json/suggestAirport.php'
        res = requests.get(url, params={
            'searchfor': 'departures',
            'searchflightid': '0',
            'departures[]': code,
            'suggestsource[0]': 'activeairports',
            'routesource[0]': 'airberlin',
        })
        return res.json()['suggestList'][0]['name']

    # @lscache.time_cached(28800)
    def get_quotes_doc(self):
        data = {
            '_ajax[requestParams][adultCount]': self._query.adult,
            '_ajax[requestParams][childCount]': self._query.child,
            '_ajax[requestParams][departure]': self._airport_name_from,
            '_ajax[requestParams][destination]': self._airport_name_to,
            '_ajax[requestParams][infantCount]': self._query.infant,
            '_ajax[requestParams][oneway]': self._query.oneway,
            '_ajax[requestParams][openDateOverview]': self._opendateoverview,
            '_ajax[requestParams][outboundDate]': self._query.departure_date,
            '_ajax[requestParams][returnDate]': self._query.arrival_date,
            '_ajax[requestParams][returnDeparture]': '',
            '_ajax[requestParams][returnDestination]': ''
        }
        data = data.items() + [
            ('_ajax[templates][]', 'main'),
            ('_ajax[templates][]', 'priceoverview'),
            ('_ajax[templates][]', 'infos'),
            ('_ajax[templates][]', 'flightinfo'),
        ]
        result = self._session.post(self._session_url, data=data)
        resultquotes = result.json()['templates']['main']

        self.doc = lxml.html.document_fromstring(resultquotes)

    def server_request(self, direction, fare_in, fl_id):
        data = {
            '_ajax[requestParams][direction]': direction,
            '_ajax[requestParams][fareIndex]': fare_in,
            '_ajax[requestParams][flightid]': fl_id,
        }
        data = data.items() + [
            ('_ajax[data][]', 'getFareList',),
            ('_ajax[templates][]', 'priceoverview'),
        ]
        return self._session.post(self._session_url, data=data)


class Scraper(object):

    def __init__(self, language, country):
        self.locale = '-'.join([language.lower(), country.upper()])

    def __str__(self):
        return '<{} - locale: {}>'.format(self.__class__.__name__,
                                          self.locale)

    def scrape(self, query):
        """
        scrape for flyniki.com
        :param Query query:
        :rtype: [Quote]
        """
        def get_outbound_leg_elements(doc):
            return doc.xpath('//*[@class="outbound block"]//*[contains(@class,"flightrow")]')

        def get_inbound_leg_elements(doc):
            return doc.xpath('//*[@class="return block"]//*[contains(@class,"flightrow")]')

        def get_currency(doc):
            return doc.xpath('//*[@class="outbound block"]/div[2]/table/thead/tr[2]/th[5]')

        def extract_leg(leg_element):
            leg_id = leg_element.xpath('./td[5]')
            print 'leg_element', leg_element
            fl_id = leg_id[0].getchildren()[2].attrib['value']
            price_text = leg_element.xpath('./td[5]/label/div[2]/span')[0].text
            if price_text[-3] == ',':
                price_text = price_text.replace('.', '').replace(',', '.')
            price = float(price_text)

            leg = Leg(price=price, flightid=fl_id)

            leg_details_element = leg_element.xpath('(./following-sibling::*)[1]')

            segment_elements = leg_details_element[0].xpath('.//td/table/tbody/tr')
            for element in segment_elements:
                departure_datetime = element.xpath('./td[2]/span/time')[0].text
                arrival_datetime = element.xpath('./td[3]/span/time')[0].text
                departure_airport = element.xpath('./td[2]/span')[0].text_content()[-4:-1]
                arrival_airport = element.xpath('./td[3]/span')[0].text_content()[-4:-1]
                airlines_flight = element.xpath('./td[4]')[0].text
                leg.add_segment(Segment(
                        from_place=departure_airport,
                        departure_datetime=departure_datetime,
                        to_place=arrival_airport,
                        arrival_datetime=arrival_datetime,
                        airline_code=airlines_flight[:2],
                        flight_number=airlines_flight[2:],
                ))

            return leg

        client = Client(self.locale, query)

        client.get_quotes_doc()

        currency_element = get_currency(client.doc)
        currency = currency_element[0].text

        price_index_table = PriceTable(client, query)
        price_index_table.get_price_doc()

        outbound_leg_elements = get_outbound_leg_elements(client.doc)
        outbound_legs = [extract_leg(element) for element in outbound_leg_elements]

        inbound_leg_elements = get_inbound_leg_elements(client.doc)
        inbound_legs = [extract_leg(element) for element in inbound_leg_elements]

        quotes = []
        for out_leg in outbound_legs:
            if inbound_legs:
                for in_leg in inbound_legs:
                    if not price_index_table.fare_index_table[(out_leg.flightid, in_leg.flightid)]['price_error']:
                        quote_price = [price_index_table.fare_index_table[(out_leg.flightid, in_leg.flightid)]['priceadult'],
                                       price_index_table.fare_index_table[(out_leg.flightid, in_leg.flightid)]['pricechild'],
                                       price_index_table.fare_index_table[(out_leg.flightid, in_leg.flightid)]['priceinfant'],
                                       ]
                        quote = Quote(quote_price, currency)
                        quote.add_leg(out_leg)
                        quote.add_leg(in_leg)
                        quotes.append(quote)
            else:
                quote = Quote(currency)
                quote.add_leg(out_leg)
                quotes.append(quote)

        return quotes


if __name__ == '__main__':
    query = Query(
        flight_from='LHR',
        flight_to='VIE',
        departure_date=datetime(2016, 2, 14),
        arrival_date=datetime(2016, 2, 16),
        oneway=False,
        adult=2,
        child=1,
        infant=1,
    )
    print query
    print

    scraper = Scraper('en', 'US')
    print scraper
    quotes = sorted(scraper.scrape(query), key=lambda x: x.price)
    for i, quote in enumerate(quotes):
        print 'Quote {}, price = {}{}: adults - {}, child - {}, infant - {}'.format(i, quote.price.value, quote.price.currency, query.adult, query.child, query.infant)
        for ii, leg in enumerate(quote.legs):
            print '\tLeg {}, price = {}{}'.format(ii, leg.price, quote.price.currency)
            for iii, segment in enumerate(leg.segments):
                print '\t\t {}'.format(iii), segment
        print '-' * 4
