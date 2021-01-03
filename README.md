# Cinema Selector

## Web App
To use a live version of the web app, visit http://cinemaselector.pythonanywhere.com/

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
Cinema Selector is intended to solve the dilemma of finding a movie to watch. The app is built on the premise that people often know what they are in the mood for but have a hard time articulating it enough to search directly for something to watch. Instead of a paralyzing searchbar, Cinema Selector offers users a series of choices between two movies. They pick the poster that looks more appealing. 

![quiz_screenshot](https://user-images.githubusercontent.com/10715620/103488188-2e48ee80-4dd0-11eb-86e3-5d60e8590be2.png)

After enough choices have been made, the program gives the user a list of recomendations.

![results_screenshot](https://user-images.githubusercontent.com/10715620/103488189-2f7a1b80-4dd0-11eb-8da5-0abf283fc69f.PNG)

Users have the option to mark a reccomendation as a "good reccomendation".

## How it Works

Raw data on 9,000 movies was from taken from The Movie Database. This raw data was processed to assign each movie vectors representing its genres, actors, directors, subjects, and production companies. The dimensions of the vectors represent the 17 most popular genres, 200 most popular actors, 100 most popular directors, 400 most popular subject keywords, and 100 most popular production companies. Therefore each movie is represented by 817 data points in total.

![movies](https://user-images.githubusercontent.com/10715620/103488186-2e48ee80-4dd0-11eb-825c-ad77efdb4ad7.PNG)

When a user selects a movie during the quiz, that movie's vectors are added to a user's preference vectors. After the quiz is complete, we sort the list of all movies according to the sum of cosign similarities between the genre, actor, director, keyword, and company vectors for the user and that movie. Each category is given a different weight, and the overall score is weighted by the popularity of the film. The highest scoring films are presented to the user.

The algorithm also incorporates a learning aspect. When the user marks a recomendation as a good recomendation, a second table called 'user_recs' is updated, with the vectors stored there moving towards the overall user preference vectors of the user who marked it. The vectors in this table are used to weight the movie vectors in the previous step. Thus if a certain type of user consistently marks a movie as a good suggestion, that movie will appear more frequently for that type of user. In general, this system allows the app to recognize associations among movies that might not be obvious from their raw data.

![user_recs](https://user-images.githubusercontent.com/10715620/103488191-30ab4880-4dd0-11eb-891e-a37cb7e95f0c.PNG)

## Credits
Web app design by Eli Sage-Martinson, Saijel Verma, and Nikhil Patel.

Home Page design based on the Greyscale Template by Start Bootstrap, licensed under [MIT](https://github.com/StartBootstrap/startbootstrap-grayscale/blob/master/LICENSE).
