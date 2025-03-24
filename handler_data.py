import os
from json import dump, load


class Data:
    def __init__(self, id):
        self.id = id
        self.user_dossier = "data/"+id
        self.fichier = ['historique.json', 'instructions.json', 'function_tools.json', 'vector.json']
        self.set_all_path_files()
        self.init_directory()

    def read_file(self, filepath):
        with open(filepath, "r") as file:
            return load(file)
    def append_file(self, filepath, donnee):
        with open(filepath, "a") as file:
            dump(donnee, file, indent=2)
    def write_file(self, filepath, donnee):
        with open(filepath, "w") as file:
            dump(donnee, file, indent=2)

    def set_all_path_files(self):
        tab = []
        for file in self.fichier:
            tab.append(os.path.join(self.user_dossier , file))
        self.fichier = tab
    def init_directory(self):
        os.makedirs('data', exist_ok=True)
        os.makedirs("data/"+str(self.id), exist_ok=True)
        for pathfile in self.fichier:
            if not os.path.exists(pathfile):
                with open(pathfile, 'w') as f:
                    if "historique" in pathfile: dump([], f)
                    else: dump({}, f)

    def add_instructions(self, new_instructions):
        if new_instructions == "": return
        instruction_path = os.path.join(self.user_dossier , "instructions.json")
        instructions = self.read_file(instruction_path)
        try: instructions["instructions"] += "\n"+new_instructions
        except KeyError: instructions["instructions"] = new_instructions
        self.write_file(instruction_path, instructions)
    def remove_instructions(self):
        instruction_path = os.path.join(self.user_dossier , "instructions.json")
        self.write_file(instruction_path, {})
    def change_instructions(self, new_instructions):
        instruction_path = os.path.join(self.user_dossier , "instructions.json")
        self.write_file(instruction_path, {"instructions":str(new_instructions)})

    def get_line(self, role, content):
        return {"role":str(role), "content":content}
    def add_historique(self, role, new_historique):
        if role not in ["user", "assistant", "system", "developer"]: return
        if new_historique == "": return
        new_historique = self.get_line(role, new_historique)
        historique_path = os.path.join(self.user_dossier , "historique.json")
        historique = self.read_file(historique_path)
        historique.append(new_historique)
        self.write_file(historique_path, historique)
    def remove_historique(self):
        historique_path = os.path.join(self.user_dossier , "historique.json")
        self.write_file(historique_path, [])
    def change_historique(self, new_historique):
        historique_path = os.path.join(self.user_dossier , "historique.json")
        self.write_file(historique_path, new_historique)

    def get_function_tools(self):
        return self.read_file(self.user_dossier + "/function_tools.json")
    def get_historique(self):
        return self.read_file(self.user_dossier+"/historique.json")
    def get_instructions(self):
        return self.read_file(self.user_dossier+"/instructions.json")
    def get_vector(self):
        return self.read_file(self.user_dossier+"/vector.json")


if __name__ == '__main__':
    data = Data("billy")
    data.change_historique("user", "dsfezfz")
