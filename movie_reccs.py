from flask import Flask, render_template, request, session
app = Flask(__name__)
app.secret_key="asdkjnah"

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/quiz', methods=['POST', 'GET'])
def quiz():
   if not 'ticker' in session:
      session['ticker'] = 0
   if request.method == 'POST':
      session['ticker'] = session['ticker'] + int(request.form['submit_btn'])
   return render_template('quiz.html', answer=session['ticker'])

if __name__ == '__main__':
   app.run()