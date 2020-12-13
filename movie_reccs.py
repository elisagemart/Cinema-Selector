from flask import Flask, render_template, request, session, g
import pandas, random, math, json
from scipy import spatial
import sqlite3

app = Flask(__name__)
app.secret_key="asdkjnah"

DATABASE = 'MoviesDB.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


#returns movies in format [Title, Pop, Overview, Poster, <genre_vec>, <actor_vec>, <dir_vec>, <key_vec>]
def format_mov(mov):
   return [mov[1], mov[2], mov[3], mov[4], json.loads(mov[5]), json.loads(mov[6]), json.loads(mov[7]), json.loads(mov[8])]

@app.route('/index')
@app.route('/')
def index():
   #reset data if user has some stored
   if 'q_asked' in session:
      session['q_asked'] = -1
   
   return render_template('index.html')

@app.route('/quiz', methods=['POST', 'GET'])
def quiz():

   if (not 'user_genre' in session) or session['q_asked'] == -1:   
      #load questions, taking answers at random
      questions = []

      #change this to change the number of questions
      for k in range(10):
         #pick an answer at random
         choices = query_db("SELECT * FROM movies WHERE Popularity > 30 ORDER BY RANDOM() LIMIT 2;")
         mov1 = choices[0][1]
         mov2 = choices[1][1]

         questions.append([mov1, mov2])

         if k == 0:
            #set reccomendation vectors to empty
            session['user_genre'] = [0]*len(format_mov(choices[0])[4])
            session['user_actors'] = [0]*len(format_mov(choices[0])[5])
            session['user_dir'] = [0] * len(format_mov(choices[0])[6])
            session['user_keys'] = [0] * len(format_mov(choices[0])[7])

      session['questions'] = questions
      print(questions)

      #set initial number of questions to 0
      session['q_asked'] = 0

   else:
      #update user's vector based on their responses
      answer = format_mov(query_db("SELECT * FROM movies WHERE title = \""+str(session['questions'][session['q_asked']][int(request.args['answer'])])+"\"")[0])
      answer_genres = answer[4]
      answer_actors = answer[5]
      answer_dir = answer[6]
      answer_keys = answer[7]
      for i in range(len(session['user_genre'])):
         session['user_genre'][i] = session['user_genre'][i] + answer_genres[i]
      for i in range(len(session['user_actors'])):
         session['user_actors'][i] = session['user_actors'][i] + answer_actors[i]
      for i in range(len(session['user_dir'])):
         session['user_dir'][i] = session['user_dir'][i] + answer_dir[i]
      for i in range(len(session['user_keys'])):
         session['user_keys'][i] = session['user_keys'][i] + answer_keys[i]

      #increment count of questions asked
      session['q_asked'] = session['q_asked'] + 1

   #if user has been asked enough questions, make reccomendation
   if session['q_asked'] >= len(session['questions']):
     
      #make reccomendation
      movies_raw = query_db("SELECT * FROM movies")

      movies = []
      for mov in movies_raw:
         movies.append(format_mov(mov))
      
      #algorithm for determining a movie's relevance to the user.
      def relevance(movie):
         genre_sim = 1 - spatial.distance.cosine(movie[4], session['user_genre'])
         if math.isnan(genre_sim):
            genre_sim = 0
         actor_sim = 1 - spatial.distance.cosine(movie[5], session['user_actors'])
         if math.isnan(actor_sim):
            actor_sim = 0
         dir_sim = 1 - spatial.distance.cosine(movie[6], session['user_dir'])
         if math.isnan(dir_sim):
            dir_sim = 0
         key_sim = 1 - spatial.distance.cosine(movie[7], session['user_keys'])
         if math.isnan(key_sim):
            key_sim = 0
         rel = (2 * genre_sim + actor_sim + dir_sim + key_sim) * (float(movie[1])**(1/float(11)))
         return rel
      
      movies.sort(reverse=True, key=relevance)
      recc_list = movies[0:18]

      #give user reccomendation
      return render_template('recc.html', recc_list = recc_list)

   #else give user new questions
   else:
      answer1=format_mov(query_db("SELECT * FROM movies WHERE title = \""+str(session['questions'][session['q_asked']][0]) + "\"")[0])
      answer2=format_mov(query_db("SELECT * FROM movies WHERE title = \""+str(session['questions'][session['q_asked']][1]) + "\"")[0])
      return render_template('quiz.html', answer1 = answer1, answer2 = answer2)

if __name__ == '__main__':
   app.run()