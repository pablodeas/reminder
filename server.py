from flask import Flask, jsonify, request
from database import Session, init_db
from models import Reminder

init_db()

app = Flask(__name__)


@app.route('/super')
def super():
    return jsonify(message="It's working"), 200

@app.route('/list')
def list():
    session = Session()
    rem = session.query(Reminder).order_by(Reminder.event_date.asc()).all()
    
    reminders_list = []
    for reminder in rem:
        reminders_list.append({
            "event_date": str(reminder.event_date),
            "message": reminder.message
        })
    
    return jsonify(reminders=reminders_list), 200
    session.close()


if __name__ == "__main__":
    app.run(port=5050)
