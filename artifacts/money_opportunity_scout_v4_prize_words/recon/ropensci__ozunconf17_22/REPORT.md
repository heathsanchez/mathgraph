# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/ropensci/ozunconf17/issues/22",
    "title": "predictive modelling competitions",
    "state": "OPEN",
    "labels": [
      "education",
      "crackerjack"
    ],
    "comment_count": 4,
    "updatedAt": "2017-10-23T05:03:25Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/ropensci__ozunconf17_22

README head:
# [rOpenSci 2017 ozunconference](http://ozunconf17.ropensci.org/)
__(invitation only), Oct 26 - 27, 2017. Melbourne__

![](static/img/melb-logo.png)

Welcome to the repository for the 2017 ozunconf.  rOpenSci will be hosting its fourth major developer meeting and open science hackathon this time in Melbourne, Australia.

* [Participants](http://ozunconf17.ropensci.org/#team)
* Please post ideas for projects, discussion topics, and sessions as [issues](https://github.com/ropensci/ozunconf17/issues/) and move to the wiki and/or a new repo within rOpenSci's account as needed.

Event hashtag is `#rozunconf17`

## Code of conduct

To ensure a safe, enjoyable, and friendly experience for everyone who participates, we have a [code of conduct](http://ozunconf17.ropensci.org/coc).  This applies to people attending in person or remotely, and for interacting over the [issues](https://github.com/ropensci/ozunconf17/issues/).

## Support
This meeting is made possible by generous support from:

- rOpenSci
- RStudio

Makefile targets:
3:all: serve
5:serve:
8:build:
11:clean:


## Issue body

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

## Comments

## goldingn — 2017-10-18T00:58:42Z

I'm imagining users would be registered manually, since setting up a safe and secure automatic registration system would be a whole other can of worms. 
---
## dicook — 2017-10-20T03:32:46Z

Yihui wrote me a little system almost 10 years ago, before kaggle in class was available. it worked beautifully in the class. I don't know that I could find the code again. I think the difficult thing was that it was difficult to hide the true solution, so anyone with a bit of hacking skill could cheat. It seems possible with a shiny app, and doesn't seem too difficult to code. 
---
## goldingn — 2017-10-20T03:41:32Z

Oh cool, that code would be helpful!

Yeah, I thought about ways of doing this without a web service. The only other option I can think of (that would effectively hide the data) is distributing compiled code. And that doesn't sound like a good idea! 
---
## dicook — 2017-10-20T03:54:20Z

I think the simplest is to compare predictions with the true values, using one of a collection of metrics provided. But you'd want to be able to split the test data into a public and private, so that only the performance on public sample is reported until the end of a competition.

## Inventory excerpt

top files
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-0630fbe2dae6cfe59a87210eeded00e8559e54aa.idx
.git/objects/pack/pack-0630fbe2dae6cfe59a87210eeded00e8559e54aa.pack
.git/objects/pack/pack-0630fbe2dae6cfe59a87210eeded00e8559e54aa.promisor
.git/objects/pack/pack-fd83dc49746f47127c7b425dd984521a1f22e711.idx
.git/objects/pack/pack-fd83dc49746f47127c7b425dd984521a1f22e711.pack
.git/objects/pack/pack-fd83dc49746f47127c7b425dd984521a1f22e711.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/master
.gitignore
.jpg
config.toml
content/.gitkeep
content/apply.md
content/apply/index.html
content/coc.md
content/projects.md
content/terms.md
content/yay.md
content/yay/index.html
docs/.gitkeep
docs/404.html
docs/apply/index.html
docs/apply/index.xml
docs/categories/index.xml
docs/categories/r/index.xml
docs/CNAME
docs/coc/index.html
docs/css/agency.css
docs/css/bootstrap-v3.3.7/bootstrap.css
docs/css/bootstrap-v3.3.7/bootstrap.min.css
docs/css/jquery.form-validator-v2.3.44/theme-default.css
docs/css/jquery.form-validator-v2.3.44/theme-default.min.css
docs/css/ropensci.css
docs/favicon.ico
docs/font-awesome-v4.7.0/css/font-awesome.css
docs/font-awesome-v4.7.0/css/font-awesome.min.css
docs/font-awesome-v4.7.0/fonts/fontawesome-webfont.eot
docs/font-awesome-v4.7.0/fonts/fontawesome-webfont.svg
docs/font-awesome-v4.7.0/fonts/fontawesome-webfont.ttf
docs/font-awesome-v4.7.0/fonts/fontawesome-webfont.woff
docs/font-awesome-v4.7.0/fonts/fontawesome-webfont.woff2
docs/font-awesome-v4.7.0/fonts/FontAwesome.otf
docs/fonts/bootstrap-v3.3.7/glyphicons-halflings-regular.eot
docs/fonts/bootstrap-v3.3.7/glyphicons-halflings-regular.svg
docs/fonts/bootstrap-v3.3.7/glyphicons-halflings-regular.ttf
docs/fonts/bootstrap-v3.3.7/glyphicons-halflings-regular.woff
docs/fonts/bootstrap-v3.3.7/glyphicons-halflings-regular.woff2
docs/img/404/404.jpg
docs/img/about/1.jpg
docs/img/about/2.jpg
docs/img/about/3.jpg
docs/img/about/4.jpg
docs/img/banner.svg
docs/img/cd-top-arrow.svg
docs/img/favicon.ico
docs/img/header.jpg
docs/img/logos/themeforest.jpg
docs/img/logos/wordpress.jpg
docs/img/map-image.png
docs/img/melb-logo.png
docs/img/melb-logo.svg
docs/img/ropensci_small.png
docs/img/sponsors/airbnb_horizontal_lockup_web.jpg
docs/img/sponsors/data_camp.png
docs/img/sponsors/googlelogo_color_272x92dp.png
docs/img/sponsors/ingham-inst.png
docs/img/sponsors/Microsoft-logo_rgb_c-gray.png
docs/img/sponsors/monash-business-school.jpg
docs/img/sponsors/RConsortium.png
docs/img/sponsors/ropensci-lettering-colour.png
docs/img/sponsors/rstudio-logo.png
docs/img/sponsors/sloan.png
docs/img/team/1.jpg
docs/img/team/2.jpg
docs/img/team/3.jpg
docs/img/team/adam-gruer.jpg
docs/img/team/alicia-allan.jpg
docs/img/team/aniko-toth.jpg
docs/img/team/anna-quaglieri.jpg
docs/img/team/charles-gray.jpg
docs/img/team/damjan-vukcevic.jpeg
docs/img/team/damjan-vukcevic.jpg
docs/img/team/daniel-falster.jpg
docs/img/team/di-cook.jpg
docs/img/team/diego-barneche.jpg
docs/img/team/earo-wang.jpg
docs/img/team/elle-saber.jpg
docs/img/team/elle.jpg
docs/img/team/grahame-grieve.jpg
docs/img/team/holly-kirk.jpg
docs/img/team/hugh-parsonage.jpg
docs/img/team/jacinta-holloway.jpg
docs/img/team/jackson-kwok.jpg
docs/img/team/jeff-hanson.jpg
docs/img/team/jessie-roberts.jpg
docs/img/team/jono-carroll.jpg
docs/img/team/justin-carmody.jpg
docs/img/team/kate-saunders.png
docs/img/team/kim-fitter.jpg
docs/img/team/liz-martin.jpg
docs/img/team/madeline-davey.jpg
docs/img/team/mathew-ling.jpg
docs/img/team/michael-sumner.jpg
docs/img/team/michael-sumner.png
docs/img/team/miles-mcbain.jpg
docs/img/team/mitch-ohara-wild.jpg
docs/img/team/natasha-cadenhead.jpg
docs/img/team/nicholas-tierney.jpg
docs/img/team/nick-golding.jpg
docs/img/team/nikeisha-caruana.jpg
docs/img/team/peter-ellis.jpg
docs/img/team/peter-hickey.jpg
docs/img/team/richard-beare.JPG
docs/img/team/rob-hyndman.png
docs/img/team/roger-peng.jpg
docs/img/team/roger-peng.png
docs/img/team/ross-gayler.jpg
docs/img/team/samithree-rajapaksha.jpg
docs/img/team/saras-mei-windecker.jpg
docs/img/team/stefan-milton-bache.jpg
docs/img/team/steph-de-silva.png
docs/img/team/steve-bennett.jpg
docs/img/team/tim-churches.jpg
docs/img/team/tim-hyndman.png
docs/img/team/yan-holtz.jpg
docs/img/venue.jpg
docs/index.html
docs/index.xml
docs/js/agency.js
docs/js/bootstrap-v3.3.7/bootstrap.js
docs/js/bootstrap-v3.3.7/bootstrap.min.js
docs/js/jquery-v3.3.1/jquery.js
docs/js/jquery-v3.3.1/jquery.min.js
docs/js/jquery.form-validator-v2.3.44/html5.js
docs/js/jquery.form-validator-v2.3.44/jquery.form-validator.js
docs/js/jquery.form-validator-v2.3.44/jquery.form-validator.min.js
docs/js/jquery.form-validator-v2.3.44/security.js
docs/js/jquery.form-validator-v2.3.44/toggleDisabled.js
docs/js/ropensci.js
docs/post/index.xml
docs/projects/index.html
docs/sitemap.xml
docs/tags/index.xml
docs/tags/plot/index.xml
docs/tags/r-markdown/index.xml
docs/tags/regression/index.xml
docs/terms/index.html
docs/yay/index.html
docs/yay/index.xml
index.Rmd
Makefile
ozunconf17.Rproj
README.md
static/.gitkeep
static/favicon.ico
static/img/banner.svg
static/img/cd-top-arrow.svg
static/img/favicon.ico
static/img/header.jpg
static/img/melb-logo.png
static/img/melb-logo.svg
static/img/ropensci_small.png
static/img/sponsors/airbnb_horizontal_lockup_web.jpg
static/img/sponsors/data_camp.png
static/img/sponsors/googlelogo_color_272x92dp.png
static/img/sponsors/ingham-inst.png
static/img/sponsors/Microsoft-logo_rgb_c-gray.png
static/img/sponsors/monash-business-school.jpg
static/img/sponsors/RConsortium.png
static/img/sponsors/ropensci-lettering-colour.png
static/img/sponsors/rstudio-logo.png
static/img/sponsors/sloan.png
static/img/team/adam-gruer.jpg
static/img/team/alicia-allan.jpg
static/img/team/aniko-toth.jpg
static/img/team/anna-quaglieri.jpg
static/img/team/charles-gray.jpg
static/img/team/damjan-vukcevic.jpg
static/img/team/daniel-falster.jpg
static/img/team/di-cook.jpg
static/img/team/diego-barneche.jpg
static/img/team/earo-wang.jpg
static/img/team/elle-saber.jpg
static/img/team/grahame-grieve.jpg
static/img/team/holly-kirk.jpg
static/img/team/hugh-parsonage.jpg
static/img/team/jacinta-holloway.jpg
static/img/team/jackson-kwok.jpg
static/img/team/jeff-hanson.jpg
static/img/team/jessie-roberts.jpg
static/img/team/jono-carroll.jpg
static/img/team/justin-carmody.jpg
static/img/team/kate-saunders.png
static/img/team/kim-fitter.jpg
static/img/team/liz-martin.jpg
static/img/team/madeline-davey.jpg
static/img/team/mathew-ling.jpg
static/img/team/michael-sumner.jpg
static/img/team/michael-sumner.png
static/img/team/miles-mcbain.jpg
static/img/team/mitch-ohara-wild.jpg
static/img/team/natasha-cadenhead.jpg
static/img/team/nicholas-tierney.jpg
static/img/team/nick-golding.jpg
static/img/team/nikeisha-caruana.jpg
static/img/team/peter-ellis.jpg
static/img/team/peter-hickey.jpg
static/img/team/richard-beare.jpg
static/img/team/rob-hyndman.png
static/img/team/roger-peng.jpg
static/img/team/ross-gayler.jpg
static/img/team/samithree-rajapaksha.jpg
static/img/team/saras-mei-windecker.jpg
static/img/team/stefan-milton-bache.jpg
static/img/team/steph-de-silva.png
static/img/team/steve-bennett.jpg
static/img/team/tim-churches.jpg
static/img/team/tim-hyndman.png
static/img/team/yan-holtz.jpg
static/img/venue.jpg
themes/hugo-ropensci-theme/archetypes/default.md
themes/hugo-ropensci-theme/CHANGELOG.md
themes/hugo-ropensci-theme/exampleSite/.gitignore
themes/hugo-ropensci-theme/exampleSite/config.toml
themes/hugo-ropensci-theme/layouts/404.html
themes/hugo-ropensci-theme/layouts/index.html
themes/hugo-ropensci-theme/LICENSE
themes/hugo-ropensci-theme/README.md
themes/hugo-ropensci-theme/static/favicon.ico
themes/hugo-ropensci-theme/theme.toml

build/test/competition files
./content/apply.md
./content/coc.md
./content/projects.md
./content/terms.md
./content/yay.md
./Makefile
./README.md
./themes/hugo-ropensci-theme/archetypes/default.md
./themes/hugo-ropensci-theme/CHANGELOG.md
./themes/hugo-ropensci-theme/README.md

workflows


## Grep excerpt

===== issue body =====
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
===== money/competition/judge hits =====
./content/apply/index.html:6:  <title>rOpenSci ozunconf 2017 nominations</title>
./content/yay/index.html:6:  <title>rOpenSci ozunconf 2017 info</title>
./content/coc.md:1:# rOpenSci code of conduct
./content/coc.md:3:The organisers of the Melbourne rOpenSci Unconference are committed to providing a welcoming and harassment-free experience for everyone, regardless of gender, gender identity and expression, age, sexual orientation, disability, physical appearance, body size, race, ethnicity, religion (or lack thereof), or technology choices. We do not tolerate harassment of conference participants in any form. Sexual language and imagery is not appropriate for any conference venue, including talks, workshops, parties, Twitter and other online media. Unconf participants violating these rules may be sanctioned or expelled from the event at the discretion of the conference organizers.
./content/coc.md:5:This code of conduct applies to all participants, including organisers and applies to all modes of interaction, both in-person and online, including Unconf GitHub project repos and rOpenSci GitHub, the rOpenSci discussion forum, Slack channels and Twitter.
./content/coc.md:7:rOpenSci unconf participants agree to:
./content/coc.md:17:If any attendee engages in harassing behavior, the conference organizers may take any lawful action we deem appropriate, including but not limited to warning the offender or asking the offender to leave the conference. (If you feel you have been unfairly accused of violating this code of conduct, you should contact the conference team with a concise description of your grievance.)
./content/coc.md:19:We welcome your [feedback](http://ropensci.org/contact.html) on this and every other aspect of rOpenSci's events, and we thank you for working with us to make it a safe, enjoyable, and friendly experience for everyone who participates.
./content/projects.md:1:# R OpenSci ozunconference 2017 Projects
./content/projects.md:3:### 🇦🇺 🏈 [AFLW - AFL Data](https://github.com/ropenscilabs/aflinfo)
./content/projects.md:5:### 🇦🇺 👩 🏈 [AFLW - AFL Womens Data](https://github.com/ropenscilabs/ozwomensport/tree/master/AFLW)
./content/projects.md:7:### 🏏 [cricinfo - access cricket data from cricinfo ](https://github.com/ropenscilabs/cricinfo)
./content/projects.md:9:### 🏠 [datagovau - R package to download data catalogued at data.gov.au](https://github.com/ropenscilabs/datagovau)
./content/projects.md:11:### 🚀 [icon - easily insert web icons](https://github.com/ropenscilabs/icon)
./content/projects.md:13:### 🇦🇺 🎨 [ochRe - Australia-themed Colour Palettes](https://github.com/ropenscilabs/ochRe)
./content/projects.md:15:### 🛩 [ozflights - pull Aviation data from BITRE ](https://github.com/ropenscilabs/ozflights)
./content/projects.md:17:### 🛣 [ozroaddeaths - Pull data from the Australian Road Deaths Database](https://github.com/ropenscilabs/ozroaddeaths)
./content/projects.md:19:### 〰️ [realtime - Plot real time events](https://github.com/ropenscilabs/realtime)
./content/projects.md:21:### 🔥 [ronfhir - makes data available in R from servers that follow the FHIR format](https://github.com/ropenscilabs/ronfhir)
./content/projects.md:23:### 🕙️ [stow - simple version control in R](https://github.com/ropenscilabs/ozrepro)
./content/projects.md:25:### 〽️ [styles - themes for base plots](https://github.com/ropenscilabs/styles)
./content/projects.md:27:### 🚋 [tRainspotting - gtfs-r feeds from R, with leaflet maps](https://github.com/ropenscilabs/tRainspotting)
./content/projects.md:32:[fork](https://github.com/ropenscilabs/ozunconf-projects) 
./content/terms.md:1:# rOpenSci unconf terms and conditions
./content/terms.md:3:These terms and conditions apply to the rOpenSci Unconference 2017 (“Event”) hosted by and on behalf of The rOpenSci project, a fiscally sponsored project of Numfocus Inc, a non-profit registered in Texas (P.O. Box 90596 Austin, TX 78709 USA). The purpose of the Event is to encourage development of open source tools and grow a community of open source developers and mentors around the R programming language. It is a condition of participation that these terms and conditions are accepted by the Participant prior to the Event. Upon acceptance these terms and conditions form a binding legal agreement between rOpenSci and the Participant. Please read them carefully.
./content/terms.md:5:rOpenSci unconf participants agree to:
./content/terms.md:7:  * Participants attending the Event maintain ownership rights over their work. Participants grant the rOpenSci project non-exclusive access to use the work and/or likeness.
./content/terms.md:8:  * By attending the Event, participants also acknowledge and agree to the [Code of Conduct](/coc)
./docs/apply/index.html:6:  <title>rOpenSci ozunconf 2017 nominations</title>
./docs/apply/index.xml:4:    <title>Applies on rOpenSci OzUnconference</title>
./docs/apply/index.xml:6:    <description>Recent content in Applies on rOpenSci OzUnconference</description>
./docs/apply/index.xml:19:      <description>  rOpenSci ozunconf 2017 nominations html{ margin: 0; height: 100%; overflow: hidden; } iframe{ position: absolute; left:0; right:0; bottom:0; top:0; border:0; }        </description>
./docs/index.html:9:  <meta name="author" content="rOpenSci OzUnconference">
./docs/index.html:11:  <title>rOpenSci OzUnconference</title>
./docs/index.html:14:  <link href="/css/ropensci.css" rel="stylesheet">
./docs/index.html:55:          <img src="/img/ropensci_small.png" class="img-responsive" alt="rOpenSci">
./docs/index.html:117:      <div class="intro-lead-in">rOpenSci OzUnconf</div>
./docs/index.html:132:        <h3 class="section-subheading text-muted"><p>For a second year running, we are excited to announce another <a href="http://ropensci.org/">rOpenSci</a> OzUnconference in 2017 held in Melbourne, Australia. We&rsquo;re organizing this event to bring together scientists, developers, and open data enthusiasts from academia, industry, government, and non-profit to get together for a few days and hack on various projects. Past projects have related to open data, data visualization, data publication and open science using R. To ensure a safe, enjoyable, and friendly experience for everyone who participates, we have a strict <a href="/coc">code of conduct</a> and <a href="/terms">terms and conditions</a>.</p>
./docs/index.html:134:<p>All OzUnconference ideas will begin as GitHub issues on the <a href="https://github.com/ropensci/ozunconf17/issues/">OzUnconf repo</a> in the weeks before the event. However, the actual schedule will not be decided until the morning of the 26th. You can see some of the <a href="https://github.com/ropensci/auunconf/issues">projects proposed</a> for last year&rsquo;s event in Australia, and the <a href="https://github.com/ropensci/unconf17/issues">projects proposed</a> at the unconf in LA earlier this year.</p>
./docs/index.html:149:        <h2 class="section-heading">Participants</h2>
./docs/index.html:150:        <h3 class="section-subheading text-mutedwith ">We are assembling an exciting team of developers and enthusiastic users representing academia, industry, government, and various open source projects.</h3>
./docs/index.html:159:            <img src="/img/team/nicholas-tierney.jpg" class="img-responsive img-circle" alt="Nicholas Tierney" height=150 width=150>
./docs/index.html:172:            <ul class="list-inline social-buttons">
./docs/index.html:190:            <img src="/img/team/di-cook.jpg" class="img-responsive img-circle" alt="Di Cook" height=150 width=150>
./docs/index.html:203:            <ul class="list-inline social-buttons">
./docs/index.html:221:            <img src="/img/team/rob-hyndman.png" class="img-responsive img-circle" alt="Rob Hyndman" height=150 width=150>
./docs/index.html:234:            <ul class="list-inline social-buttons">
./docs/index.html:252:            <img src="/img/team/miles-mcbain.jpg" class="img-responsive img-circle" alt="Miles McBain" height=150 width=150>
./docs/index.html:265:            <ul class="list-inline social-buttons">
./docs/index.html:283:            <img src="/img/team/roger-peng.png" class="img-responsive img-circle" alt="Roger Peng" height=150 width=150>
./docs/index.html:296:            <ul class="list-inline social-buttons">
./docs/index.html:314:            <img src="/img/team/jessie-roberts.jpg" class="img-responsive img-circle" alt="Jessie Roberts" height=150 width=150>
./docs/index.html:327:            <ul class="list-inline social-buttons">
./docs/index.html:345:            <img src="/img/team/earo-wang.jpg" class="img-responsive img-circle" alt="Earo Wang" height=150 width=150>
./docs/index.html:358:            <ul class="list-inline social-buttons">
./docs/index.html:376:            <img src="/img/team/charles-gray.jpg" class="img-responsive img-circle" alt="Charles Gray" height=150 width=150>
./docs/index.html:389:            <ul class="list-inline social-buttons">
./docs/index.html:407:            <img src="/img/team/stefan-milton-bache.jpg" class="img-responsive img-circle" alt="Stefan Milton Bache" height=150 width=150>
./docs/index.html:420:            <ul class="list-inline social-buttons">
./docs/index.html:438:            <img src="/img/team/steph-de-silva.png" class="img-responsive img-circle" alt="Steph de Silva" height=150 width=150>
./docs/index.html:451:            <ul class="list-inline social-buttons">
./docs/index.html:469:            <img src="/img/team/peter-ellis.jpg" class="img-responsive img-circle" alt="Peter Ellis" height=150 width=150>
./docs/index.html:482:            <ul class="list-inline social-buttons">
./docs/index.html:500:            <img src="/img/team/nick-golding.jpg" class="img-responsive img-circle" alt="Nick Golding" height=150 width=150>
./docs/index.html:513:            <ul class="list-inline social-buttons">
./docs/index.html:531:            <img src="/img/team/holly-kirk.jpg" class="img-responsive img-circle" alt="Holly Kirk" height=150 width=150>
./docs/index.html:544:            <ul class="list-inline social-buttons">
./docs/index.html:562:            <img src="/img/team/elle-saber.jpg" class="img-responsive img-circle" alt="Elle Saber" height=150 width=150>
./docs/index.html:575:            <ul class="list-inline social-buttons">
./docs/index.html:593:            <img src="/img/team/michael-sumner.png" class="img-responsive img-circle" alt="Michael Sumner" height=150 width=150>
./docs/index.html:606:            <ul class="list-inline social-buttons">
./docs/index.html:624:            <img src="/img/team/kate-saunders.png" class="img-responsive img-circle" alt="Kate Saunders" height=150 width=150>
./docs/index.html:637:            <ul class="list-inline social-buttons">
./docs/index.html:655:            <img src="/img/team/peter-hickey.jpg" class="img-responsive img-circle" alt="Peter Hickey" height=150 width=150>
./docs/index.html:668:            <ul class="list-inline social-buttons">
./docs/index.html:686:            <img src="/img/team/aniko-toth.jpg" class="img-responsive img-circle" alt="Anikó Tóth" height=150 width=150>
./docs/index.html:699:            <ul class="list-inline social-buttons">
./docs/index.html:715:            <img src="/img/team/richard-beare.JPG" class="img-responsive img-circle" alt="Richard Beare" height=150 width=150>
./docs/index.html:728:            <ul class="list-inline social-buttons">
./docs/index.html:744:            <img src="/img/team/liz-martin.jpg" class="img-responsive img-circle" alt="Liz Martin" height=150 width=150>
./docs/index.html:757:            <ul class="list-inline social-buttons">
./docs/index.html:775:            <img src="/img/team/jeff-hanson.jpg" class="img-responsive img-circle" alt="Jeff Hanson" height=150 width=150>
./docs/index.html:788:            <ul class="list-inline social-buttons">
./docs/index.html:806:            <img src="/img/team/jono-carroll.jpg" class="img-responsive img-circle" alt="Jono Carroll" height=150 width=150>
./docs/index.html:819:            <ul class="list-inline social-buttons">
./docs/index.html:837:            <img src="/img/team/samithree-rajapaksha.jpg" class="img-responsive img-circle" alt="Samithree Rajapaksha" height=150 width=150>
./docs/index.html:850:            <ul class="list-inline social-buttons">
./docs/index.html:866:            <img src="/img/team/saras-mei-windecker.jpg" class="img-responsive img-circle" alt="Saras Mei Windecker" height=150 width=150>
./docs/index.html:879:            <ul class="list-inline social-buttons">
./docs/index.html:897:            <img src="/img/team/damjan-vukcevic.jpg" class="img-responsive img-circle" alt="Damjan Vukcevic" height=150 width=150>
./docs/index.html:910:            <ul class="list-inline social-buttons">
./docs/index.html:928:            <img src="/img/team/jacinta-holloway.jpg" class="img-responsive img-circle" alt="Jacinta Holloway" height=150 width=150>
./docs/index.html:929:            <h3>Jacinta Holloway</h3>
./docs/index.html:941:            <ul class="list-inline social-buttons">
./docs/index.html:957:            <img src="/img/team/grahame-grieve.jpg" class="img-responsive img-circle" alt="Grahame Grieve" height=150 width=150>
./docs/index.html:970:            <ul class="list-inline social-buttons">
./docs/index.html:988:            <img src="/img/team/daniel-falster.jpg" class="img-responsive img-circle" alt="Daniel Falster" height=150 width=150>
./docs/index.html:1001:            <ul class="list-inline social-buttons">
./docs/index.html:1019:            <img src="/img/team/nikeisha-caruana.jpg" class="img-responsive img-circle" alt="Nikeisha Caruana" height=150 width=150>
./docs/index.html:1032:            <ul class="list-inline social-buttons">
./docs/index.html:1050:            <img src="/img/team/mathew-ling.jpg" class="img-responsive img-circle" alt="Mathew Ling" height=150 width=150>
./docs/index.html:1063:            <ul class="list-inline social-buttons">
./docs/index.html:1081:            <img src="/img/team/hugh-parsonage.jpg" class="img-responsive img-circle" alt="Hugh Parsonage" height=150 width=150>
./docs/index.html:1094:            <ul class="list-inline social-buttons">
./docs/index.html:1112:            <img src="/img/team/madeline-davey.jpg" class="img-responsive img-circle" alt="Madeline Davey" height=150 width=150>
./docs/index.html:1125:            <ul class="list-inline social-buttons">
./docs/index.html:1141:            <img src="/img/team/tim-hyndman.png" class="img-responsive img-circle" alt="Tim Hyndman" height=150 width=150>
./docs/index.html:1154:            <ul class="list-inline social-buttons">
./docs/index.html:1171:            <a href="https://scholar.google.com.au/citations?user=V1-2VSUAAAAJ&amp;hl=en">
./docs/index.html:1172:            <img src="/img/team/diego-barneche.jpg" class="img-responsive img-circle" alt="Diego Barneche" height=150 width=150>
./docs/index.html:1185:            <ul class="list-inline social-buttons">
./docs/index.html:1203:            <img src="/img/team/ross-gayler.jpg" class="img-responsive img-circle" alt="Ross Gayler" height=150 width=150>
./docs/index.html:1216:            <ul class="list-inline social-buttons">
./docs/index.html:1234:            <img src="/img/team/jackson-kwok.jpg" class="img-responsive img-circle" alt="Jackson Kwok" height=150 width=150>
./docs/index.html:1247:            <ul class="list-inline social-buttons">
./docs/index.html:1263:            <img src="/img/team/natasha-cadenhead.jpg" class="img-responsive img-circle" alt="Natasha Cadenhead" height=150 width=150>
./docs/index.html:1276:            <ul class="list-inline social-buttons">
./docs/index.html:1294:            <img src="/img/team/adam-gruer.jpg" class="img-responsive img-circle" alt="Adam Gruer" height=150 width=150>
./docs/index.html:1307:            <ul class="list-inline social-buttons">
./docs/index.html:1325:            <img src="/img/team/yan-holtz.jpg" class="img-responsive img-circle" alt="Yan Holtz" height=150 width=150>
./docs/index.html:1338:            <ul class="list-inline social-buttons">
./docs/index.html:1354:            <img src="/img/team/kim-fitter.jpg" class="img-responsive img-circle" alt="Kim Fitter" height=150 width=150>
./docs/index.html:1367:            <ul class="list-inline social-buttons">
./docs/index.html:1385:            <img src="/img/team/steve-bennett.jpg" class="img-responsive img-circle" alt="Steve Bennett" height=150 width=150>
./docs/index.html:1389:            <h4>opencouncildata.org</h4>
./docs/index.html:1398:            <ul class="list-inline social-buttons">
./docs/index.html:1414:            <img src="/img/team/mitch-ohara-wild.jpg" class="img-responsive img-circle" alt="Mitch O&#39;Hara-Wild" height=150 width=150>
./docs/index.html:1427:            <ul class="list-inline social-buttons">
./docs/index.html:1445:            <img src="/img/team/alicia-allan.jpg" class="img-responsive img-circle" alt="Alicia Allan" height=150 width=150>
./docs/index.html:1446:            <h3>Alicia Allan</h3>
./docs/index.html:1458:            <ul class="list-inline social-buttons">
./docs/index.html:1460:            <li><a href="http://twitter.com/correctalicia"><i class="fa fa-twitter"></i></a></li>
./docs/index.html:1476:            <img src="/img/team/tim-churches.jpg" class="img-responsive img-circle" alt="Tim Churches" height=150 width=150>
./docs/index.html:1489:            <ul class="list-inline social-buttons">
./docs/index.html:1507:            <img src="/img/team/justin-carmody.jpg" class="img-responsive img-circle" alt="Justin Carmody" height=150 width=150>
./docs/index.html:1520:            <ul class="list-inline social-buttons">
./docs/index.html:1552:        <div class="joinus"><p>The rOpenSci OzUnconference is our annual event loosely modeled on Foo Camp. This event is unlike many other unconferences in that it is mostly invite-only (past attendees often recommend new ones) with a few spots set aside for self-nominations from the community at large. The agenda is mostly decided during the conference itself.</p>
./docs/index.html:1570:        <h3 class="section-subheading text-muted">The event will be hosted at the <a href="https://www.monash.edu/international-business/city-location">Monash University City Campus</a>, 271 Collins St, Melbourne.</h3>
./docs/index.html:1603:            <a href="http://ropensci.org">
./docs/index.html:1604:              <img src="/img/sponsors/ropensci-lettering-colour.png" class="img-responsive img-centered" alt="">
./docs/index.html:1660:        <a href="https://njtierney.typeform.com/to/RYOPYW">Contact us</a> for more information about the event. This page is available at <a href="https://github.com/ropensci/ozunconf17">this repo</a>. Corrections, changes, and suggestions for improvement are welcome as pull requests.
./docs/index.html:1679:<script src="/js/ropensci.js"></script>
./docs/post/index.xml:4:    <title>Posts on rOpenSci Unconference</title>
./docs/post/index.xml:6:    <description>Recent content in Posts on rOpenSci Unconference</description>
./docs/font-awesome-v4.7.0/css/font-awesome.css:261:.fa-arrow-circle-o-down:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:264:.fa-arrow-circle-o-up:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:270:.fa-play-circle-o:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:370:.fa-pencil:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:383:.fa-pencil-square-o:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:431:.fa-plus-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:434:.fa-minus-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:437:.fa-times-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:440:.fa-check-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:443:.fa-question-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:446:.fa-info-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:452:.fa-times-circle-o:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:455:.fa-check-circle-o:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:492:.fa-exclamation-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:671:.fa-arrow-circle-left:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:674:.fa-arrow-circle-right:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:677:.fa-arrow-circle-up:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:680:.fa-arrow-circle-down:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:716:.fa-scissors:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:933:.fa-circle-o:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:945:.fa-circle:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:979:.fa-flag-checkered:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:1052:.fa-chevron-circle-left:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:1055:.fa-chevron-circle-right:before {
./docs/font-awesome-v4.7.0/css/font-awesome.css:1058:.fa-chevron-circle-up:before {
./docs/font-awesome-v4.7.0/css/font-a

