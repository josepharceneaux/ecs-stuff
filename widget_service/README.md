# Resume Service
Flask microservice for handling widget serving/form processing.

### Testing the Angular Widgets
Angular widgets are hosted in this service directory even though they are not specifically hosted
through flask/nginx/docker (S3).
To preview an angular widget go to the specific widget directory (`demoWidget`) and run using
`python -m <port> SimpleHTTPServer`. This will host the app on your machine through localhost.