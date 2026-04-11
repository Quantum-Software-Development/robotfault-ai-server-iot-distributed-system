import socket
import threading
import joblib
import pandas as pd
import ast

HOST = '0.0.0.0'
PORT = 5000

model_saved = joblib.load('Bot Status Identificator.pkl')
bot_list = pd.DataFrame(columns=['id', 'conn', 'addr', 'amount_fail'])
bot_list_lock = threading.RLock()


def exist(addr: tuple) -> bool:
    '''Verifica se um cliente já existe na lista de bots.'''
    global bot_list, bot_list_lock
    
    with bot_list_lock:
        if bot_list.empty:
            return False
        if addr in bot_list['addr'].values:
            return True
    return False


def register_bot(conn, addr: tuple) -> None:
    '''Registra um cliente na lista de bots.'''
    global bot_list, bot_list_lock
    
    with bot_list_lock:
        if not exist(addr):
            bot_list = pd.concat(
                [
                    bot_list,
                    pd.DataFrame(
                        {
                            'id': [len(bot_list) + 1],
                            'conn': [conn],
                            'addr': [addr],
                            'amount_fail': [0]
                        }
                    )
                ],
                ignore_index=True
            )


def remove_bot(addr: tuple) -> None:
    '''Remove um cliente da lista de bots.'''
    global bot_list, bot_list_lock

    with bot_list_lock:
        print(f"Antes: {bot_list.shape[0]} bots")
        bot_list = bot_list[bot_list['addr'] != addr].reset_index(drop=True)
        print(f"Depois: {bot_list.shape[0]} bots, removido {addr}")


def response(conn, addr: tuple, msg: str) -> None:
    '''Envia resposta ao cliente especificado.'''
    global bot_list, bot_list_lock

    try:
        if msg.lower() == 'listar bots':
            with bot_list_lock:
                msg = str(
                    [
                        {'id': row['id'], 'addr': row['addr']}
                        for _, row in bot_list[['id', 'addr']].iterrows()
                    ]
                )
        else:
            msg_parts = msg.split(',')
            with bot_list_lock:
                proba = model_saved.predict_proba(
                    pd.DataFrame(
                        {
                            'uptime_horas': ast.literal_eval(msg_parts[0]),
                            'latencia_ms': ast.literal_eval(msg_parts[1]),
                            'uso_cpu_pct': ast.literal_eval(msg_parts[2]),
                            'erros_api_por_minuto': ast.literal_eval(msg_parts[3]),
                            'versao_firmware': ast.literal_eval(msg_parts[4])
                        }
                    )
                )

                amount_fail = 1
                pos_possible_fail = 1

                for pos, row in bot_list[['addr', 'amount_fail']].iterrows():
                    if addr == row['addr']:
                        amount_fail = row['amount_fail']
                        pos_possible_fail = pos
                        break

                if proba[0][1] > 0.5:
                    msg = (
                        f'1. Status atual do Bot: Funcionamento NORMAL, '
                        f'com acurácia de {proba[0][1] * 100:.0f}%\n'
                        f'2. Quantidade de falhas acumuladas: {amount_fail}'
                    )
                else:
                    bot_list.loc[pos_possible_fail, 'amount_fail'] += 1
                    msg = (
                        f'1. Status atual do Bot: FALHA no Funcionamento, '
                        f'com acurácia de {proba[0][0] * 100:.0f}%\n'
                        f'2. Quantidade de falhas acumuladas: '
                        f'{bot_list.loc[pos_possible_fail, "amount_fail"]}'
                    )

        conn.sendall(msg.encode())

    except OSError as e:
        print(f"Erro ao enviar mensagem para {addr}: {e}")
        remove_bot(addr)


def handle_client(conn, addr: tuple):
    '''Função para lidar com a conexão do cliente. Recebe o socket da conexão e o endereço do cliente.'''
    global bot_list, bot_list_lock

    try:
        while True:
            msg = conn.recv(1024).decode()  # Recebe a msg do cliente, decodificando de bytes para string
            
            if msg.lower() == 'sair':
                remove_bot(addr)
                break  # Sai do loop quando o cliente se desconecta
            
            elif msg.lower() == 'cadastro':
                register_bot(conn, addr)  # Registra o cliente na lista de bots
            
            elif msg:
                response(conn, addr, msg)  # Envia a mensagem de volta para o cliente
                
    except OSError as e:
        # Trata o erro quando o socket é fechado
        print(f"Conexão fechada para {addr}: {e}")
        remove_bot(addr)
    finally:
        # Garante que a conexão seja fechada
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
