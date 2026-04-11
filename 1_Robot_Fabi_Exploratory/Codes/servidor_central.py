
import socket
import threading
import json
import pickle
import numpy as np
import os
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000
MODEL_PATH = "modelo_falha_rf.pkl"

alertas_totais = 0
lock_alertas = threading.Lock()


def log(level, message, client=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if client:
        ip, port = client
        print(f"[{timestamp}] [{level}] [{ip}:{port}] {message}")
    else:
        print(f"[{timestamp}] [{level}] {message}")


def verificar_modelo(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo de modelo não encontrado: {path}. "
            f"Execute 'python3 treinar_modelo.py' primeiro."
        )

    if os.path.getsize(path) == 0:
        raise ValueError(f"O arquivo de modelo está vazio: {path}")

    try:
        with open(path, "rb") as f:
            modelo = pickle.load(f)
    except pickle.UnpicklingError:
        raise ValueError(f"O arquivo {path} não é um pickle válido.")
    except Exception as e:
        raise RuntimeError(f"Falha ao carregar o modelo: {e}")

    if not hasattr(modelo, "predict"):
        raise TypeError("O objeto carregado não possui o método '.predict()'.")

    return modelo


def classificar_dados(dados):
    campos_obrigatorios = ["temperatura", "vibracao", "rpm"]

    for campo in campos_obrigatorios:
        if campo not in dados:
            raise KeyError(f"Campo obrigatório ausente: {campo}")

    temperatura = float(dados["temperatura"])
    vibracao = float(dados["vibracao"])
    rpm = float(dados["rpm"])

    X = np.array([[temperatura, vibracao, rpm]])
    pred = modelo.predict(X)[0]

    return "FALHA" if pred == 1 else "NORMAL"


def tratar_cliente(conn, addr):
    global alertas_totais

    log("INFO", "Nova conexão aceita.", addr)

    try:
        while True:
            dados_brutos = conn.recv(1024)

            if not dados_brutos:
                log("INFO", "Cliente encerrou a conexão.", addr)
                break

            try:
                mensagem = dados_brutos.decode("utf-8")
                dados = json.loads(mensagem)
            except UnicodeDecodeError:
                erro = {"erro": "Falha ao decodificar mensagem em UTF-8."}
                conn.send(json.dumps(erro).encode("utf-8"))
                log("ERROR", "Mensagem não pôde ser decodificada.", addr)
                continue
            except json.JSONDecodeError:
                erro = {"erro": "JSON inválido enviado pelo cliente."}
                conn.send(json.dumps(erro).encode("utf-8"))
                log("ERROR", f"JSON inválido recebido: {dados_brutos!r}", addr)
                continue

            try:
                diagnostico = classificar_dados(dados)

                if diagnostico == "FALHA":
                    with lock_alertas:
                        alertas_totais += 1
                        total_atual = alertas_totais
                else:
                    with lock_alertas:
                        total_atual = alertas_totais

                resposta = {
                    "robot_id": dados.get("robot_id", "desconhecido"),
                    "diagnostico": diagnostico,
                    "alertas_totais": total_atual,
                    "status": "ok"
                }

                conn.send(json.dumps(resposta).encode("utf-8"))

                log(
                    "ALERT" if diagnostico == "FALHA" else "INFO",
                    f"Dados={dados} | Diagnóstico={diagnostico} | Alertas={total_atual}",
                    addr
                )

            except KeyError as e:
                erro = {"erro": str(e), "status": "bad_request"}
                conn.send(json.dumps(erro).encode("utf-8"))
                log("ERROR", f"Campo ausente: {e}", addr)

            except ValueError as e:
                erro = {"erro": f"Valor inválido: {e}", "status": "bad_request"}
                conn.send(json.dumps(erro).encode("utf-8"))
                log("ERROR", f"Erro de conversão: {e}", addr)

            except Exception as e:
                erro = {"erro": "Falha interna na inferência.", "status": "server_error"}
                conn.send(json.dumps(erro).encode("utf-8"))
                log("ERROR", f"Erro interno durante inferência: {e}", addr)

    except ConnectionResetError:
        log("WARN", "Conexão resetada pelo cliente.", addr)

    except Exception as e:
        log("ERROR", f"Erro inesperado na thread do cliente: {e}", addr)

    finally:
        conn.close()
        log("INFO", "Conexão encerrada.", addr)


def iniciar_servidor():
    global modelo

    try:
        log("INFO", "Verificando arquivo do modelo...")
        modelo = verificar_modelo(MODEL_PATH)
        log("INFO", f"Modelo carregado com sucesso: {MODEL_PATH}")

        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PORT))
        servidor.listen()

        log("INFO", f"Servidor escutando em {HOST}:{PORT}")

        while True:
            conn, addr = servidor.accept()
            thread = threading.Thread(target=tratar_cliente, args=(conn, addr), daemon=True)
            thread.start()
            log("INFO", f"Thread iniciada. Threads ativas: {threading.active_count() - 1}")

    except KeyboardInterrupt:
        log("WARN", "Servidor interrompido manualmente.")

    except Exception as e:
        log("ERROR", f"Falha ao iniciar o servidor: {e}")


if __name__ == "__main__":
    iniciar_servidor()
