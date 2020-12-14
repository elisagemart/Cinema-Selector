# Cinema Selector

## Installation
Cinema Selector requires Python 3 and several packages to run correctly. To install the required packages, run:
`pip install Flask`
`pip install scipy`
`pip install sqlite3`

## Setup
To run the app on your device, run:
`Python movie_reccs.py`
The app will run at http://127.0.0.1:5000/

## What it Does
Cinema Selector offers users a series of choices between two movies. They pick the poster that looks more appealing. 

![quiz_screenshot](https://user-images.githubusercontent.com/10715620/102035583-49eb4700-3d86-11eb-8fe0-9119a3d1a72a.png)

After enough choices have been made, the program gives the user a list of recomendations.

![results_screenshot](https://user-images.githubusercontent.com/10715620/102035586-4bb50a80-3d86-11eb-9b7f-e086199da0b0.png)

Users have the option to mark a reccomendation as a "good reccomendation".

## How it Works

Raw data on 5,000 movies from taken from The Movie Database. This data included two tables. One gave data on the movie (including a list of topic keywords) and the other gave information on the cast. The tables were combined to assign each movie a vector representing its genres, actors, directors, and subject. We picked the 18 most common genres, 150 most common actors, 80 most common directors, and 300 most common topic keywords as dimensions. If a movie fit into a category, it had a 1 on that dimension of the appropriate vector. Else the dimensions were 0.

![movies](https://user-images.githubusercontent.com/10715620/102036526-aea7a100-3d88-11eb-8c4d-f55b88c071e5.PNG)

When a user selects a movie during the quiz, that movie's vectors are added to a user's preference vectors. After the quiz is complete, we sort the list of all movies according to the sum of cosign similarities between the genre, actor, director, and keyword vectors for the user and that movie. Each category is given a different weight, and the overall score is weighted by the popularity of the film. The highest scoring films are presented to the user.

The algorithm also incorporates a learning aspect. When the user marks a reccomendation as a good reccomendation, a second table called 'user_reccs' is updated, with the vectors stored there moving towards the overall user preference vectors of the user who marked it. The vectors in this table are used to weight the movie vectors in the previous step. Thus if a certain type of user consistently marks a movie as a good suggestion, that movie will appear more frequently for that type of user. In general, this system allows the app to recognize associations among movies that might not be obvious from their genre, cast, or keywords.

![user_reccs](https://user-images.githubusercontent.com/10715620/102036527-af403780-3d88-11eb-8b0c-e834d45101e2.PNG)

