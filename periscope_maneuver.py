import re
import datetime
import importlib

from periscope.periscope_pilot import PeriscopePilot
from raspador import Maneuver, OrdnanceManeuver, NavigationManeuver, SequenceManeuver, UploadReportRaspador, ClickXPathSequenceManeuver, InteractManeuver, OrdnanceParser, XPath, RaspadorNoOrdnanceError, ClickXPathManeuver, SeekParser, SoupElementParser, FindElementManeuver, ClickSoupElementManeuver, Element, ElementManeuver, ClickElementManeuver
from typing import Generator, Optional, Dict, List, Callable
from time import sleep
from bs4 import BeautifulSoup, Tag

class SignInManeuver(Maneuver[PeriscopePilot]):
  def attempt(self, pilot: PeriscopePilot):
    email_element = yield ClickElementManeuver(
      instruction='click the email filed',
      seeker=lambda p: p.soup.find('input', placeholder='Enter email address')
    )
    email_element.ordnance.send_keys(pilot.email)

    password_element = yield ClickElementManeuver(
      instruction='click the password field',
      seeker=lambda p: p.soup.find('input', placeholder='Enter password')
    )
    password_element.ordnance.send_keys(pilot.password)

    yield ClickElementManeuver(
      instruction='click the login button',
      seeker=lambda p: p.soup.find('span', text='LOG IN')
    )
    sleep(pilot.sign_in_wait)

class DismissPopUpManeuver(Maneuver[PeriscopePilot]):
  def attempt(self, pilot: PeriscopePilot):
    tries = 0
    while tries < 3:
      try:
        dismiss_popup = yield ElementManeuver(
          instruction='dismiss popup',
          seeker=lambda p: p.soup.find('div', {'title': 'Stop Walk-thru'})
        )
        dismiss_popup.ordnance.click()
        break
      except RaspadorNoOrdnanceError:
        tries = tries + 1
        continue

class OpenFilterBarManeuver(Maneuver[PeriscopePilot]):
  def attempt(self, pilot: PeriscopePilot, fly: Callable[[Maneuver], Maneuver]):
    fly(ClickElementManeuver(
      instruction='open the filter bar',
      seeker=lambda p: p.soup.find('div', {'class': 'filters-bar'})
    ))

class DimensionElementsParser(OrdnanceParser[List[Tag]]):
  def parse(self):
    self.ordnance = self.soup.find_all('div', {'class': 'dimension-setting'})
    return self

class EditIconChildParser(OrdnanceParser[List[str]]):
  def parse(self, filter_element):
    edit_icons = filter_element.soup_element.find_all('div', {'class': 'edit-icon'})
    self.ordnance = [self.xpath_for_element(edit_icon) for edit_icon in edit_icons]
    return self

class RefreshFilterManeuver(Maneuver[PeriscopePilot]):
  def __init__(self):
    super().__init__()

  def attempt(self, pilot: PeriscopePilot, fly: Callable[[Maneuver], Maneuver]):
    fly(ClickElementManeuver(
      instruction='click the refresh icon',
      seeker=lambda p: p.soup.find('div', {'class': 'refresh-icon'})
    ))

class RefreshFiltersManeuver(Maneuver[PeriscopePilot]):
  def attempt(self, pilot: PeriscopePilot, fly: Callable[[Maneuver], Maneuver]):
    parser = DimensionElementsParser.from_browser(browser=pilot.browser)
    dimension_elements = parser.parse().deploy()
    filter_elements = [
      Element(soup_element=dimension_element, browser=pilot.browser)
      for dimension_element in dimension_elements
    ]
    # Hide all the filters with css
    for filter_element in filter_elements:
     filter_element.set_css_property('display', 'none')
    # Loop through all the now invisible filters
    #   - display each one in the top, left corner of the filter area
    #   - open it and perform the refresh maneuver
    #   - make it invisible again
    for filter_element in filter_elements:
      filter_element.set_css_property('display', 'inherit')
      filter_element.set_css_property('top', '0px')
      filter_element.set_css_property('left', '0px')
      filter_element.set_css_property('zIndex', '100')
      filter_element.add_class('open')
      edit_icon_xpaths = EditIconChildParser.from_browser(pilot.browser).parse(filter_element).deploy()
      if len(edit_icon_xpaths) > 0:
        edit_icon_element = Element(xpath=edit_icon_xpaths[0], browser=pilot.browser)
        edit_icon_element.click()
        fly(RefreshFilterManeuver())
        sleep(1)
      filter_element.set_css_property('display', 'none')

class PeriscopeManeuver(Maneuver[PeriscopePilot]):
  def attempt(self, pilot: PeriscopePilot):
    yield NavigationManeuver(url='https://app.periscopedata.com/login?controller=welcome')
    yield SignInManeuver()

    for url in pilot.urls:
      yield NavigationManeuver(url=url)
      sleep(5)
      try:
        yield DismissPopUpManeuver()
      except:
        import pdb; pdb.set_trace()
      yield OpenFilterBarManeuver()
      yield RefreshFiltersManeuver()

    yield InteractManeuver()

if __name__ == '__main__':
  enqueue_maneuver(PeriscopeManeuver())
else:
  enqueue_maneuver(RefreshFilterManeuver(edit_element=Element(xpath='html[1]/body[1]/div[1]/div[3]/div[4]/div[2]/div[1]/div[4]/header[1]/div[1]')))
