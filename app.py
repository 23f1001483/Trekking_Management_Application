from flask import Flask 
from application.models import User, db

def create_app():
  app = Flask(__name__)                                                 
  app.config['SECRET_KEY'] = 'trekmate-secret-key'
  app.debug = True 
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekking.sqlite3'
  db.init_app(app)
  app.app_context().push()
  return app


app = create_app()
from application.controllers import *

if __name__ == "__main__":
  with app.app_context():
    db.create_all()
    Admin = User.query.filter_by(role='admin').first()
    if Admin is None:
      Admin = User(username='admin', email='admin@trek.com', password='1234', role='admin', is_approved=True)
      db.session.add(Admin)
      db.session.commit()
  app.run()
