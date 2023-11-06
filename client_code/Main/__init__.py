from ._anvil_designer import MainTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
from .NewJob import NewJob
from .Settings import Settings
from 
class Main(MainTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    while not anvil.users.login_with_form():
      pass

  def form_show(self, **event_args):
    """This method is called when the form is shown on the page"""
    self.content_panel.add_component(NewJob())

  def job_settings_click(self, **event_args):
    """This method is called when the link is clicked"""
    alert(
      content=Settings(),
      title="Update Settings",
      large=True
    )
