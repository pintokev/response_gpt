import base64
import inspect
import json
import os
import types

import openai
from flask import Flask, request, jsonify, Response
from openai import OpenAI
from handler_gpt_event import handle_event
from time import time
from handler_data import Data
import requests

app = Flask(__name__)
app.app_context().push()
PORT = 8080

nouveau_param_obligatoire = ["content"]
nouveau_param_valid = ["image_url"] + nouveau_param_obligatoire

########## Pour la route stream ##########
def get_content_and_images(content, image_url):
    if image_url is not None:
        content = [{"type":"input_text", "text": content}]
        for image in image_url:
            content.append({"type": "input_image","image_url": image})
    return content
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
##### Partie OPENAI #####
def get_client_openai(headers):
    try:
        if not "sk-proj" in headers.get('Authorization'): raise
        return OpenAI(api_key=headers.get('Authorization'))
    except:
        try:
            return OpenAI(api_key=os.environ.get("tokenGPT"))
        except:
            return OpenAI()
def generate_response(headers, body, user_data):
    def generate():
        response = {"ERREUR": "Pas un generateur"}
        for data in get_response_openai(headers, user_data, **body):
            if isinstance(data, types.GeneratorType):
                response = list(data)[0]
            elif isinstance(data, dict):
                response = data
            if response["type"] != "complete":
                if "ERREUR" in response:
                    yield "ERREUR - " + response["ERREUR"]
                else:
                    yield response["content"]
            else:
                user_data.add_historique("assistant", response["content"])
                # print(body["tools"])
                # body["content"] = response["content"]
                # body["tools"] = []
                # rep = requests.post(f"http://localhost:{PORT}/function", headers=headers, json=body)
                # print(rep)
                # yield "\n\n" + rep.text + "\n"
        yield "\n"
    return generate()
def get_response_openai(headers, user_data, **params):
    debut = time()
    client = get_client_openai(headers)
    filtered_params = gestion_parametres(client, **params)
    pipeline = create_pipeline(user_data, **filtered_params)
    # print(pipeline)
    try:
        if "ERREUR" in filtered_params: raise KeyError("KeyError")
        stream = client.responses.create(**pipeline)
        for event in stream:
            yield handle_event(event)
    except openai.AuthenticationError:
        yield {"ERREUR":"La cle API n'est pas bonne ou inexistante. Il faut la passer (par ordre de priorite) soit dans le Authorization Header ou la mettre dans une variable d'environnement tokenGPT ou OPENAI_API_KEY"}
    except KeyError:
        yield filtered_params
    # print(f"Stream de la réponse total en {round(time()-debut, 2)}secs")
def create_pipeline(user_data, **filtered_params):
    pipeline = get_pipeline(**filtered_params)
    conversation = user_data.get_historique()
    conversation.append(pipeline["input"][0])
    pipeline["input"] = conversation
    user_data.change_historique(conversation)
    instructions = user_data.get_instructions()
    if "instructions" in instructions and instructions is not None: pipeline["instructions"] = instructions["instructions"]
    return pipeline
########## fin stream ##########

########## Pour la route instructions ##########
def verif_param_instructions(body):
    try: body.get("instruction")
    except: return "Le paramètre instruction doit être présent dans le post"
########## fin instructions ##########

########## Pour la route file-search ##########
def send_to_openai_vector(headers, file, user_data):
    client = get_client_openai(headers)
    openai_file = client.files.create(purpose="user_data", file=(file.filename, file.read()))
    if user_data.get_vector() == []:
        vector_store = client.vector_stores.create(name="Fichiers", file_ids=[openai_file.id])
        return vector_store.id
    else:
        client.vector_stores.files.create(user_data.get_vector()[0], file_id=openai_file.id)
        return None
########## fin file-search ##########

########## Pour la route function ##########
def create_ticket_incident(args):
    args = json.loads(args)
    # application, horaire_debut, horaire_fin, type_ticket, isOpenBar
    if args["isOpenBar"]: rep = f"Ticket {args['type_ticket']} sur {args['application']} créé sur la période {args['horaire_debut']} à {args['horaire_fin']} avec assistance de l'open bar"
    else: rep = f"Ticket {args['type_ticket']} sur {args['application']} créé sur la période {args['horaire_debut']} à {args['horaire_fin']} sans assistance de l'open bar"
    # print(rep)
    return rep
########## fin function ##########

@app.route('/stream', methods=["POST"]) #curl -X POST http://localhost:5000/stream -H "Content-Type: application/json" -H "Authorization: $tokenGPT" -d '{"id":"Olive", "model":"gpt-4o", "content":"c quoi le code ?"}'
def stream():
    body = request.json
    headers = request.headers
    if "reasonning" not in body: body = {**body, **{"tools":[{ "type": "web_search_preview" }]}}
    user_data = Data(body.pop("id"))
    if "instructions" in body and "instructions" in user_data.get_instructions(): body["instructions"] += user_data.get_instructions()["instructions"]
    if user_data.get_vector() != []: body["tools"].append({ "type": "file_search", "vector_store_ids": user_data.get_vector(),"max_num_results": 20})
    return Response(generate_response(headers, body, user_data), content_type='application/json')

