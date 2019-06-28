'''
created on 19.04.2018

author twirtz
'''

from multiprocessing import Queue
import random
import threading
import time

def main_thread():
    """Our main loop in the main thread.

    It receives the values via a Queue instance which it passes on to the
    other threads on thread start-up.
    """


    queue = Queue()

    thread = threading.Thread(target=run_in_other_thread,
                              args=(queue,))
    thread.daemon = True  # so you can quit the demo program easily :)
    thread.start()

    while True:
         val = queue.get()
         print("from main-thread", val)

def run_in_other_thread(queue):
    """Our worker thread.

    It passes it's generated values on the the main-thread by just
    putting them into the `Queue` instance it got on start-up.
    """
    while True:
         queue.put(random.random())
         time.sleep(1)

if __name__ == '__main__':
    main_thread()