#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 13:30:14 2022
@author: mat
"""
##SERVIDOR##

from multiprocessing.connection import Listener
from multiprocessing import Process, Manager
from multiprocessing.connection import Client
import sys
from time import time
import traceback

# client_info = {'name','address','authkey','port'}
# database = [{'name'}]

def send_msg_all(msg,database):
    
    for info in database:
        with Client(address=(info['address'],info['port']),authkey=info['authkey']) as conn:
            conn.send(msg)


def manage(conn,lock,database):
    
    while True:
        try:
            client_msg = conn.recv()
            request,client_info = client_msg['request'], client_msg['info']
            if request == '__join__':
                if client_info['name'] in [t['name'] for t in database]:
                    conn.send('Nickname used, choose another')
                else:
                    send_msg_all(f'New user online <{client_info["name"]}>',database)
                    database.append(client_info)
                    print(f'client {client_info["name"]} is now online')
                    conn.send('conectado')
                    
            elif request == '__quit__':
                print(f'client {client_info["name"]} is offline')
                send_msg_all(f'User <{client_info["name"]}> has disconnected',database)
                break
            
            elif request == '__refresh__':
                print(f'Sending connected users to {client_info["name"]}')
                nicknames = [t['name'] for t in database if t['name'] != client_info['name']]
                conn.send(nicknames)
            
            elif request == '__talk__':
                name = client_msg['user']
                for t in database:
                    if t['name'] == name:
                        print(f'Retreiving <{name}> info; requested by <{client_info["name"]}>')
                        conn.send(t)
                        break
                    elif t == database[-1]:
                        conn.send('That user was not found')      
            elif request == '__talkall__':
                temp = [t for t in database if t['name'] != client_info['name']]
                conn.send(temp)
            else:
                print(request)                      
        except:
            print(f'client {client_info["name"]} apparently crashed')
            send_msg_all(f'User <{client_info["name"]}> apparently crashed',database)
            break
        
    database.remove(client_info)
    conn.close()
    print(f'client {client_info["name"]} removed from database')
    

if __name__ == '__main__':
    
    ip_address ='127.0.0.1'
    server_port = 6000
    if len(sys .argv)>1:
        ip_address = sys.argv[1]
        
    with Listener(address=(ip_address, server_port),authkey=b'secret password server') as listener:
        print('listener starting')  
        m = Manager()
        database = m.list()
        lock = m.Lock()
        
        while True:
            try:
                conn = listener.accept()
                print ('connection accepted from', listener.last_accepted)
                p = Process(target=manage, args=(conn,lock,database))
                p.start()
            except KeyboardInterrupt:
                print('\nInterrupt request by administrator\nServer terminated')
                break
            except:
                print('\nServer crashed\nHeres the crash report: ')
                traceback.print_exc()
                


###CLIENTE###
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 14:01:43 2022
@author: mat
"""
from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Lock
from multiprocessing.connection import Client
import sys
from time import time
import traceback

# client_info = {'name','address','authkey','port'}
        

def client_listener(info):
    
        cl = Listener(address=(info['address'],info['port']),
                             authkey=info['authkey'])
        print('listener starting')
        while True:
            conn = cl.accept()
            m=conn.recv()
            if m == 'Speaker no longer is speaking to you':
                conn.close()
                print(m)
            else:
                print('message received:', m)
            
            

if __name__ == '__main__':
    
    server_address = '127.0.0.1'
    server_port = 6000
    port = 6001
    authkey=b'secret client server'
    if len(sys .argv)>1:
        server_address = sys.argv[1]
    if len(sys .argv)>2:
        port = int(sys.argv[2])
    
    name = input('Your name to use: ')
    address = input('Your ip_address: ')   
    client_info = {'name':name,'address':address,'authkey':authkey,'port':port}  
    
    with Client(address=(server_address, server_port),authkey=b'secret password server') as conn:
        
        temp={'address':address,'authkey':authkey,'port':port} 
        
        cl = Process(target=client_listener, args =(temp,))
        cl.start()
        
        to_server = {'request':'__join__','info':client_info}   
        conn.send(to_server)
        answer = conn.recv()      
        while answer == 'Nickname used, choose another':
            m = input('That nickname is already in use, choose another: ')
            to_server['info']['name'] = m
            conn.send(to_server)
            answer = conn.recv()

        while True:
            msg = input('enter (__help__ for command menu): ')
            if msg == '__help__':
                print('Commands for server interaction: \n__help__       prints this message'\
                      '\n__refresh__    returns currently online users'\
                      '\n__quit__       exits online chat'\
                      '\n__talk__       enters user to user interface')
            elif msg == "__quit__":
                to_server['request'] = msg
                conn.send(to_server)
                break
            elif msg == '__refresh__':
                to_server['request'] = msg
                conn.send(to_server)
                print(conn.recv())
            elif msg == '__talk__':
                to_server['request'] = '__refresh__'
                conn.send(to_server)
                print('Currently online: ',conn.recv()) #primero muestra un __refresh__               
                to_server['request'] = msg
                name = input('Enter nickname: ')
                to_server['user'] = name
                conn.send(to_server)
                other_client = conn.recv()
                if other_client == 'That user was not found':
                    print(other_client)
                    continue
                else:
                    while True:
                        with Client(address=(other_client['address'], other_client['port']),authkey=other_client['authkey']) as conn_2:
                            msg = input(f'Message {other_client["name"]}: ')
                            if msg == '__quit__':
                                conn_2.send('Speaker has quit the conversation')
                                break
                            conn_2.send(msg)
                            
            elif msg == '__talkall__':
                to_server['request'] = '__talkall__'
                conn.send(to_server)
                users = conn.recv()
                message = input('Enter message to all: ')
                for user in users:
                    with Client(address=(user['address'], user['port']),authkey=user['authkey']) as conn_2:
                        conn_2.send(msg)
                    
        cl.terminate()
        print('client exited')
