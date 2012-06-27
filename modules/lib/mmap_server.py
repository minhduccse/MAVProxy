import BaseHTTPServer
import json
import os.path
import threading
import urlparse

DOC_DIR = os.path.join(os.path.dirname(__file__), 'mmap_app')


class Server(BaseHTTPServer.HTTPServer):
  def __init__(self, handler, address='', port=9999, module_state=None):
    BaseHTTPServer.HTTPServer.__init__(self, (address, port), handler)
    self.allow_reuse_address = True
    self.module_state = module_state


def content_type_for_file(path):
  content_types = {
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.html': 'text/html; charset=utf-8'}
  root, ext = os.path.splitext(path)
  if ext in content_types:
    return content_types[ext]
  else:
    return 'text/plain; charset=utf-8'


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
  def log_request(code, size=None):
    pass

  def do_GET(self):
    scheme, host, path, params, query, frag = urlparse.urlparse(self.path)
    if path == '/data':
      state = self.server.module_state
      data = {'lat': state.lat,
              'lon': state.lon,
              'heading': state.heading,
              'pitch': state.pitch,
              'roll': state.roll,
              'yaw': state.yaw,
              'alt': state.alt,
              'airspeed': state.airspeed,
              'groundspeed': state.groundspeed,
              'gps_fix_type': state.gps_fix_type,
              'wp_change_time': state.wp_change_time,
              'waypoints': state.waypoints}
      self.send_response(200)
      # http://www.ietf.org/rfc/rfc4627.txt says application/json.
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json.dumps(data))
    else:
      # Remove leading '/'.
      path = path[1:]
      # Ignore all directories.  E.g.  for ../../bar/a.txt serve
      # DOC_DIR/a.txt.
      unused_head, path = os.path.split(path)
      # for / serve index.html.
      if path == '':
        path = 'index.html'
      content = None
      error = None
      try:
        with open(os.path.join(DOC_DIR, path), 'rb') as f:
          content = f.read()
      except IOError, e:
        error = str(e)
      if content:
        self.send_response(200)
        self.send_header('Content-type', content_type_for_file(path))
        self.end_headers()
        self.wfile.write(content)
      else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write('Error: %s' % (error,))


def start_server(address, port, module_state):
  server = Server(
    Handler, address=address, port=port, module_state=module_state)
  server_thread = threading.Thread(target=server.serve_forever)
  server_thread.daemon = True
  server_thread.start()
  return server
