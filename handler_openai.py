import json
import os
import types

import openai
from flask import Flask, request, jsonify, Response
from openai import OpenAI
from handler_gpt_event import handle_event
from time import time

app = Flask(__name__)
app.app_context().push()

def stream_response(headers, params):

    debut = time()
    client = get_client_openai(headers)

    try:
        stream = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "user",
                    "content": "quel est la météo de demain ? J'habite à Alfortville",
                },
            ],
            stream=True,
        )
        for event in stream:
            yield handle_event(event)
    except openai.AuthenticationError:
        yield {"ERREUR":"La cle API n'est pas bonne ou inexistante. Il faut la passer (par ordre de priorite) soit dans le Authorization Header ou la mettre dans une variable d'environnement tokenGPT ou OPENAI_API_KEY"}
    # print(f"Stream de la réponse total en {round(time()-debut, 2)}secs")

@app.route('/stream', methods=["POST"])
def stream():
    body = request.json
    headers = request.headers
    def generate():
        response = {"error":"Pas un generateur"}
        for data in stream_response(headers, body):
            if isinstance(data, types.GeneratorType):
                response = list(data)[0]
            elif isinstance(data, dict): response = data
            yield response["content"]
        yield "\n"
    return Response(generate(), content_type='application/json')

def get_client_openai(headers):
    try: return OpenAI(api_key=headers.get('Authorization'))
    except:
        try:
            return OpenAI(api_key=os.environ.get("tokenGPT"))
        except:
            return OpenAI()
    return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
