import anvil.files
from anvil.files import data_files
import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#
@anvil.server.callable
def get_settings():
    user = anvil.users.get_user()
    return app_tables.settings.get(user=user)
    
@anvil.server.callable
def save_settings(settings):
  user = anvil.users.get_user()
  user_settings = app_tables.settings.get(user=user)
  if user_settings != None:
    user_settings.update(broadcasters=settings['broadcasters'], profiles=settings['profiles'])
  else:
    app_tables.settings.add_row(user=user,broadcasters=settings['broadcasters'],profiles=settings['profiles'])