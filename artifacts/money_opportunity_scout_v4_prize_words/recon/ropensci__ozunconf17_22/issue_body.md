[kaggle](https://www.kaggle.com/competitions) is a company that runs predictive modelling competitions on behalf of organisations. Competitors are given a dataset with covariates and response variables which they can use to train a model; they then use the model to make predictions for a new dataset (for which they only have the predictors, not the response variables) and submit these predictions to a web platform. The web platform compares the predictions with the withheld data and posts a score on a [leaderboard](https://www.kaggle.com/c/dog-breed-identification/leaderboard). At the end of the competition, the winner gets a prize and the organisation gets the model and code to produce it. It's pretty cool.

Predictive modelling competitions are also really useful to organisations and research communities that don't have the funds to use Kaggle or [similar commercial platforms](https://stats.stackexchange.com/questions/11142/sites-for-predictive-modeling-competitions), e.g. for resolving disputes about methodology (something I want to do with [zoon](https://ropensci.org/blog/blog/2016/12/12/ropensci-fellowship-zoon)), or for education (I have run something similar in an undergrad practical session). An R package that makes it easy to set up simple, free, self-hosted competitions like this could be really handy.

The main technical requirement is setting up a server (just an r session running on a web-connected computer) to host the hidden validation dataset, calculate the evaluation scores for each new submission, and serve a leaderboard on the web. The package could use [plumber](https://github.com/trestletech/plumber) (or [jug](http://bart6114.github.io/jug/index.html) or [OpenCPU](https://www.opencpu.org/) or something) to create the API for submission, create a shiny app for the leaderboard and to host the training data to download, and provide users with streamlined functions to submit predictions.

So the organiser might do something like:
```r
run_competition(title = "predict the weights of these guinea pigs",
                description = "build a model that predicts the weights of these loveable balls of
                               fluff from some metadata about them",
                training_data = "train_guinea_pig_features_weights.Rdata",
                test_data = "test_guinea_pig_features.rds"
                secret_test_labels = "test_guinea_pig_weights.csv",
                metric = "RMSE")
```
```
Your competition and leaderboard is live and hosted at:
  http://128.250.4.119/8000
```

Competitors could also use the package to submit their predictions to the leaderboard:
```r
submit_prediction(predicted_weights,
                  website = "http://128.250.4.119/8000",
                  user = "nick",
                  password = "averysecurepassword1")
```