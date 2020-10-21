import os

from pathlib import Path
from raspador import Raspador, ScriptManeuver
from typing import Dict
from .periscope_pilot import PeriscopePilot

class PeriscopeBot(Raspador):
  def scrape(self):
    maneuver = ScriptManeuver(script_path=str(Path(__file__).parent / 'periscope_maneuver.py'))
    pilot = PeriscopePilot(config=self.configuration, browser=self.browser, user=self.user)
    self.fly(pilot=pilot, maneuver=maneuver)

    super().scrape()