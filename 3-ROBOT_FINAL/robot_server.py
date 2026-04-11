import socket
import threading
import joblib
import pandas as pd
import ast

# [EN] HOST defines where the server will listen for incoming connections.
#      0.0.0.0 tells the OS to listen on all available IPv4 interfaces.
#      Any machine that can reach this host and PORT on the network can try to connect.
# [PT-BR] HOST define onde o servidor vai escutar por conexões.
#         0.0.0.0 faz o sistema ouvir em todas as interfaces IPv4 disponíveis.
#         Qualquer máquina que alcance este host e PORTA na rede pode tentar se conectar.
HOST = "0.0.0.0"
PORT = 5000

# Valor sentinela para o comando de saída do cliente / Sentinel value for client exit command
SENTINEL_EXIT = "sair"

# Pre-trained ML model used to classify robot status
model_saved = joblib.load("Bot Status Identificator.pkl")

# Shared table with connected robots and their state
bot_list = pd.DataFrame(columns=["id", "conn", "addr", "amount_fail"])
bot_list_lock = threading.RLock()  # Lock para ambiente multithread / RLock for concurrent access


def exist(addr: tuple) -> bool:
    """Check if a client address is already registered in bot_list."""
    global bot_list, bot_list_lock

    with bot_list_lock:
        if bot_list.empty:
            return False
        return addr in bot_list["addr"].values


def register_bot(conn, addr: tuple) -> None:
    """Register a new robot client in bot_list if it is not already present."""
    global bot_list, bot_list_lock

    with bot_list_lock:
        if not exist(addr):
            bot_list = pd.concat(
                [
                    bot_list,
                    pd.DataFrame(
                        {
                            "id": [len(bot_list) + 1],
                            "conn": [conn],
                            "addr": [addr],
                            "amount_fail": [0],
                        }
                    ),
                ],
                ignore_index=True,
            )


def remove_bot(addr: tuple) -> None:
    """Remove a robot client from bot_list based on its address."""
    global bot_list, bot_list_lock

    with bot_list_lock:
        print(f"Antes: {bot_list.shape[0]} bots")
        bot_list = bot_list[bot_list["addr"] != addr].reset_index(drop=True)
        print(f"Depois: {bot_list.shape[0]} bots, removido {addr}")


def response(conn, addr: tuple, msg: str) -> None:
    """Process a client message (commands or feature vector) and send a reply."""
    global bot_list, bot_list_lock

    try:
        if msg.lower() == "listar bots":
            # Return a simple list with id and address of each registered robot
            with bot_list_lock:
                msg = str(
                    [
                        {"id": row["id"], "addr": row["addr"]}
                        for _, row in bot_list[["id", "addr"]].iterrows()
                    ]
                )
        else:
            # Expecting a comma-separated feature vector
            msg_parts = msg.split(",")

            with bot_list_lock:
                proba = model_saved.predict_proba(
                    pd.DataFrame(
                        {
                            "uptime_horas": ast.literal_eval(msg_parts[0]),
                            "latencia_ms": ast.literal_eval(msg_parts[1]),
                            "uso_cpu_pct": ast.literal_eval(msg_parts[2]),
                            "erros_api_por_minuto": ast.literal_eval(msg_parts[3]),
                            "versao_firmware": ast.literal_eval(msg_parts[4]),
                        }
                    )
                )

                amount_fail = 1
                pos_possible_fail = 1

                # Find current failure count for this robot (by addr)
                for pos, row in bot_list[["addr", "amount_fail"]].iterrows():
                    if addr == row["addr"]:
                        amount_fail = row["amount_fail"]
                        pos_possible_fail = pos
                        break

                # proba[0][1] assumed to be the probability of "normal" class
                if proba[0][1] > 0.5:
                    msg = (
                        "1. Status atual do Bot: Funcionamento NORMAL, "
                        f"com acurácia de {proba[0][1] * 100:.0f}%\n"
                        f"2. Quantidade de falhas acumuladas: {amount_fail}"
                    )
                else:
                    # Increment failure counter for this robot
                    bot_list.loc[pos_possible_fail, "amount_fail"] += 1
                    msg = (
                        "1. Status atual do Bot: FALHA no Funcionamento, "
                        f"com acurácia de {proba[0][0] * 100:.0f}%\n"
                        "2. Quantidade de falhas acumuladas: "
                        f'{bot_list.loc[pos_possible_fail, "amount_fail"]}'
                    )

        conn.sendall(msg.encode())

    except OSError as e:
        print(f"Erro ao enviar mensagem para {addr}: {e}")
        remove_bot(addr)


def handle_client(conn, addr: tuple) -> None:
    """Handle a single TCP client connection and dispatch its commands."""
    global bot_list, bot_list_lock

    try:
        while True:
            msg = conn.recv(1024).decode()

            # Client closed the connection
            if not msg:
                remove_bot(addr)
                break

            # Sentinel command to close from the client side
            if msg.lower() == SENTINEL_EXIT:
                remove_bot(addr)
                break

            elif msg.lower() == "cadastro":
                register_bot(conn, addr)

            else:
                response(conn, addr, msg)

    except OSError as e:
        print(f"Conexão fechada para {addr}: {e}")
        remove_bot(addr)
    finally:
        conn.close()


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"Servidor ouvindo em {HOST}:{PORT}...")

        while True:
            conn, addr = server.accept()
            print(f"Conexão estabelecida com {addr}")
            threading.Thread(target=handle_client, args=(conn, addr)).start()