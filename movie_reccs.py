from flask import Flask, render_template, request, session
app = Flask(__name__)
app.secret_key="asdkjnah"

@app.route('/')
def index():
   return render_template('index.html')

@app.route('/quiz', methods=['POST', 'GET'])
def quiz():
   if not 'user_vec' in session:
      #store a vector representing the user's reccomendation data; TODO: determine what dim we want here
      session['user_vec'] = [0, 0, 0, 0, 0]
      #load a set of questions; TODO: from external file, mix & match compatible answers
      session['questions'] = [
         [("Tom Cruise", [-1, 3, 0, 0, 1]), ("Tom Hanks", [5, 0, 3, 4, 0])],
         [("Chocolate", [7, 4, 0, 3, 1]), ("Popcorn", [-2, 7, 3, 4, 8])],
         [("Valentine's Day", [-1, 3, 0, 0, 1]), ("Halloween", [5, 0, 3, 4, 0])],
      ]
      #set initial number of questions to 0
      session['q_asked'] = 0

   if request.method == 'POST':
      #update user's vector based on their responses
      answer_vec = session['questions'][session['q_asked']][int(request.form['submit_btn'])][1]
      for i in range(len(session['user_vec'])):
         session['user_vec'][i] = session['user_vec'][i] + answer_vec[i]
      #increment count of questions asked
      session['q_asked'] = session['q_asked'] + 1

   #give user new questions
   answer1=session['questions'][session['q_asked']][0][0]
   answer2=session['questions'][session['q_asked']][1][0] 
   return render_template('quiz.html', output=session['user_vec'], answer1 = answer1, answer2 = answer2)

if __name__ == '__main__':
   app.run()