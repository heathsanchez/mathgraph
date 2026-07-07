## Description
Code-golf competition! 


## Proposed Implementation

1. The bot stores a queue of challenges. Staff members should be able to add new questions to the queue with a command (say, `.cg add`). Questions should be uploaded as a .json file, containing the problem description, visible test cases and hidden test cases.
2. The bot should maintain per-day leaderboards, as well as an overall one in a configured channel (top 25 entries). 
    - Per-day leaderboards should display the username and the entry length.
    - We could adopt the Advent of Code style for the overall leaderboard - people get points between 25 to 1 for their rank on the leaderboard on the day. The overall score is the sum of the points obtained on each day.
3. People should be able to assign themselves a `@Code Golf Participant` role with a `.cg join` command.
4. The bot should post a new challenge everyday at a configured time, pinging this role. The message should contain the problem description and visible test cases, a blank leaderboard for the day, and the best solution of the previous day's question.
5. People submit their solutions via Forms, trying to shorten their code as much as possible. 
6. Tests are run on the code using snekbox with the visible and hidden test cases, and the results are shown right after submission.
7. If all tests pass, the bot receives the user's name and the length of their code. If the code is short enough to make it to the top 25, the leaderboard for the day is edited. In case the same user already had an entry on the leaderboard, remove the previous entry. Ties are broken by time of submission.
8. At the end of the event, top 3 on the overall leaderboard get a vanity `@Code Golf Winner` role.


## Would you like to implement this yourself?
- [x] I'd like to implement this feature myself
- [ ] Anyone can implement this feature
