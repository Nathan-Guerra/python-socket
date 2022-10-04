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
    ELA PRECISA SER A MESMA PORTA DO ARQUIVO server.py PORQUE É POR ELA QUE ENVIAMOS O CONTEÚDO
"""
PORT = 8000

"""
    MANTENDO O MONITORAMENTO DOS SOCKETS UTILIZANDO O sel
    OLHAR NO ARQUIVO REFERENCES.md
"""
sel = selectors.DefaultSelector()
"""
    MENSAGENS QUE ESTAMOS ENVIANDO A PARTIR DO NOSSO SOCKET
    ELAS FICAM VISIVEIS NO LADO DO SERVIDOR
"""
messages = [b"Message 1 from client.", b"Message 2 from client."]

"""
    FUNÇÃO PARA INICIAR OS NOSSOS SOCKETS
    host = URL EM QUE VAMOS NOS CONECTAR
    port = PORTA DO HOST QUE VAMOS ACESSAR
    num_conns = NÚMERO DE CONEXÕES QUE VAMOS CRIAR
"""
def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print(f"Starting connection {connid} to {server_addr}")
        """
            PARA CONECTAR AO SOCKET, VAMOS UTILIZAR O PROTOCOLO TCP COM IPV4
            PRA ISSO UTILIZAMOS OS VALORES
            AF_INET = SINALIZA QUE VAMOS UTILIZAR O IPv4
            SOCK_STREAM = PROTOCOLO TCP
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # blocking igual a False pra podermos criar mais de um socket ao mesmo tempo
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        """
            INDICA EM QUE MOMENTO ESTAMOS. CASO O EVENT_READ SEJA TRUE, LEMOS A MENSAGEM
            CASO CONTRARIO, COLOCAMOS ELA NO BUFFER DE OUTPUT ATÉ ESTAR FINALIZADA PARA PODERMOS LER QUANDO ESTIVER PRONTA
        """
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        """
            SALVAMOS O NOSSO CONTEÚDO EM UM SimpleNamespace PORQUE ELE CONSEGUE GUARDAR AS INFORMAÇÕES CORRETAMENTE
            E NÃO PRECISAMOS CRIAR NENHUMA CLASSE EXTRA
        """
        data = types.SimpleNamespace(
            connid=connid,
            msg_total=sum(len(m) for m in messages),
            recv_total=0,
            messages=messages.copy(),
            outb=b"",
        )
        """
            REGISTRAMOS O SOCKET NO DefaultSelector PARA QUE ELE SEJA MONITORADO
        """
        sel.register(sock, events, data=data)

"""
    CONEXÃO DO SOCKET
    key = CADA ÍNDICE DO DefaultSelector
    mask = https://en.wikipedia.org/wiki/Mask_(computing)
"""
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data

    # verifica se estamos no evento de escrita
    if mask & selectors.EVENT_WRITE:
        # se temos mensagens disponíveis, pega a primeira da lista
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        # se a mensagem não estiver vazia, enviamos ela para o socket e incrementamos o buffer de output para ser lida posteriormente.
        if data.outb:
            print(f"Sending {data.outb!r} to connection {data.connid}")
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

    # verifica se estamos no evento de leitura
    if mask & selectors.EVENT_READ:
        # conteúdo do socket
        recv_data = sock.recv(1024)
        if recv_data:
            print(f"Received {recv_data!r} from connection {data.connid}")
            # incrementamos a quantidade de bytes recebidos no data.recv_total
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection {data.connid}")
            # se não há mais bytes a ser recebido remove o socket do listener e fecha a conexão
            sel.unregister(sock)
            sock.close()
    

# cria as conexões
start_connections(HOST, PORT, 2)

try:
    while True:
        # recupera todos os eventos criados
        events = sel.select(timeout=1)
        if events:
            for key, mask in events:
                # faz o envio de todos os eventos
                service_connection(key, mask)
        # quando todos os sockets monitorados enviarem as mensagens o listener fica vazio e saímos do while.
        if not sel.get_map():
            break
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    # fecha o DefaultSelector corretamente antes de finalizar o programa
    sel.close()
