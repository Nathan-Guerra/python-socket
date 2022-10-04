import socket
import selectors
import types

"""
    NOME PADRÃO DO HOST LOCAL.
    NÃO UTILIZAMOS O NOME "localhost" PORQUE AS VEZES O DNS DA MÁQUINA CAUSA PROBLEMAS ENVIANDO OUTRO IP NO LUGAR
"""
HOST = "127.0.0.1" 
"""
    PORTA PADRÃO DO PROJETO
    ELA PRECISA SER A MESMA PORTA DO ARQUIVO client.py PORQUE É POR ELA QUE RECEBEMOS O CONTEÚDO
"""
PORT = 8000

# monitoramento dos sockets do lado do servidor 
sel = selectors.DefaultSelector()

"""
    inclui a monitoração do socket do lado do servidor
"""
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # mantém registro dos conteúdos de input e output do socket
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # registra o socket no nosso listener
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        # dados recebidos do socket
        recv_data = sock.recv(1024)
        if recv_data:
            # inclui output no buffer de resposta
            data.outb += recv_data
        else:
            # ao finalizar a leitura dos dados, removemos o socket do listener e fechamos a conexão
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        """
            se existe dados disponíveis para leitura, lemos os dados 
            como essa função roda dentro de um while, enquanto houver mensagens restantes não finalizamos o output
        """
        if data.outb:
            print(f"Echoing {data.outb!r} to {data.addr}")
            # enviamos o dado recebido de volta para o client salvando a quantidade de bytes enviadas
            sent = sock.send(data.outb)
            # gravamos no buffer somente os dados que não foram enviados
            data.outb = data.outb[sent:]


# conexão com o socket no mesmo padrão do client.py
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Listening on {(HOST, PORT)}")
    s.setblocking(False)
    # configuração padrão do servidor
    sel.register(s, selectors.EVENT_READ, data=None)
    s.bind((HOST, PORT))
    s.listen()

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                # se o data é None significa que é um novo socket então inicializamos no listener
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    # se o socket já existe fazemos o read e write até que seja finalizado
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

