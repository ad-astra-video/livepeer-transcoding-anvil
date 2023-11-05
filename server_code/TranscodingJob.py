import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
import anvil.server
import ffmpeg

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
@anvil.server.background_task
def save_file_loaded(file):
  user = anvil.users.get_user()
  fn = "%s_%s" % (user.get_id(), file.name)
  app_tables.jobs.add_row(file_name=file.name,user=user, file=file)
  print("source file saved for %s %s" % (user.get_id(), file.name))
  
@anvil.server.callable
def start_transcoding_job(file_name, file, profiles):
  user = anvil.users.get_user()
  job = app_tables.jobs.get(user=user, file_name=file_name)
  #set profiles of job and start it
  job.update(profiles=profiles)
  
