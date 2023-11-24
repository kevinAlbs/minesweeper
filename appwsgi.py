import os
import sys

sys.path.insert(0, '/var/www/minesweeper')
os.chdir('/var/www/garage_checker/minesweeper')

import server

# mod_wsgi expects the application to be named `application`.
# See https://flask.palletsprojects.com/en/2.1.x/deploying/mod_wsgi/
application = server.app
