
import socket
import json
import time
import random
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000
INTERVALO_ENVIO = 2

robot_id = input("Digite o ID do robô: ").strip() or "robot_01"


def log(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [{robot_id}] {message}")


def gerar_dados():
    return {
        "robot_id": robot_id,
        "temperatura": round(random.uniform(35.0, 90.0), 2),
        "vibracao": round(random.uniform(0.2, 2.0), 2),
        "rpm": random.randint(800, 1800)
    }


def conectar():
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.settimeout(5)
    cliente.connect((HOST, PORT))
    return cliente


def executar_cliente():
    cliente = None

    while True:
        try:
            if cliente is None:
                log("INFO", f"Tentando conectar ao servidor em {HOST}:{PORT}...")
                cliente = conectar()
                log("INFO", "Conexão estabelecida com sucesso.")

            dados = gerar_dados()
            mensagem = json.dumps(dados)

            cliente.send(mensagem.encode("utf-8"))
            log("SEND", f"Dados enviados: {dados}")

            resposta_bruta = cliente.recv(1024)
            if not resposta_bruta:
                log("WARN", "Servidor fechou a conexão.")
                cliente.close()
                cliente = None
                time.sleep(2)
                continue

            try:
                resposta = json.loads(resposta_bruta.decode("utf-8"))
            except json.JSONDecodeError:
                log("ERROR", f"Resposta inválida do servidor: {resposta_bruta!r}")
                time.sleep(INTERVALO_ENVIO)
                continue

            if "erro" in resposta:
                log("ERROR", f"Erro retornado pelo servidor: {resposta}")
            else:
                diagnostico = resposta.get("diagnostico", "desconhecido")
                total_alertas = resposta.get("alertas_totais", "N/A")
                nivel = "ALERT" if diagnostico == "FALHA" else "INFO"
                log(nivel, f"Diagnóstico={diagnostico} | Alertas Totais={total_alertas}")

            print("-" * 70)
            time.sleep(INTERVALO_ENVIO)

        except socket.timeout:
            log("WARN", "Timeout na comunicação com o servidor. Tentando novamente...")
            if cliente:
                cliente.close()
            cliente = None
            time.sleep(2)

        except ConnectionRefusedError:
            log("ERROR", "Conexão recusada. Verifique se o servidor está rodando.")
            if cliente:
                cliente.close()
            cliente = None
            time.sleep(3)

        except ConnectionResetError:
            log("WARN", "Conexão resetada pelo servidor. Reconectando...")
            if cliente:
                cliente.close()
            cliente = None
            time.sleep(2)

        except KeyboardInterrupt:
            log("INFO", "Cliente encerrado manualmente.")
            if cliente:
                cliente.close()
            break

        except Exception as e:
            log("ERROR", f"Erro inesperado no cliente: {e}")
            if cliente:
                cliente.close()
            cliente = None
            time.sleep(2)


if __name__ == "__main__":
    executar_cliente()
