#!/usr/bin/env python3
import amqp_connection
import json
import pika
#from os import environ

a_queue_name = 'Email_Log' # queue to be subscribed by email_log microservice

# Instead of hardcoding the values, we can also get them from the environ as shown below
# a_queue_name = environ.get('email_log') #email_log

def receiveEmailLog(channel):
    try:
        # set up a consumer and start to wait for coming messages
        channel.basic_consume(queue=a_queue_name, on_message_callback=callback, auto_ack=True)
        print('email_log: Consuming from queue:', a_queue_name)
        channel.start_consuming()  # an implicit loop waiting to receive messages;
             #it doesn't exit by default. Use Ctrl+C in the command window to terminate it.
    
    except pika.exceptions.AMQPError as e:
        print(f"email_log: Failed to connect: {e}") # might encounter error if the exchange or the queue is not created

    except KeyboardInterrupt:
        print("email_log: Program interrupted by user.") 


def callback(channel, method, properties, body): # required signature for the callback; no return
    print("\nemail_log: Received an email log by " + __file__)
    processEmailLog(json.loads(body))
    print()

def processEmailLog(email):
    print("email_log: Recording an email log:")
    print(email)

if __name__ == "__main__":  # execute this program only if it is run as a script (not by 'import')
    print("email_log: Getting Connection")
    connection = amqp_connection.create_connection() #get the connection to the broker
    print("email_log: Connection established successfully")
    channel = connection.channel()
    receiveEmailLog(channel)
