# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 17:13:19 2018

@author: ladilova
"""
## Input stream
import pika
import time

# send a message on localhost RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='inputs')
for i in range(100):
    channel.basic_publish(exchange='', routing_key='inputs', body='input image')
    time.sleep(10)
connection.close()

## Coordinator
import pika
import threading
import time

class Coordinator():
    def __init__(self):
        self.violations = []
        self.state = 'idle'
        self.nodes_list = ['42']
        self.balance_set = {}
        thread = threading.Thread(target=self.consume_violations)
        thread.setDaemon(True)
        thread.start()
        thread = threading.Thread(target=self.consume_balancing)
        thread.setDaemon(True)
        thread.start()
        
    def balancing_callback(self, ch, method, properties, body):
        print('got a model for balancing\n')
        self.balance_set[body.decode('ascii').split()[-1]] = body
        
    def consume_balancing(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='balancing')
        channel.basic_consume(self.balancing_callback, queue='balancing', no_ack=True)
        channel.start_consuming()
        
    def violations_callback(self, ch, method, properties, body):
        print('got a violation message\n')
        self.violations.append(body)
        print('now coordinator has ' + str(len(self.violations)) + ' violations\n')
        
    def consume_violations(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='violations')
        channel.basic_consume(self.violations_callback, queue='violations', no_ack=True)
        channel.start_consuming()
        
    def send_balancing_request(self, node_id):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=node_id)
        channel.basic_publish(exchange='', routing_key=node_id, body='request')
        print("Sent request to the node " + node_id)
        connection.close()
        
    def send_averaged_model(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        for node_id in self.nodes_list:
            channel.queue_declare(queue=node_id)
            channel.basic_publish(exchange='', routing_key=node_id, body='average')
        connection.close()
        
c = Coordinator()
while True:
    if len(c.violations) > 0:
        c.state = 'balancing'
        violation = c.violations[0]
        del(c.violations[0])
        print('performing balancing process...')
        balance_set_keys = ['42']
        for node_id in balance_set_keys:
            c.send_balancing_request(node_id)
        while not set(c.balance_set.keys()) == set(balance_set_keys):
            time.sleep(5)
        print('balancing done!')
        c.send_averaged_model()
        c.state = 'idle'
        c.balance_set = {}
        
## Node
import pika
import threading
import time
import random

class Node():
    def __init__(self, identifier):
        self.requests = 0
        self.id = identifier
        self.averaged_model = None
        self.inputs = []
        thread = threading.Thread(target=self.consume_node_queue)
        thread.setDaemon(True)
        thread.start()
        thread = threading.Thread(target=self.consume_inputs)
        thread.setDaemon(True)
        thread.start()
        
    def node_queue_callback(self, ch, method, properties, body):
        if 'request' in str(body):
            print('got a request\n')
            self.requests += 1
            print('now the node ' + self.id + ' has ' + str(self.requests) + ' requests\n')
        if 'average' in str(body):
            print('got an averaged model, should check if the reference model should be changed as well\n')
            self.averaged_model = body
        
    def consume_node_queue(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=self.id)
        channel.basic_consume(self.node_queue_callback, queue=self.id, no_ack=True)
        channel.start_consuming()
    
    def inputs_callback(self, ch, method, properties, body):
        print('got input\n')
        self.inputs.append(body)
        
    def consume_inputs(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='inputs')
        channel.basic_consume(self.inputs_callback, queue='inputs', no_ack=True)
        channel.start_consuming()
    
    def answer_balancing_request(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='balancing')
        channel.basic_publish(exchange='', routing_key='balancing', body='Weights of node ' + self.id)
        print("Sent weights to coordinator")
        connection.close()
        self.requests -= 1
        
    def send_violation(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='violations')
        channel.basic_publish(exchange='', routing_key='violations', body='Weights of node ' + self.id)
        print("Sent violation to coordinator")
        connection.close()
                
n = Node('42')
while True:
    if len(n.inputs) > 0:
        print('training process...')
        time.sleep(5)
        print('check if we have requests for the weights')
        if n.requests > 0:
            n.answer_balancing_request()
        print('check if local condition is violated')
        if random.random() > 0.5:
            n.send_violation()
        print('check if we got an averaged model')
        if not n.averaged_model == None:
            print('set new weights received from coordinator')
            n.averaged_model = None
        del(n.inputs[0])
        