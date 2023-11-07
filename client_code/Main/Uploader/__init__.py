from ._anvil_designer import UploaderTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.js import window, import_from, get_dom_node
import anvil.js

class Uploader(UploaderTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    #init uploader
    mod = anvil.js.import_from("https://releases.transloadit.com/uppy/v3.18.1/uppy.min.mjs")
    self.uppy = mod.Uppy().use(mod.Dashboard, {
      'inline': True,
      'target': get_dom_node(self.uppy_container)
    })
    self.uppy.use(mod.AwsS3, {
      'getUploadParameters': self.get_upload_url
    })
    #self.uppy.on('complete', self.on_complete)
  
  @anvil.js.report_exceptions
  def get_upload_url(self, file_descr):
    return anvil.server.call('get_upload_file_url', file_descr['name'], file_descr['type'])