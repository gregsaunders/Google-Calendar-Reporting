#!/usr/bin/python

import gdata.calendar.service

import settings
from query import Query

calendar_service = gdata.calendar.service.CalendarService()
calendar_service.email = settings.username
calendar_service.password = settings.password
calendar_service.ProgrammaticLogin()
