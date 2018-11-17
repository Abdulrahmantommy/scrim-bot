from flask import Flask, request
from flask import json as fjson
import json

app = Flask(__name__)

@app.route('/')
def api_root():
    return 'Hello'

## Returns ordered list of leaderboard entries
# for solo
@app.route('/solo', methods=['GET'])
def api_solo():
    with open('solo_leaderboard.json') as leaderboard_file:
        contents = json.load(leaderboard_file)
        scores = contents['scores']

        scores.sort(key=lambda score: score['score'], reverse=True)

        return fjson.dumps(scores)

# for duo
@app.route('/duo', methods=['GET'])
def api_duo():
    with open('duo_leaderboard.json') as leaderboard_file:
        contents = json.load(leaderboard_file)
        scores = contents['scores']

        scores.sort(key=lambda score: score['score'], reverse=True)

        return fjson.dumps(scores)

# for squad
@app.route('/squad', methods=['GET'])
def api_squad():
    with open('squad_leaderboard.json') as leaderboard_file:
        contents = json.load(leaderboard_file)
        scores = contents['scores']

        scores.sort(key=lambda score: score['score'], reverse=True)

        return fjson.dumps(scores)


if __name__ == '__main__':
    app.run()