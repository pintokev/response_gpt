import inspect
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

nouveau_param_obligatoire = ["content", "id"]
nouveau_param_valid = ["image_url"] + nouveau_param_obligatoire

def stream_response(headers, **params):
    debut = time()
    client = get_client_openai(headers)
    filtered_params = gestion_parametres(client, **params)
    try:
        if "ERREUR" in filtered_params: raise KeyError("KeyError")
        stream = client.responses.create(**get_pipeline(**filtered_params))
        for event in stream:
            yield handle_event(event)
    except openai.AuthenticationError:
        yield {"ERREUR":"La cle API n'est pas bonne ou inexistante. Il faut la passer (par ordre de priorite) soit dans le Authorization Header ou la mettre dans une variable d'environnement tokenGPT ou OPENAI_API_KEY"}
    except KeyError:
        yield filtered_params
    # print(f"Stream de la réponse total en {round(time()-debut, 2)}secs")

def get_content_and_images(content, image_url):
    if image_url is not None:
        return [{"type":"input_text", "text": content},
                {"type": "input_image","image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"}]
    else: return content
def get_pipeline(**filtered_params):
    image_url = None
    content = filtered_params.pop("content")
    if "image_url" in filtered_params: image_url = filtered_params.pop("image_url")
    for param_valid in nouveau_param_valid:
        if param_valid in filtered_params: filtered_params.pop(param_valid)
    pipeline = {**filtered_params, **{"input":[{"role":"user", "content":get_content_and_images(content, image_url)}]}, **{"stream":True}}
    return pipeline
def gestion_parametres(client, **params):
    signature = inspect.signature(client.responses.create)
    filtered_params = get_filtered_params(signature, **params)
    verification, param = verifier_params_obligatoires(signature, **filtered_params)
    if verification: return filtered_params
    else: return {"ERREUR":f"Il manque le paramètre obligatoire {param} dans la requête"}
def verifier_params_obligatoires(signature, **filtered_params):
    for param in get_params_obligatoire(signature):
        if param not in filtered_params:
            return False, param
    return True, None
def get_params_obligatoire(signature):
    params_obligatoires = [
        name for name, param in signature.parameters.items()
        if param.default == inspect.Parameter.empty and param.kind in (
        inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    if "input" in params_obligatoires: params_obligatoires.remove("input")
    for param_obligatoire in nouveau_param_obligatoire:
        params_obligatoires.append(param_obligatoire)
    return params_obligatoires
def get_filtered_params(signature, **params):
    valid_params = list(signature.parameters.keys())
    if "stream" in valid_params: valid_params.remove("stream")
    if "input" in valid_params: valid_params.remove("input")
    for param_valid in nouveau_param_valid:
        valid_params.append(param_valid)
    filtered_params = {k: v for k, v in params.items() if k in valid_params}
    return filtered_params

@app.route('/stream', methods=["POST"])
def stream():
    body = request.json
    headers = request.headers
    def generate():
        response = {"ERREUR":"Pas un generateur"}
        for data in stream_response(headers, **body):
            if isinstance(data, types.GeneratorType):
                response = list(data)[0]
            elif isinstance(data, dict): response = data
            if "ERREUR" in response: yield "ERREUR - " + response["ERREUR"]
            else: yield response["content"]
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
