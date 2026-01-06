from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    auth_code = None
    auth_state = None
    
    def do_GET(self):
        # Parse the callback URL
        if self.path.startswith('/callback'):
            query_string = self.path.split('?', 1)[1] if '?' in self.path else ''
            params = parse_qs(query_string)
            
            if 'code' in params:
                OAuthCallbackHandler.auth_code = params['code'][0]
                OAuthCallbackHandler.auth_state = params.get('state', [None])[0]
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                    <html>
                    <head><title>Authorization Success</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px; background: #121212; color: #fff;">
                        <h1 style="color: #1db954;">Authorization Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                    </body>
                    </html>
                ''')
            else:
                error = params.get('error', ['Unknown error'])[0]
                error_desc = params.get('error_description', [''])[0]
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f'''
                    <html>
                    <head><title>Authorization Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px; background: #121212; color: #fff;">
                        <h1 style="color: #ff4444;">Authorization Failed</h1>
                        <p>{error}: {error_desc}</p>
                        <p>Please close this window and try again.</p>
                    </body>
                    </html>
                '''.encode())
    
    def log_message(self, format, *args):
        # Suppress logging
        pass