#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 17 13:30:14 2022
@author: mat
"""
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

