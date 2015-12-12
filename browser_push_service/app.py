import pusher

p = pusher.Pusher(
  app_id='160550',
  key='7fbaa3e3bfe2607563cb',
  secret='4f8bc5987c6f07dfd5d4',
  ssl=True,
  port=443
)
# p.trigger('test_channel', 'my_event', {'message': 'hello world'})

from flask import Flask # requires `pip install flask`
from flask import render_template
from flask import request
app = Flask(__name__)


@app.route("/")
def show_index():
    return render_template('index.html')


@app.route("/notification")
def trigger_notification():
    p.trigger('getTalent', 'push_event', {'message': 'hello world'});
    return "Notification triggered!"

if __name__ == "__main__":
    app.run(port=8011)