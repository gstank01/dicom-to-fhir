import os
import time
import uuid
import json
import requests
import jwt
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Parse the incoming request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_response(400, {"error": "Missing request body"})
                return

            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            identifier = body.get("identifier")

            # 2. Fetch Environment Variables
            client_id = os.getenv("CLIENTID")
            audience_url = os.getenv("AUDIENCEURL")
            private_key_text = os.getenv("BACKEND_APP_KEY")
            fhir_url = os.getenv("FHIRURL")

            if not all([private_key_text, client_id, audience_url, fhir_url]):
                self._send_response(500, {"error": "Missing required environment variables."})
                return

            # Restore escaped newlines
            private_key_text = private_key_text.replace('\\n', '\n')

            # 3. Generate Client Assertion (JWT)
            now = int(time.time())
            payload = {
                "iss": client_id,
                "sub": client_id,
                "aud": audience_url,
                "exp": now + 300,
                "jti": str(uuid.uuid4()).upper()
            }

            client_assertion = jwt.encode(
                payload,
                private_key_text,
                algorithm="RS512",
                headers={"alg": "RS512", "typ": "JWT", "kid": "myapp-key-3"}
            )

            # 4. Exchange Assertion for Access Token
            token_response = requests.post(
                audience_url,
                data={
                    "grant_type": "client_credentials",
                    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                    "client_assertion": client_assertion
                },
                timeout=10
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")

            # 5. Patient Lookup using the "DICOM to FHIR " workflow context
            patient_search_url = f"{fhir_url}/Patient?identifier={identifier}"
            patient_response = requests.get(
                patient_search_url,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                timeout=10
            )
            patient_response.raise_for_status()

            # 6. Return Success Response
            self._send_response(200, {
                "success": True,
                "message": "Patient data fetched successfully!",
                "token": access_token,
                "fhirUrl": fhir_url,
                "patientBundle": patient_response.json(),
                "identifier": identifier
            })

        except requests.exceptions.RequestException as req_err:
            self._send_response(502, {"success": False, "error": f"Network Error: {str(req_err)}"})
        except Exception as e:
            self._send_response(500, {"success": False, "error": f"Internal Server Error: {str(e)}"})

    def _send_response(self, status_code, response_dict):
        """Helper to format and send JSON responses."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_dict).encode('utf-8'))