from raspador import Pilot, UserInteractor, BrowserInteractor
from typing import Dict, List

class PeriscopePilot(Pilot):
  config: Dict[str, any]
  sign_in_wait = 3.0

  def __init__(self, config: Dict[str, any], user: UserInteractor, browser: BrowserInteractor):
    self.config = config
    super().__init__(user=user, browser=browser)
  
  @property
  def email(self) -> str:
    return self.config['email']

  @property
  def password(self) -> str:
    return self.config['password']
  
  @property
  def base_url(self) -> str:
    return self.config['base_url']

  @property
  def dashboard_ids(self) -> List[str]:
    return self.config['dashboard_ids']

  @property
  def urls(self) -> List[str]:
    return [f'{self.base_url}/{dash_id}' for dash_id in self.dashboard_ids]