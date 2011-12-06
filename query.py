import time, datetime, types, yaml, copy
import string

import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import atom

from decimal import Decimal
from staff import Staff
from event import Event


class Query(object):
    def __init__(self,
            date_from=None,
            date_to=None,
            text_query=None,
            calendar_service=None,
            calendars=None,
            max_results=1000
        ):
        self.__clients_projects = {}
        
        if date_from:
            self.date_from = date_from
        else:
            self.__date_from = datetime.date(*time.localtime()[0:3])

        if date_to:
            self.date_to = date_to
        else:
            self.__date_to = datetime.date(*time.localtime()[0:3]) + datetime.timedelta(days=1)
        
        self.__text_query = text_query

        self.calendar_service = calendar_service
        self.calendars = calendars
        
        self.__last_date_from  = None
        self.__last_date_to    = None
        self.__last_text_query = None
        self.__last_result     = []

        self.__result = []
        self.__max_results = max_results

    @property
    def clients(self):
        clients = self.__clients_projects.keys()
        clients.sort()
        return clients

    @property
    def date_from(self):
        return self.__date_from

    @date_from.setter
    def date_from(self, date_from=None):
        if type(date_from) == types.StringType:
            try:
                ts = time.strptime(date_from, '%Y-%m-%d')
                self.date_from = datetime.date(ts.tm_year, ts.tm_mon, ts.tm_mday)
            except Exception, e:
                print e
                return
        else:
            self.__date_from = date_from

    @date_from.deleter
    def date_from(self):
        self.__date_from = None

    @property
    def date_to(self):
        return self.__date_to

    @date_to.setter
    def date_to(self, date_to=None):
        if type(date_to) == types.StringType:
            try:
                ts = time.strptime(date_to, '%Y-%m-%d')
                self.date_to = datetime.date(ts.tm_year, ts.tm_mon, ts.tm_mday)
            except Exception, e:
                print e
                return
        else:
            self.__date_to = date_to

    @date_to.deleter
    def date_to(self):
        self.__date_to = None

    def get_events(self, client=None, project=None):
        if client and project:
            events = self.__clients_projects[client][project]
        elif client:
            events = []
            for project in self.__clients_projects[client].keys():
                events += self.__clients_projects[client][project]
        else:
            events = self.__result

        return events

    @property
    def last_date_from(self):
        return self.__last_date_from

    @property
    def last_date_to(self):
        return self.__last_date_to

    @property
    def last_text_query(self):
        return self.__last_text_query

    def print_client_summary(self, client=None, billable='all'):
        if client:
            print 'Client:       ', client
            print 'Date from:    ', self.__date_from.strftime('%Y-%m-%d')
            print 'Date to:      ', self.__date_to.strftime('%Y-%m-%d')
            print 'Text query:   ', self.__text_query
            print 'Total time:   ', self.get_total_hours(
                client=client
            ).to_eng_string()
            print 'Billable:     ', self.get_total_hours(
                client=client, billable=True
            ).to_eng_string()
            print 'Non Billable: ', self.get_total_hours(
                client=client, billable=False
            ).to_eng_string()
            
            for project in self.projects(client):
                self.print_client_project_one_line(
                    client=client, project=project
                )
                
        else:
            print 'No client selected. Please try again.'

    def print_client_one_line(self, client=None):
        if client:
            client_text      = 'Client: %s' % (client)
            total_hours_text = '%s' % self.get_total_hours(
                client=client
            ).to_eng_string()
            print client_text.ljust(30)[:30], total_hours_text.rjust(10)
            
    def print_client_detail(self, client=None, project=None):
        if client and project:
            for event in self.get_events(client=client, project=project):
                print '-' * 80
                event.print_detail()
        elif client:
            for event in self.get_events(client=client):
                print '-' * 80
                event.print_detail()

    def print_client_project_one_line(self, client=None, project=None):
        if client and project:
            client_text  = 'Client: %s' % (client)
            project_text = 'Project: %s' % (project)

            total_hours_text = '%s' % self.get_total_hours(
                client=client, project=project
            ).to_eng_string()
            print client_text.ljust(30)[:30], project_text.ljust(30)[:30], total_hours_text.rjust(10)
            
    def print_query_summary(self):
        print 'Date from: ', self.__date_from.strftime('%Y-%m-%d')
        print 'Date to:   ', self.__date_to.strftime('%Y-%m-%d')
        print 'Text query:', self.__text_query
        print 'Total time:', self.get_total_hours().to_eng_string()

        for client in self.clients:
            self.print_client_one_line(client=client)

    def projects(self, client):
        projects = self.__clients_projects[client].keys()
        projects.sort()
        return projects

    @property
    def result(self):
        return self.__result

    @property
    def result_length(self):
        return len(self.__result)

    def run_query(self):
        self.__last_result = copy.copy(self.__result)
        self.__result = []

        self.__clients_projects = {}

        for calendar_name in self.calendars.keys():
            calendar = self.calendars[calendar_name]
            
            if self.text_query:
                query = gdata.calendar.service.CalendarEventQuery(
                    calendar, 'private', 'full', self.text_query
                )
            else:
                query = gdata.calendar.service.CalendarEventQuery(
                    calendar, 'private', 'full'
                )

            if self.date_from:
                query.start_min = self.date_from.strftime('%Y-%m-%d')
                self.__last_date_from = copy.copy(self.date_from)

            if self.date_to:
                query.start_max = self.date_to.strftime('%Y-%m-%d')
                self.__last_date_to = copy.copy(self.date_to)

            query.max_results = self.__max_results
            
            feed = self.calendar_service.CalendarQuery(query)

            for an_event in feed.entry:
                event = Event()
                event.staff   = calendar_name
                event.title   = an_event.title.text
                event.content = an_event.content.text
                
                for a_when in an_event.when:
                    start_time_ts = time.strptime(
                        a_when.start_time[0:16], '%Y-%m-%dT%H:%M'
                    )
                    start_time = datetime.datetime(
                        start_time_ts.tm_year,
                        start_time_ts.tm_mon,
                        start_time_ts.tm_mday,
                        start_time_ts.tm_hour,
                        start_time_ts.tm_min
                    )
                    event.start_time = start_time

                    end_time_ts = time.strptime(
                        a_when.end_time[0:16], '%Y-%m-%dT%H:%M'
                    )
                    end_time = datetime.datetime(
                        end_time_ts.tm_year,
                        end_time_ts.tm_mon,
                        end_time_ts.tm_mday,
                        end_time_ts.tm_hour,
                        end_time_ts.tm_min
                    )
                    event.end_time = end_time

                try:
                    content_text = an_event.content.text.replace(
                        'desc:', 'description:'
                    )
                    content_dict = yaml.load(content_text)
                    
                except Exception, e:
                    print e
                    print 'an_event.title.text:', an_event.title.text
                    
                    for a_when in an_event.when:
                        print time.strptime(
                            a_when.start_time[0:16], '%Y-%m-%dT%H:%M'
                        )

                for key in content_dict.keys():
                    '''
                    this steps through the content of the description in the
                    event entry to determin the client, project, etc.
                    '''
                    event.__dict__[key] = content_dict[key]

                self.__result.append(event)

                if not self.__clients_projects.has_key(content_dict['client']):
                    self.__clients_projects[content_dict['client']] = {}

        self.__result.sort(key=lambda x: x.start_time, reverse=False)

        for event in self.__result:
            if not event.project:
                self.__clients_projects[event.client]['None'] = []
            
            if not self.__clients_projects[event.client].has_key(event.project):
                self.__clients_projects[event.client][event.project] = []

        for event in self.__result:
            if not event.project:
                self.__clients_projects[event.client]['None'].append(event)
            else:
                self.__clients_projects[event.client][event.project].append(event)

    @property
    def text_query(self):
        return self.__text_query

    @text_query.setter
    def text_query(self, text_query=None):
        if text_query:
            self.__text_query = text_query

    @text_query.deleter
    def text_query(self):
        self.__text_query = None

    def get_total_hours(self, client=None, project=None, billable='all'):
        '''returns a "Decimal" object'''
        total_time = datetime.timedelta()
        
        if billable == 'all':
            if client:
                for event in self.get_events(client=client, project=project):
                    total_time += event.total_time
            else:
                for event in self.get_events():
                    total_time += event.total_time

        else:
            if billable == True:
                if client:
                    for event in self.get_events(client=client, project=project):
                        if event.billable == True:
                            total_time += event.total_time
                else:
                    for event in self.get_events():
                        if event.billable == True:
                            total_time += event.total_time

            else:
                if client:
                    for event in self.get_events(client=client, project=project):
                        if event.billable == False:
                            total_time += event.total_time
                else:
                    for event in self.get_events():
                        if event.billable == False:
                            total_time += event.total_time
                

        day_hours    = total_time.days * 24.0
        second_hours = total_time.seconds / 60.0 / 60.0
        hours = day_hours + second_hours
        
        return Decimal('%.2f' % hours)

    def total_time(self, client=None, project=None):
        '''returns a "datetime.timedelta" object'''
        total_time = datetime.timedelta()

        if client:
            for event in self.get_events(client=client, project=project):
                total_time += event.total_time
        else:
            for event in self.get_events():
                total_time += event.total_time

        return total_time
