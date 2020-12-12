from flask import Flask, render_template, request, session
import pandas, random, math
from scipy import spatial


app = Flask(__name__)
app.secret_key="asdkjnah"

@app.route('/index')
@app.route('/')
def index():
   #reset data if user has some stored
   if 'q_asked' in session:
      session['q_asked'] = -1

   return render_template('index.html')

@app.route('/quiz', methods=['POST', 'GET'])
def quiz():

   genre_titles = ['Drama', 'Comedy', 'Thriller', 'Action', 'Romance', 'Adventure', 'Science Fiction', 'Horror', 'Family', 'Fantasy', 'Mystery', 'Animation', 'Music', 'War', 'Documentary', 'Western', 'Foreign']
   mood_titles = ['Quirky', 'Cerebral', 'Fast-Paced', 'Epic', 'Historical', 'Heartwarming', 'Creative', 'Independent', 'Tense','Realistic', 'Funny', 'New Release', 'Critically Acclaimed']

   if (not 'user_genre' in session) or session['q_asked'] == -1:
      
      #load questions, taking answers at random
      questions = []
      q_asked = []
      answers_df = pandas.read_csv('questions_db.csv')
      
      #change this to change the number of questions
      for k in range(4):
         #pick an answer at random
         answer_1 = random.randrange(0, len(answers_df))
         count = 0
         while answer_1 in q_asked and count < 100:
            answer_1 = random.randrange(0, len(answers_df))
            count+=1

         #pick second answer from same category at random
         answer_2 = -1
         while answer_2 < 0:
            choice = random.randrange(0, len(answers_df))
            if choice != answer_1 and answers_df['Category'][choice] == answers_df['Category'][answer_1]:
               answer_2 = choice
         
         q_asked.append(answer_1)
         q_asked.append(answer_2)

         #returns answers in format [Name, <genre_vec>, <mood_vec>]
         def format_answer(answer):
            genre_vec = [0]*len(genre_titles)
            mood_vec = [0]*len(mood_titles)
            for i in range(len(genre_titles)):
               genre_vec[i] = int(answers_df[genre_titles[i]][answer])
            for i in range(len(mood_titles)):
               mood_vec[i] = int(answers_df[mood_titles[i]][answer])
            return [answers_df['Name'][answer], genre_vec, mood_vec]

         questions.append([format_answer(answer_1), format_answer(answer_2)])
      session['questions'] = questions

      #set initial number of questions to 0
      session['q_asked'] = 0

      #set reccomendation vectors to empty
      session['user_genre'] = [0]*len(genre_titles)
      session['user_moods'] = [0]*len(mood_titles)

   if request.method == 'POST':
      #update user's vector based on their responses
      answer_genres = session['questions'][session['q_asked']][int(request.form['submit_btn'])][1]
      answer_moods = session['questions'][session['q_asked']][int(request.form['submit_btn'])][2]
      for i in range(len(session['user_genre'])):
         session['user_genre'][i] = session['user_genre'][i] + answer_genres[i]
      for i in range(len(session['user_moods'])):
         session['user_moods'][i] = session['user_moods'][i] + answer_moods[i]

      #increment count of questions asked
      session['q_asked'] = session['q_asked'] + 1

   #if user has been asked enough questions, make reccomendation
   if session['q_asked'] >= len(session['questions']):
      #make reccomendation
      movies_df = pandas.read_csv('movies_db.csv')

      #return movie represented as [Title, Popularity, <genre vec>, <mood vec>, Image Url, Overview]
      def format_movie(movie):
         genre_vec = [0]*len(genre_titles)
         mood_vec = [0]*len(mood_titles)
         for i in range(len(genre_titles)):
            genre_vec[i] = int(movies_df[genre_titles[i]][movie])
         for i in range(len(mood_titles)):
            mood_vec[i] = int(movies_df[mood_titles[i]][movie])
         image = "https://lh3.googleusercontent.com/proxy/p8Kz642g_nud-IC-r-YKeip7psx0mYbr7SWU2uuo4B9AJfsYhOn0ovWcL9ne53FiOXw8eQwzHwFXucPbAMHxu3wogkYpUPf1Et-XDcC8YG-EmIvlVgvh7tooLQkZJGcXIqnwxoKH6L7ln5PRNmWXTBgdWY7kd3udrTfneahCnoRdvNzdGW8a0DBVWGuOwFnjnUCJTIqV__oU9qzAhFMy5HBO58h7qdrB6p-jN65PKFLP1j-PexHqloL8VnWc5CAyAtDF0pTb44eeeOvf8xTxBj6a2Pkqz_XJhtg28VHbtDlbV7P4DTJqjfJcSHnh06wqSTmvlff_Ph4dojx9u7L2UAFfOeTlgZLGLJqgaQzUmUXPi4CTJA_9OfqBYnsbfn0S-Im0ghb9qa0CjrvegggYEpyzdZOH4ddiYwaeTui1jP1lHRWTBAgy16P-Y9y2emxJCQJbREvs4l6u9tKC3UY1nh9FRQPsiKUzr1zrxIIqaXHjtlMpPWoZ-0hr_DJFFpjqQP9i-fcs2HNtj7pZnHCbKur8QOuBdbnkwP1l3fPOLg9vkSMQ6uX5axveUtr-gWNFV_lbIBc"
         if movies_df['Poster_Image'][movie] != "NONE":
            image = movies_df['Poster_Image'][movie]
         return [movies_df['Title'][movie], int(movies_df['Popularity'][movie]), genre_vec, mood_vec, image, movies_df['Overview'][movie]]

      movies = []
      for i in range(len(movies_df)):
         movies.append(format_movie(i))
      
      #algorithm for determining a movie's relevance to the user.
      #takes movies as [Title, Popularity, <genre vec>, <mood vec>, Image, Overview] and user's genre and mood vecs
      def relevance(movie):
         genre_sim = 1 - spatial.distance.cosine(movie[2], session['user_genre'])
         mood_sim = 1 - spatial.distance.cosine(movie[3], session['user_moods'])
         return (2.3 * genre_sim + mood_sim) * (movie[1]**(1/float(11)))
      
      movies.sort(reverse=True, key=relevance)
      recc_list = movies[0:18]

      #give user reccomendation
      return render_template('recc.html', recc_list = recc_list)

   #else give user new questions
   else:
      answer1=session['questions'][session['q_asked']][0][0]
      answer2=session['questions'][session['q_asked']][1][0] 
      return render_template('quiz.html', answer1 = answer1, answer2 = answer2)

if __name__ == '__main__':
   app.run()