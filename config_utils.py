import os
import json

class ConfigUtils:
    def __init__(self, setup_file='setup.json'):
        self.setup_file = setup_file

    def manipular_configuracao(self, acao, novos_valores=None):
        if acao == 'ler':
            if os.path.exists(self.setup_file):
                with open(self.setup_file, 'r') as f:
                    return json.load(f)
            return None
        elif acao == 'atualizar' and novos_valores:
            with open(self.setup_file, 'w') as f:
                json.dump(novos_valores, f, indent=4)

    @staticmethod
    def write_good_seed_to_file(data, filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                try:
                    dados_existentes = json.load(f)
                except json.JSONDecodeError:
                    dados_existentes = []
        else:
            dados_existentes = []

        # dados_existentes.append(data)
        dados_existentes.extend(data)
        with open(filename, "w") as f:

            json.dump(dados_existentes, f, indent=4)
