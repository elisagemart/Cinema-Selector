from flask import Flask, render_template, request, session, g
import math, json
from scipy import spatial
import sqlite3
import os
import timeit

app = Flask(__name__)
app.secret_key="asdkjnah213iuhewr"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "Movies.db")

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

#rearrages list so it is in 3-column format
def rearrange(lst):
   if len(lst) % 3 != 0:
      return lst
   res = [0]*len(lst)
   num = int(len(lst) / 3)
   for i in range(len(lst)-1):
      res[(i*num) % (len(lst) - 1)] = lst[i]
   res[len(lst)-1] = lst[len(lst)-1]
   return res

#returns movies in format [Title, Pop, Overview, Poster, <genre_vec>, <actor_vec>, <dir_vec>, <key_vec>, <company_vector>, Providers]
def format_mov(mov):
   return [mov[1], mov[2], mov[4], mov[5], json.loads(mov[6]), json.loads(mov[7]), json.loads(mov[8]), json.loads(mov[9]), json.loads(mov[10]), json.loads(mov[11])]

#makes the max of an array 1
def normalize(arr):
   big = max(arr)
   if big > 0:
      for i in range(len(arr)):
         arr[i] = arr[i] / big

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
   mov_companies = movie[8]

   prev = query_db("SELECT * FROM user_recs WHERE Title = \"" + movie[0] + "\"")
   if len(prev) > 0:
      prev_score = prev[0]
      adjust(mov_genre, json.loads(prev_score[1]))
      adjust(mov_actor, json.loads(prev_score[2]))
      adjust(mov_dir, json.loads(prev_score[3]))
      adjust(mov_keys, json.loads(prev_score[4]))
      adjust(mov_companies, json.loads(prev_score[5]))

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
   com_sim = 1 - spatial.distance.cosine(mov_companies, session['user_companies'])
   if math.isnan(com_sim):
      com_sim = 0
   rel = (2 * genre_sim + 0.6*actor_sim + dir_sim + key_sim + (0.2 *com_sim)) * (5 + float(movie[1])**(1/float(11)))
   return rel

@app.route('/index')
@app.route('/')
def index():
   #reset data if user has some stored
   if 'q_asked' in session:
      session['q_asked'] = -1
   
   return render_template('index.html')

@app.route('/start')
def start():
   return render_template('genre_pref.html')

@app.route('/quiz', methods=['POST', 'GET'])
def quiz():

   #list of how many options we pull questions from at each stage
   q_options = [2,2,2,2,2,2,2,2,20,20,20,20,22,22,24,24,26,26,28,30,32]

   #if we haven't asked any questions yet, load the initial data
   if (not 'user_genre' in session) or session['q_asked'] == -1:

      #load initial user vectors, based on sample data from db
      sample = query_db("SELECT * FROM movies LIMIT 1")
      session['user_genre'] = [0]*len(format_mov(sample[0])[4])
      session['user_actors'] = [0]*len(format_mov(sample[0])[5])
      session['user_dir'] = [0] * len(format_mov(sample[0])[6])
      session['user_keys'] = [0] * len(format_mov(sample[0])[7])
      session['user_companies'] = [0] * len(format_mov(sample[0])[8])

      #initialize number of questions
      session['q_asked'] = 8

      #update user's initial genre vector
      if request.args['answer'] == 'action':
         session['user_genre'][3] = 3
      elif request.args['answer'] == 'comedy':
         session['user_genre'][1] = 3
      elif request.args['answer'] == 'drama':
         session['user_genre'][0] = 3
      elif request.args['answer'] == 'horror':
         session['user_genre'][7] = 3
      elif request.args['answer'] == 'romance':
         session['user_genre'][4] = 3
         session['user_genre'][8] = -3
      elif request.args['answer'] == 'family':
         session['user_genre'][8] = 3
      else:
         session['q_asked'] = 0

   #otherwise, update based on the question they just answered
   else:
      #update user's vector based on their responses
      answer = int(request.args['answer'])
      non_answer = (1 + answer) % 2
      answer = session['question'][answer]
      non_answer = session['question'][non_answer]
      DF = 0.1
      for i in range(len(session['user_genre'])):
         session['user_genre'][i] = session['user_genre'][i] + answer[4][i]
         session['user_genre'][i] = session['user_genre'][i] - (DF * non_answer[4][i])
      for i in range(len(session['user_actors'])):
         session['user_actors'][i] = session['user_actors'][i] + answer[5][i]
         session['user_actors'][i] = session['user_actors'][i] - (DF * non_answer[5][i])
      for i in range(len(session['user_dir'])):
         session['user_dir'][i] = session['user_dir'][i] + answer[6][i]
         session['user_dir'][i] = session['user_dir'][i] - (DF * non_answer[6][i])
      for i in range(len(session['user_keys'])):
         session['user_keys'][i] = session['user_keys'][i] + answer[7][i]
         session['user_keys'][i] = session['user_keys'][i] - (DF * non_answer[7][i])
      for i in range(len(session['user_companies'])):
         session['user_companies'][i] = session['user_companies'][i] + answer[8][i]
         session['user_companies'][i] = session['user_companies'][i] - (DF * non_answer[8][i])

      #increment count of questions asked
      session['q_asked'] = session['q_asked'] + 1

   #if user has been asked enough questions, make reccomendation
   if session['q_asked'] >= len(q_options):
     
      #make reccomendation
      movies_raw = query_db("SELECT * FROM movies")

      movies = []
      for mov in movies_raw:
         movies.append(format_mov(mov))

      movies.sort(reverse=True, key=relevance)
      recc_list = movies[0:21]

      #give user reccomendation
      return render_template('recc.html', recc_list = rearrange(recc_list))

   #else give user new questions
   else:
      #get set of choices; more options for later questions
      choices_raw = query_db("SELECT * FROM movies WHERE Popularity > 20 ORDER BY RANDOM() LIMIT " + str(q_options[session['q_asked']]) + ";")
      choices = []
      for mov in choices_raw:
         choices.append(format_mov(mov))

      #sort based on computed relevance
      choices.sort(reverse=True, key=relevance)

      answer1=choices[0]
      answer2=choices[1]
      session['question'] = [answer1, answer2]
      return render_template('quiz.html', answer1 = answer1, answer2 = answer2)

