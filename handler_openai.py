import json

from flask import Flask, Response, jsonify, stream_with_context
from openai import OpenAI
from openai.types.responses import *

app = Flask(__name__)

def stream_response():
    client = OpenAI(api_key="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")
    stream = client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": "Say 'double bubble bath' ten times fast.",
            },
        ],
        stream=True,
    )

    for event in stream:
        # print(f"Received event: {event}")  # Ajoute ceci pour voir les événements

        if isinstance(event, ResponseTextDeltaEvent):
            yield {'type': 'delta', 'content': event.delta}
        if isinstance(event, ResponseCreatedEvent):
            # yield {'type': 'event', 'name': 'Response Created'}
            pass
        elif isinstance(event, ResponseCompletedEvent):
            # yield {'type': 'event', 'name': 'Response Completed'}
            pass
        # Ajoute d'autres elif pour les événements que tu veux gérer
        else:
            # yield {'type': 'unhandled', 'name': type(event).__name__}
            pass

@app.route('/stream')
def stream():
    # print(stream_response())
    # def generate():
    for data in stream_response():
        # print(data)
        yield json.dumps(data) + "\n"
    # return Response(generate())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
