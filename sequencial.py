
from mnemonic import Mnemonic

class Sequencial:
    def __init__(self, INDEX=0):
        self.N = 12
        self.M = 0
        
    def get_next(self, M, N):
        # Inicializa o gerador BIP39 em inglês
        mnemo = Mnemonic("english")

        # Define o número de palavras da seed (12, 15, 18, 21 ou 24)
        #N = 12
        #M = 0 # Index of word from BIP39

        # Pega a primeira palavra da lista BIP39
        first_word = mnemo.wordlist[M]  # geralmente 'abandon'

        # Cria a base da frase com N - 1 repetições da primeira palavra
        base_phrase = [first_word] * (N - 1)

        # Dicionário para armazenar frases válidas
        #valid_phrases = {}
        my_list = []

        # Testa todas as palavras possíveis como última palavra
        for candidate in mnemo.wordlist:
            test_phrase = base_phrase + [candidate]
            phrase_str = " ".join(test_phrase)
            if mnemo.check(phrase_str):
                #valid_phrases[candidate] = phrase_str
                my_list.append(phrase_str)

        # Exibe os resultados
        #print(f"Frases válidas encontradas: {len(valid_phrases)}")
        #for word, phrase in valid_phrases.items():
        #    print(f"{phrase}")

        return(my_list)