@app.route('/filter', methods=['POST', 'GET'])
def filter():
   providers = request.form.getlist('provider')
   #make reccomendation again, using only movies from selected providers
   movies_raw = query_db("SELECT * FROM movies")
   movies = []
   for mov in movies_raw:
      fmov = format_mov(mov)
      #if filters blank, return all movies
      if not providers:
            movies.append(fmov)
      else:
         for prov in fmov[9]:
            if prov['provider_name'] in providers:
               movies.append(fmov)
               break
      
   movies.sort(reverse=True, key=relevance)
   recc_list = movies[0:21]

   return render_template('recc.html', recc_list = rearrange(recc_list))

#code to update the user_recc db
@app.route('/update', methods=['POST', 'GET'])
def update():
   title = request.args['title']
   existing = query_db("SELECT * FROM user_recs WHERE title =\"" + title + "\"")
   new_genre = [0]*len(session['user_genre'])
   new_actors = [0]*len(session['user_actors'])
   new_dir = [0]*len(session['user_dir'])
   new_keys = [0]*len(session['user_keys'])
   new_companies = [0]*len(session['user_companies'])
   if len(existing) > 0:
      current = existing[0]
      for i in range(len(session['user_genre'])):
         new_genre[i] = (float(session['user_genre'][i])/float(current[6])) + json.loads(current[1])[i]
      normalize(new_genre)
      for i in range(len(session['user_actors'])):
         new_actors[i] = (float(session['user_actors'][i])/float(current[6])) + json.loads(current[2])[i]
      normalize(new_actors)
      for i in range(len(session['user_dir'])):
         new_dir[i] = (float(session['user_dir'][i])/float(current[6])) + json.loads(current[3])[i]
      normalize(new_dir)
      for i in range(len(session['user_keys'])):
         new_keys[i] = (float(session['user_keys'][i])/float(current[6])) + json.loads(current[4])[i]
      normalize(new_keys)
      for i in range(len(session['user_companies'])):
         new_companies[i] = (float(session['user_companies'][i])/float(current[6])) + json.loads(current[5])[i]
      normalize(new_companies)
      query_db("UPDATE user_recs SET Genre_Vector = \"" + str(new_genre) + "\", Actor_Vector = \"" + str(new_actors) + "\", Director_Vector = \"" + str(new_dir) + "\", Keyword_Vector = \"" + str(new_keys) + "\", Company_Vector = \"" + str(new_companies) + "\", Count = \"" + str(current[6] + 1) + "\" WHERE Title = \"" + str(title) +"\"")
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
      for i in range(len(session['user_companies'])):
         new_companies[i] = session['user_companies'][i]
      normalize(new_companies)
      query_db("INSERT INTO user_recs (Title, Genre_Vector, Actor_Vector, Director_Vector, Keyword_Vector, Company_Vector, Count) VALUES (\"" + title + "\", \"" + str(new_genre) + "\", \"" + str(new_actors) + "\", \"" + str(new_dir) + "\", \"" + str(new_keys) + "\", \"" + str(new_companies) + "\", \"" + str(1) + "\")")
      get_db().commit()
   

   return '', 204

if __name__ == '__main__':
   app.run()