import socket

# [EN] HOST defines where the client will connect.
#      127.0.0.1 means localhost: server and client on the same machine (local TCP test).
# [PT-BR] HOST define para onde o cliente vai se conectar.
#         127.0.0.1 significa localhost: servidor e cliente na mesma máquina (teste TCP local).
HOST = "127.0.0.1"
PORT = 5000


def main() -> None:
    """Start a TCP client, send user commands and print server responses."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print(f"Conectado ao servidor em {HOST}:{PORT}")

        # [EN] Before running the TCP tests, we can check local connectivity with:
        #      ping localhost
        #      ping 127.0.0.1
        # [PT-BR] Antes dos testes de TCP, podemos verificar a conectividade local com:
        #         ping localhost
        #         ping 127.0.0.1

        while True:
            msg = input(
                "Digite a mensagem ('cadastro', 'listar bots', "
                "dados do modelo ou 'sair'): "
            )
            client.sendall(msg.encode())

            if msg.lower() == "sair":
                print("Encerrando cliente.")
                break

            response = client.recv(4096).decode()
            print("\nResposta do servidor:")
            print(response)
            print()


if __name__ == "__main__":
    main()