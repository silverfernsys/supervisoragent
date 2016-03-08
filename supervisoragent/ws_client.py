#! /usr/bin/env python
import websocket
import thread
import time

class WSHandler(object):
  @classmethod
  def on_message(self, ws, message):
      print message

  @classmethod
  def on_error(self, ws, error):
      print error

  @classmethod
  def on_close(self, ws):
      print "### closed ###"

  @classmethod
  def on_open(self, ws):
      def run(*args):
          for i in range(3):
              time.sleep(1)
              ws.send("Hello %d" % i)
          time.sleep(1)
          ws.close()
          print "thread terminating..."
      thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    # url = "ws://10.0.0.10:8081/agent/"
    # header=["authorization: f5bd7592b40d9dff08e9dc668818414572946146"]
    url = "ws://10.0.0.10:8081/user/"
    header=["authorization: bd190a983abf2f1dfab3d7b80f595eb322e9ff76"]
    ws = websocket.WebSocketApp(url,
                              header=header,
                              on_message = WSHandler.on_message,
                              on_error = WSHandler.on_error,
                              on_close = WSHandler.on_close,
                              on_open = WSHandler.on_open)
    ws.run_forever()