#TODO keep it at one place
@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"
