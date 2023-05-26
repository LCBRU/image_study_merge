#!/usr/bin/env python3

from dotenv import load_dotenv
from lbrc_flask.database import db
from lbrc_flask.security import init_roles, init_users

load_dotenv()

from image_study_merge import create_app

application = create_app()
application.app_context().push()
db.create_all()
init_roles([])
init_users()

db.session.close()
