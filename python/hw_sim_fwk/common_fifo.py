import os
import logging
from inspect import currentframe
import win32pipe
import win32file
import configuration

cf = currentframe()


# create a fifo (named pipe) for writing,
# connection is done in a loop without blocking,
# calling module then changes to non-blocking for write operations
def create_w_fifo(file_name, event_close):
    fifo_w = None
    if os.path.exists(file_name) is False:
        try:
            logging.info("server, create write named_pipe = " + file_name)
            fifo_w = win32pipe.CreateNamedPipe(
                file_name,
                win32pipe.PIPE_ACCESS_OUTBOUND,
                # the pipe treats the bytes written during each write operation as a message:
                # win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_NOWAIT,
                # pipe as a stream of bytes:
                win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_NOWAIT,
                1, configuration.FIFO_WRITE_BUFFER_SIZE, configuration.FIFO_READ_BUFFER_SIZE,
                win32pipe.NMPWAIT_NOWAIT,
                None)
        except Exception as e:
            logging.error("server, could not create pipe for " + file_name + ", exception: " + str(e))
            exit(cf.f_lineno)
    # open fifo (named pipe)
    connected = False
    logging.info("server, waiting for client")
    while (connected is False) and (event_close.is_set() is False):
        try:
            connected = win32pipe.ConnectNamedPipe(fifo_w, None)
            logging.info("server, got client")
        except Exception as e:
            logging.debug(str(e))
    # return value
    return fifo_w


# create a fifo (named pipe) for reading,
# connection is done in a blocking wait
def create_r_fifo(file_name, event_close):
    fifo_r = None
    try:
        logging.info("client, create read named_pipe = " + file_name)
        fifo_r = win32pipe.CreateNamedPipe(
            file_name,
            win32pipe.PIPE_ACCESS_INBOUND,
            # the pipe treats the bytes written during each write operation as a message:
            # win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            # pipe as stream of bytes:
            win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
            1, configuration.FIFO_WRITE_BUFFER_SIZE, configuration.FIFO_READ_BUFFER_SIZE,
            win32pipe.NMPWAIT_NOWAIT,
            None)
    except Exception as e:
        logging.error("client, exception: " + str(e))
        exit(cf.f_lineno)
    # open fifo (named pipe)
    if event_close.is_set() is False:
        try:
            logging.info("client, waiting for server for " + file_name)
            win32pipe.ConnectNamedPipe(fifo_r, None)
            logging.info("client, got server for " + file_name + " with handle/fifo = " + str(fifo_r))
        except Exception as e:
            logging.error("client, could not connect to pipe of " + file_name + ", exception: " + str(e))
            win32file.CloseHandle(fifo_r)
            exit(cf.f_lineno)
    # return value
    return fifo_r
