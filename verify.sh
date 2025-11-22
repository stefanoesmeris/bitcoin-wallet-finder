#!/bin/bash

# Caminho do arquivo que contém o estado
STATE_FILE="/tmp/script_status.flag"

# Verificar se o arquivo existe
if [ ! -f "$STATE_FILE" ]; then
    echo "Arquivo de estado não encontrado: $STATE_FILE - criando arquivo"
    echo "running" > /tmp/script_status.flag
fi

# Ler o estado do arquivo
STATE=$(cat "$STATE_FILE" | tr -d '[:space:]')  # Remove espaços extras


# Caminho completo do script Python
SCRIPT_PYTHON="/home/stefano/bitcoin-wallet-finder/main.py"

# Comando para executar o script Python
COMMAND="python3 /home/stefano/bitcoin-wallet-finder/main.py "

# Nome do processo (somente o nome do script Python, sem caminho)
PROCESS_NAME=$(basename "$SCRIPT_PYTHON")

# Verificar se o script já está em execução
if pgrep -f "$PROCESS_NAME" > /dev/null; then
    echo "$(date) - O script $PROCESS_NAME já está em execução."
else
    echo "$(date) - O script $PROCESS_NAME não está em execução. Iniciando..."
    nohup $COMMAND > /dev/null 2>&1 &
    echo "$(date) - Script $PROCESS_NAME iniciado com sucesso."
fi

# Tomar decisão com base no estado
case "$STATE" in
    running)
        echo "O estado é 'running'. Continuando a operação..."
        # Adicione aqui as ações para o estado 'running'
        ;;
    suspend)
        echo "O estado é 'suspend'. Pausando a operação..."
        # Simula espera até que o estado mude
        echo "suspend" > /tmp/script_status.flag
        ;;
    stop)
        echo "O estado é 'stop'. Pausando a operação."
        # Adicione aqui as ações para encerrar
        echo "suspend" > /tmp/script_status.flag
        ;;
    *)
        echo "Estado desconhecido: $STATE"
        exit 2
        ;;
esac
