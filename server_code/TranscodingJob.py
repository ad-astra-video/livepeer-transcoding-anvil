import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users, anvil.server, anvil.http
from anvil.server import http_endpoint, request
import json, boto3
import ffmpeg, pathlib

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

@anvil.server.http_endpoint('/transcode', authenticate_users=True)
def transcode():
  req_data = request.body_json
  job = app_tables.jobs.add_row(user=anvil.users.get_user(), job_details=req_data, in_progress=True, req_url=request.remote_address)
  #start transcoding job
  start_transcode(job)
  
@anvil.server.background_task
def start_transcode(job):
  job_details = job['job_details']
  #download the file
  if not os.path.exists("/srv/videos/inputs"):
    os.makedirs("/srv/videos/inputs", exist_ok=True)
  if not os.path.exists("/srv/videos/segments"):
    os.makedirs("/srv/videos/segments", exist_ok=True)
  if not os.path.exists("/srv/videos/transcoded"):
    os.makedirs("/srv/videos/transcoded", exist_ok=True)
  try:
    s3 = boto3.client(service_name='s3', 
                    aws_access_key_id=job_details["input"]["credentials"]["accessKeyId"], 
                    aws_secret_access_key=job_details["input"]["credentials"]["secretAccessKey"])
    fp = f"/srv/videos/inputs/{job['user'].get_id()}_{job_details['input']['bucket']}_{job_details['input']['path']}"
    s3.download_file(job_details["input"]["bucket"], job_details["input"]["path"], fp)
  except botocore.exceptions.ClientError as e:
    job['error'] = e.response
    if e.response['Error']['Code'] == "404":
      print("The object does not exist.")
    else:
      print("error getting file")
    return

  #start watcher that will submit segments for transcoding
  vid_path = pathlib.Path(job_details['input']['path'])
  vid_ext = vid_path.suffix
  vid_fn = f"/srv/videos/segments/{job['user'].get_id()}_{job_details['input']['bucket']}_{vid_path.stem}"
  start_transcode_requests_watcher(job, vid_fn, vid_ext)
  #segment the video
  ffmpeg.input(fp).output(f"{vid_fn}_%d{vid_ext}", f='segment', segment_time='10').run()

@anvil.server.background_task
def start_transcode_requests_watcher(job, vid_fn, vid_ext):
  #give segmenter some time to start up
  time.sleep(10)
  transcodes_in_process = []
  seg_num = 0
  while True:
    if len(transcodes_in_process) <= 5:
      seg = f"{vid_fn}_{seg_num}{vid_ext}"
      if os.path.exists(seg):
        t_proc = send_transcode_request(job, seg, 1)
        transcodes_in_process.append(t_proc)
        seg_num += 1 #move to next segment
      else:
        time.sleep(1) #let segmenter catch up
    else:
      for t in range(0,5):
        t_status = transcodes_in_process[t].get_termination_status()
        if t_status != None:
          if t_status == "completed":
            transcodes_in_process.pop(t)
          else:
            if t_status == "failed":
              transcodes_in_process[t] = send_transcode_request(transcodes_in_process[t].task_state['job'], transcodes_in_process[t].task_state['segment'], transcodes_in_process[t].task_state['attempt'])
            
      
@anvil.server.background_task
def send_transcode_request(job, segment, attempt):
  anvil.server.task_state['segment'] = segment
  anvil.server.task_state['job'] = job
  anvil.server.task_state['attempt'] = attempt
  anvil.server.task_state['error'] = ""
  anvil.server.task_state['retry'] = True
  job_details = job['job_details']
  
  #get segment information
  try:
    probe = ffmpeg.probe(segment)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])
  except ffmpeg.Error as e:
    print("Error: Could not get file information "+e.stderr)
    anvil.server.task_state['error'] = "could not get segment information"
    add_error_segment(job, segment, attempts)
    return
    
  with open(segment,'rb') as segment_file:
    data = segment_file.read()
    seg_name = segment.split("/")[-1]
      
    try:
      headers = {'Accept':'multipart/mixed','Content-Duration':'10000','Content-Resolution':str(width)+"x"+str(height)}
      resp = anvil.http.request("http://127.0.0.1:3935/live/"+seg_name, 
                               method="POST",
                               headers = {'Accept':'multipart/mixed','Content-Duration':'10000','Content-Resolution':'1920x1080'},
                               data=data,
                               timeout=60)
      #save the transcoded renditions
      if resp.headers['content-type'][:15] =='multipart/mixed':
        transcoded_segment_folder = os.path.dirname(segment.replace("/srv/videos/segments/", "/srv/videos/transcoded/"))
        decoded = MultipartDecoder.from_response(resp)
        for part in decoded.parts:
          disposition = part.headers[b'content-disposition']
          filename = parse_stream_resp_hdr(disposition)['filename']  
          rendition = part.headers[b'rendition-name']
          transcoded_file_name = transcoded_segment_folder+"/"+rendition+"/"+filename
          #make directories for transcoded segments
          os.makedirs(os.path.dirname(CLIP_RESULTS_PATH.format(eth_address=eth_address, region=WORKER_REGION, results_file='0.ts')), exist_ok=True)
          #get the binary data of the rendition
          rendition = part.content #actual transcoded stream
          with open(transcoded_file_name,'wb') as t:
              t.write(rendition)
        
        #received completed segment add to completed segments
        add_completed_segment(job, transcoded_file_name, attempt)
    except anvil.http.HttpError as e:
      print(f"Segment Transcode Error:  {e.status} {e.content}")
      anvil.server.task_state['error'] = f"{e.status} {e.content}"
  
def add_completed_segment(job, segment, attempts):
  if job['completed_segments'] != None:
    job['completed_segments'].append({"segment":segment, "attempts":attempt})
  else:
    job['completed_segments'] = [].append({"segment":segment, "attempts":attempt})

def add_error_segment(job, segment, attempts):
  if job['error_segments'] != None:
    job['error_segments'].append({"segment":segment, "attempts":attempt})
  else:
    job['error_segments'] = [].append({"segment":segment, "attempts":attempt})

#  livepeer.transcode({
#  input: {
#    type: "s3",
#    endpoint: "https://gateway.storjshare.io",
#    credentials: {
#      accessKeyId: "$ACCESS_KEY_ID",
#      secretAccessKey: "$SECRET_ACCESS_KEY"
#    },
#    bucket: "mybucket",
#    path: "/video/source.mp4"
#  },
#  storage: {
#    type: "s3",
#    endpoint: "https://gateway.storjshare.io",
#    credentials: {
#      accessKeyId: "$ACCESS_KEY_ID",
#      secretAccessKey: "$SECRET_ACCESS_KEY"
#    },
#    bucket: "mybucket"
#  },
#  outputs: {
#    hls: {
#      path: "/samplevideo/hls"
#    },
#    mp4: {
#      path: "/samplevideo/mp4"
#    }
#  },
#  profiles: [
#    {
#      name: "480p",
#      bitrate: 1000000,
#      fps: 30,
#      width: 854,
#      height: 480
#    },
#    {
#      name: "360p",
#      bitrate: 500000,
#      fps: 30,
#      width: 640,
#      height: 360
#    }
#  ]
#});
