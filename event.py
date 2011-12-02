from decimal import Decimal


class Event(object):
    def __init__(self):
        self.staff       = None
        self.title       = ''
        self.content     = ''
        self.start_time  = None
        self.end_time    = None
        self.client      = ''
        self.project     = ''
        self.task        = ''
        self.description = ''
        self.url1        = ''
        self.billable    = True
        self.km          = 0
        self.parking     = Decimal('0.00')
        self.expenses    = Decimal('0.00')

    def print_detail(self):
        line1 = '%s | %s | %s | %.2f | %s' % (
            self.start_time.strftime('%Y-%m-%d %H:%M'),
            self.end_time.strftime('%Y-%m-%d %H:%M'),
            self.staff,
            self.get_total_hours(),
            self.title
        )
        
        if self.billable:
            billable_value = 'billable'
        else:
            billable_value = '* not billable *'
            
        line2 = '%s | %s | %s | %s' % (
            self.client, self.project, billable_value, self.task
        )
        line3 = self.description
        print line1
        print line2
        
        if line3:
            print line3

    def __repr__(self):
        text = '<class: %s :: %s :: %s :: %s>' % (
            self.__class__.__name__,
            self.start_time,
            self.end_time,
            self.title
        )
        return text

    def get_total_hours(self, client=None, project=None):
        '''returns a "Decimal" object'''
        day_hours    = self.total_time.days * 24.0
        second_hours = self.total_time.seconds / 60.0 / 60.0
        hours = day_hours + second_hours
        return Decimal('%.2f' % hours)

    @property
    def total_time(self):
        return self.end_time - self.start_time
