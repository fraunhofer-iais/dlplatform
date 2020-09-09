from DLplatform.parameters import Parameters
from DLplatform.communicating import Communicator

from typing import List
import pika
import pickle
import sys
import threading

class RabbitMQComm(Communicator):
    '''
    Class incapsulating all the methods for sending
    and receiving messages in the distributed system
    The only connection to the communication server (RabbitMQ) is 
    hold here.

    best practices for RabbitMQ https://www.cloudamqp.com/blog/2017-12-29-part1-rabbitmq-best-practice.html
    main rules:
        - one connection per process, one channel per thread
        - different connections for publishing and consuming
        - acknowledgements, durable queues and persistent messages in order not to loose messages 
            (though it might lead to slower performance)
    '''

    def __init__(self, hostname: str, port: int, user : str, password : str, uniqueId : str, name = "RabbitMQComm"):
        '''
        Initializes the BaseClass with name RabbitMQComm
        Also sets up parameters needed for connecting to the 
        communication server. Also initializes the thread that 
        later will be used for running a messages queue consuming.
        In order to follow the best practice two connections are used in 
        the class - for publishing and for consuming. Since publishing does 
        not require separate thread the connection is established in the 
        initializer and later on is used in all the publishing messages methods.
        Exchanges for nodes and coordinator are hardcoded with names "nodes" and
        "coordinator"

        Parameters
        ----------
        hostname of the communication server
        port on which the connection to the communicator server should be performed
        user and password to connect to RabbitMQ on the host
        '''

        Communicator.__init__(self, name = name)

        self._port                      = port # 5672 is default
        self._hostname                  = hostname # 'localhost' as the simplest
        self._user                      = user
        self._password                  = password
        # we use uniqueId in order to allow running several experiments on one and the same
        # rabbitMQ instance - the messages would not be mixed up then, because channels
        # have this uniqueId, that is the PID of the experiment process
        self._exchangeCoordinator       = 'coordinator' + uniqueId
        self._exchangeNodes             = 'nodes' + uniqueId
        self._threads                   = []
        self._setupPublishConnection()

    '''
    When using multiprocessing, the communicator is serialized using pickle (in windows, not so under linux). 
    However, the connection cannot be pickled, since it contains a thread.lock object.
    To avoid this, we implemented the following two functions which govern the behavior of pickle.
    In here, the connection object is disregarded and reopened in the child process, later.
    '''

    def __getstate__(self):
        d = self.__dict__.copy()
        if '_publishConnection' in d:
            d['_publishConnection'] = "reconnect_required"
        if '_publishChannel' in d:
            d['_publishChannel'] = "reconnect_required"
        return d

    def __setstate__(self, d):
        if '_publishConnection' in d and d['_publishConnection'] == "reconnect_required":
            credentials = pika.PlainCredentials(d['_user'], d['_password'])
            d['_publishConnection'] = pika.BlockingConnection(pika.ConnectionParameters(host=d['_hostname'],
                                        port=d['_port'], credentials=credentials, blocked_connection_timeout=None,
                                        socket_timeout=None, heartbeat=0))
            d['_publishChannel'] = d['_publishConnection'].channel()
            d['_publishChannel'].exchange_declare(exchange=d['_exchangeCoordinator'], exchange_type='topic')
            d['_publishChannel'].exchange_declare(exchange=d['_exchangeNodes'], exchange_type='topic')
        self.__dict__.update(d)

    def initiate(self, exchange : str, topics : List[str]):
        '''
        Sets the needed exchange name and topics to listen to.
        For worker it is Nodes exchange and topics with its id
        For coordinator it is Coordinator exchange and topics such as "registration"

        Parameters
        ----------
        exchange to consume
        topics to consume
        '''
        self._exchange = exchange
        self._topics = topics

    def connect(self) -> pika.BlockingConnection:
        '''
        Performs connection to the communication server
        All the parameters of a server are set up in the initializer.

        Returns
        -------
        connection to the server
        '''

        credentials = pika.PlainCredentials(self._user, self._password)
        return pika.BlockingConnection(pika.ConnectionParameters(host = self._hostname,
                    port = self._port, credentials = credentials, blocked_connection_timeout = None,
                    socket_timeout = None, heartbeat = 0))

    def _setupPublishConnection(self):
        '''
        Creates a connection to RabbitMQ server for publishing
        Declares to exchanges: for Nodes and Coordinator, each instance of communicator
        will know, which of the exchanges should be used for publishing
        '''
        self._publishConnection         = self.connect()
        self._publishChannel            = self._publishConnection.channel()

        self._publishChannel.exchange_declare(exchange=self._exchangeCoordinator, exchange_type='topic')
        self._publishChannel.exchange_declare(exchange=self._exchangeNodes, exchange_type='topic')

    def _setupConsumeConnection(self):
        '''
        Setups a separate connection to RabbitMQ server for consumption of messages.
        Each instance of communicator consumes only from the needed exchange and only needed topics
        So workers would only consume from Nodes exchange topics that have their id
        Coordinator will consume only topics "violation", "registration", etc. from Coordinator exchange
        When message is received it is directly pushed into interProcess communication (via _onMessageReceived) and
        acknowledgement sent automatically, so RabbitMQ is never stuck waiting for response
        '''
        self._consumeConnection = self.connect()
        channel = self._consumeConnection.channel()
        queue = channel.queue_declare(exclusive=True, queue='').method.queue

        for topic in self._topics:
            channel.queue_bind(exchange=self._exchange, queue=queue, routing_key=topic)

        # does not allow to stack more than 1 message in prefetch, helps to make the communication lighter
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_message_callback=self._onMessageReceived, queue=queue, auto_ack=True)
        return channel

    def _publish(self, exchange, topic, message):
        '''
        Publishes a message to the exchange (Nodes for workers and Coordinator for coordinator) with
        a needed topic, e.g., "violation" or "newModel.0.1"
        '''
        try:
            self._publishChannel.basic_publish(exchange=exchange, routing_key=topic, body=message)
        except pika.exceptions.ConnectionClosed:
            # should actually never happen if everything is working smoothly
            print("Pika connection to RabbitMQ server was closed!")
            self._setupPublishConnection()
            self._publishChannel.basic_publish(exchange=exchange, routing_key=topic, body=message)

    def sendViolation(self, identifier : str, param : Parameters):
        '''
        Publish message about violation
        Called from a worker with violation and published to coordinator
        exchange with topic violation. Message is pickled dictionary of 
        the form {'id': identifier, 'param': param}

        Parameters
        ----------
        identifier of a worker with violation
        param - parameters of the worker that sends the violation

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case that param is not of type Parameters
            in case identifier is not a string
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type" + str(str) + "it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        if not isinstance(param, Parameters):
            error_text = "The argument param is not of type" + str(Parameters) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        message = pickle.dumps({'id' : identifier, 'param' : param})
        message_size = sys.getsizeof(message)
        topic = 'violation'
        self._publish(self._exchangeCoordinator, topic, message)
        self.info("Sent violation message to coordinator")
        self.learningLogger.logViolationMessage(self._exchangeCoordinator, topic, identifier, message_size, 'send')

    def sendRegistration(self, identifier : str, param : Parameters):
        '''
        Publish message that will register a new node on coordinator
        Called from a newly connected worker and published to coordinator
        exchange with topic registration. Message is pickled dictionary of 
        the form {'id': identifier}. Supposed to be answered from coordinator 
        with a message containng current averaged model.

        Parameters
        ----------
        identifier of a new worker

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case identifier is not a string
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type" + str(str) + "it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'registration'
        message = pickle.dumps({'id' : identifier, 'param' : param})
        message_size = sys.getsizeof(message)
        self._publish(self._exchangeCoordinator, topic, message)
        self.learningLogger.logRegistrationMessage(self._exchangeCoordinator, topic, identifier, message_size, 'send')

    def sendDeregistration(self, identifier : str, param : Parameters):
        '''
        When a node finished according to the stopping criterion,
        it send the deregistration message to coordinator
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type 'string' it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        if not isinstance(param, Parameters):
            error_text = "The argument param is not of type 'Parameters' it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'deregistration'
        message = pickle.dumps({'id' : identifier, 'param' : param})
        message_size = sys.getsizeof(message)
        self._publish(self._exchangeCoordinator, topic, message)
        self.learningLogger.logRegistrationMessage(self._exchangeCoordinator, topic, identifier, message_size, 'send')

    def sendParameters(self, identifier : str, param : Parameters):
        '''
        Publish message with parametres
        Called from a worker that was requested for its parameters
        while balancing process and published to coordinator
        exchange with topic balancing. Message is pickled dictionary of 
        the form {'id': identifier, 'param': param}

        Parameters
        ----------
        identifier of a worker sending its parameters
        param - parameters of the worker

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case that param is not of type Parameters
            in case identifier is not a string
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type" + str(str) + "it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        if not isinstance(param, Parameters):
            error_text = "The argument param is not of type" + str(Parameters) + "it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'balancing'
        message = pickle.dumps({'id' : identifier, 'param' : param})
        message_size = sys.getsizeof(message)
        self._publish(self._exchangeCoordinator, topic, message)
        self.learningLogger.logBalancingMessage(self._exchangeCoordinator, topic, identifier, message_size, 'send')

    def sendBalancingRequest(self, identifier : str):
        '''
        Publish message to query the worker for its current parameters
        Called from coordinator while balancing process and published to nodes
        exchange with topic identifier of the worker and 'request'. Message is empty.

        Parameters
        ----------
        identifier of a worker requested for its parameters

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case identifier is not a string
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type" + str(str) + "it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'request.' + identifier
        # since it is just a request nothing should be sent in a message
        message_size = 0
        self._publish(self._exchangeNodes, topic, '')
        self.learningLogger.logBalancingRequestMessage(self._exchangeNodes, topic, identifier, message_size, 'send')

    def sendExitRequest(self, identifier : str):
        '''
        Publish message to ask the worker to finish its process
        Called from coordinator when not enough workers are left
        with topic identifier of the worker and 'exit'. Message is empty.

        Parameters
        ----------
        identifier of a worker requested to finish execution

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case identifier is not a string
        '''
        if not isinstance(identifier, str):
            error_text = "The argument identifier is not of type" + str(str) + "it is of type " + str(type(identifier))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'exit.' + identifier
        # since it is just a request nothing should be sent in a message
        message_size = 0
        self._publish(self._exchangeNodes, topic, '')

    def sendAveragedModel(self, identifiers : List[str], param : Parameters, flags: dict):
        '''
        Publish message to send an averaged model to the nodes
        Called from coordinator after balancing process and published to nodes
        exchange with topic identifiers of the workers that took part in 
        balancing process and 'newModel'. This message is also used as an 
        answer to a registration request. In case when it was full synchronization setReference is 
        set to True and then the workers will also update the referenceModel. Message is 
        pickled dictionary of form {'param': param, 'ref': setReference}.

        Parameters
        ----------
        identifiers of workers to receive the averaged model
        param - parameters of the averaged model
        setReference - boolean value that defines if the reference model should be updated

        Returns
        -------
        None

        Exception
        -------
        ValueError
            in case identifiers is not a list
            in case param is not Parameters
            in case setReference is not bool value
        '''
        if not isinstance(identifiers, List):
            error_text = "The argument identifier is not of type " + str(List) + " it is of type " + str(type(identifiers))
            self.error(error_text)
            raise ValueError(error_text)

        if not isinstance(param, Parameters):
            error_text = "The argument param is not of type " + str(Parameters) + " it is of type " + str(type(param))
            self.error(error_text)
            raise ValueError(error_text)

        if not isinstance(flags, dict):
            error_text = "The argument setReference is not of type " + str(dict) + " it is of type " + str(type(flags))
            self.error(error_text)
            raise ValueError(error_text)

        topic = 'newModel.' + '.'.join(identifiers)
        message = pickle.dumps({'param' : param, 'flags' : flags})
        message_size = sys.getsizeof(message)
        self._publish(self._exchangeNodes, topic, message)
        self.learningLogger.logSendModelMessage(self._exchangeNodes, topic, message_size, 'send')

    def setPort(self, port: int) :
        '''
        Setter for the port of the communication server

        Parameters
        ----------
        port

        Returns
        -------
        None

        Exceptions
        ----------
        ValueError
            in case port is not integer
        '''

        if not isinstance(port, int):
            error_text = "The attribute port is of type " + str(type(port)) + " and not of type" + str(int)
            self.error(error_text)
            raise ValueError(error_text)

        self._port = port

    def setHostName(self, hostname: str):
        '''
        Setter for the hostname of communication server

        Parameters
        ----------
        hostname

        Returns
        -------
        None

        Exceptions
        ----------
        ValueError
            in case the hostname is not a string
        '''

        if not isinstance(hostname, str):
            error_text = "The attribute hostname is of type " + str(type(hostname)) + " and not of type" + str(str)
            self.error(error_text)
            raise ValueError(error_text)

        self._hostname = hostname

    def getPort(self) -> int:
        '''
        Getter for port of the communication server

        Returns
        -------
        port
        '''

        return self._port

    def getHostName(self) -> str:
        '''
        Getter for hostname of the communication server

        Returns
        -------
        hostname
        '''

        return self._hostname

    def run(self):
        '''
        Method that is run as target of the thread with communicator
        Opens a connection to the communication server and starts an 
        endless loop that is consuming the queue of messages. The callback 
        is the onMessageReceived that is set up before. Subscription is made 
        on particular exchange and particular topics.

        Returns
        -------
        None

        '''

        # run Process parent class
        super().run()

        channel = self._setupConsumeConnection()
        try:
            channel.start_consuming()
        except pika.exceptions.ConnectionClosed:
            # should actually never happen if everything is working smoothly
            print("Pika connection to RabbitMQ server was closed!")
        except KeyboardInterrupt:
            channel.stop_consuming()

        self._publishConnection.close()
        self._consumeConnection.close()
