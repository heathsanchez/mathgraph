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