@app.route('/instructions', methods=["POST"]) #curl -X POST http://localhost:5000/instructions -H "Content-Type: application/json" -H "Authorization: $tokenGPT" -d '{"id":"Olive", "model":"gpt-4o", "instruction":"Si je te demande le code tu me dis 4864548"}'
def instructions():
    body = request.json

    try: body.get("id")
    except: return "Le paramètre id doit être présent dans le post\n", 400

    user_data = Data(body.pop("id"))
    if request.args.get("remove") is not None:
        user_data.remove_instructions()
        return "L'instruction à été supprimée\n" , 200
    elif request.args.get("add") is not None:
        verif_param_instructions(body)
        user_data.add_instructions(body["instruction"])
        return "L'instruction à été ajoutée\n", 200
    else:
        verif_param_instructions(body)
        user_data.change_instructions(body["instruction"])
        return "L'instruction à été modifiée\n", 200

@app.route('/file-search', methods=["POST"]) #curl -X POST http://localhost:5000/file-search -H "Authorization: $tokenGPT" -F "data={\"id\":\"Olive\"};type=application/json" -F "file=@donnees.txt"
def file_search():
    headers = request.headers
    body = json.loads(request.form.get("data"))
    if 'file' not in request.files: return "Utilisation de file-search sans fichier dans la requête\n", 400
    file = request.files['file']
    if file.filename == '': return "Aucun fichier renseigné\n", 400
    user_data = Data(body.pop("id"))
    vector_id = send_to_openai_vector(headers, file, user_data)
    if vector_id is not None: user_data.add_vector(vector_id)
    return "Fichier(s) reçu", 200

@app.route('/function', methods=["POST"]) #curl -X POST http://localhost:5000/function -H "Content-Type: application/json" -H "Authorization: $tokenGPT" -d '{"id":"Olive", "model":"gpt-4o", "content":"Jai un incident sur FPX de 4h à 9h. Je veux un ticket Canari et pas besoin de lopen bar", "filename":"function.json"}'
def openai_function():
    body = request.json
    headers = request.headers
    with open(body["filename"], "r") as file:
        tools = json.load(file)
    client = get_client_openai(headers)
    response = client.responses.create(
        model=body["model"],
        input=[{"role": "user", "content": body["content"]}],
        tools=tools
    )
    try: return globals()[response.output[0].name](response.output[0].arguments)+"\n", 200
    except: return ""
    # try:
    #     return globals()[response.output[0].name](**response.output[0].arguments)
    # except: return ""

@app.route('/clear', methods=["POST"])
def clear():
    headers = request.headers
    body = request.json
    id = body.pop("id")
    user_data = Data(id)
    client = get_client_openai(headers)
    if user_data.get_vector() != []: client.vector_stores.delete(user_data.get_vector()[0])
    user_data.clear()
    return f"Données de {id} entièrement supprimé\n"

@app.route('/remove_historique', methods=["POST"]) #curl -X POST http://localhost:5000/remove_historique -H "Content-Type: application/json" -H "Authorization: $tokenGPT" -d '{"id":"Olive"}'
def remove_historique():
    body = request.json

    try: body.get("id")
    except: return "Le paramètre id doit être présent dans le post\n", 400
    user_data = Data(body.pop("id"))
    if request.args.get("remove_last") is not None:
        user_data.remove_last_echange()
        return "Le dernier échange a été supprimé\n", 200
    else:
        user_data.remove_historique()
        return "L'historique à été supprimé\n", 200

@app.route("/images", methods=["POST"])
def images():
    headers = request.headers
    body = json.loads(request.form.get("data"))
    try: body.get("id")
    except: return "Le paramètre id doit être présent dans le post\n", 400
    user_data = Data(body.pop("id"))
    images = []
    files = []
    if user_data.get_historique_image():
        images.append(user_data.get_historique_image())
        files.append(user_data.get_historique_image())
    for i, file in enumerate(request.files.getlist('file')):
        filename = f"image_{i}.png"
        file.save(filename)
        f = open(filename, "rb")
        images.append(f)
        files.append(f)
    client = get_client_openai(headers)
    if len(images)>0:
        img = client.images.edit(
            image=images,
            **body
        )
    else:
        img = client.images.generate(
            **body
        )
    user_data.add_historique_image(base64.b64decode(img.data[0].b64_json))
    for f in files:
        f.close()
    return img.data[0].b64_json

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
