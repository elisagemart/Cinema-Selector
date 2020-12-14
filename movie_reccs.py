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

#makes the max of an array 1
def normalize(arr):
   big = max(arr)
   for i in range(len(arr)):
      arr[i] = arr[i] / big

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
      for k in range(2):
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
      
      #add an adjustment array to a movies vector at 10% strength
      def adjust(arr, adj):
         for i in range(len(arr)):
            arr[i] = arr[i] + 0.1*adj[i]
            
      #algorithm for determining a movie's relevance to the user.
      def relevance(movie):
         mov_genre = movie[4]
         mov_actor = movie[5]
         mov_dir = movie[6]
         mov_keys = movie[7]

         prev = query_db("SELECT * FROM user_reccs WHERE title = \"" + movie[0] + "\"")
         if len(prev) > 0:
            prev_score = prev[0]
            adjust(mov_genre, json.loads(prev_score[1]))
            adjust(mov_actor, json.loads(prev_score[2]))
            adjust(mov_dir, json.loads(prev_score[3]))
            adjust(mov_keys, json.loads(prev_score[4]))

         genre_sim = 1 - spatial.distance.cosine(mov_genre, session['user_genre'])
         if math.isnan(genre_sim):
            genre_sim = 0
         actor_sim = 1 - spatial.distance.cosine(mov_actor, session['user_actors'])
         if math.isnan(actor_sim):
            actor_sim = 0
         dir_sim = 1 - spatial.distance.cosine(mov_dir, session['user_dir'])
         if math.isnan(dir_sim):
            dir_sim = 0
         key_sim = 1 - spatial.distance.cosine(mov_keys, session['user_keys'])
         if math.isnan(key_sim):
            key_sim = 0
         rel = (2 * genre_sim + 0.6*actor_sim + dir_sim + key_sim) * (3 + float(movie[1])**(1/float(11)))
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

#code to update the user_recc db
@app.route('/update', methods=['POST', 'GET'])
def update():
   title = request.args['title']
   existing = query_db("SELECT * FROM user_reccs WHERE title =\"" + title + "\"")
   new_genre = [0]*len(session['user_genre'])
   new_actors = [0]*len(session['user_actors'])
   new_dir = [0]*len(session['user_dir'])
   new_keys = [0]*len(session['user_keys'])
   if len(existing) > 0:
      current = existing[0]
      for i in range(len(session['user_genre'])):
         new_genre[i] = (float(session['user_genre'][i])/float(current[5])) + current[1][i]
      normalize(new_genre)
      for i in range(len(session['user_actors'])):
         new_actors[i] = (float(session['user_actors'][i])/float(current[5])) + current[2][i]
      normalize(new_actors)
      for i in range(len(session['user_dir'])):
         new_dir[i] = (float(session['user_dir'][i])/float(current[5])) + current[3][i]
      normalize(new_dir)
      for i in range(len(session['user_keys'])):
         new_keys[i] = (float(session['user_keys'][i])/float(current[5])) + current[4][i]
      normalize(new_keys)
      query_db("UPDATE user_reccs SET Genre_Vector = \"" + str(new_genre) + "\", Actor_Vector = \"" + str(new_actors) + "\", Director_Vector = \"" + str(new_dir) + "\", Keyword_Vector = \"" + str(new_keys) + "\", Count = \"" + str(current[5] + 1) + "\" WHERE Title = \"" + title +"\" LIMIT 1")
      get_db().commit()
   else:
      for i in range(len(session['user_genre'])):
         new_genre[i] = session['user_genre'][i]
      normalize(new_genre)
      for i in range(len(session['user_actors'])):
         new_actors[i] = session['user_actors'][i]
      normalize(new_actors)
      for i in range(len(session['user_dir'])):
         new_dir[i] = session['user_dir'][i]
      normalize(new_dir)
      for i in range(len(session['user_keys'])):
         new_keys[i] = session['user_keys'][i]
      normalize(new_keys)
      query_db("INSERT INTO user_reccs (Title, Genre_Vector, Actor_Vector, Director_Vector, Keyword_Vector, Count) VALUES (\"" + title + "\", \"" + str(new_genre) + "\", \"" + str(new_actors) + "\", \"" + str(new_dir) + "\", \"" + str(new_keys) + "\", \"" + str(1) + "\")")
      get_db().commit()
   

   return '', 204

if __name__ == '__main__':
   app.run()