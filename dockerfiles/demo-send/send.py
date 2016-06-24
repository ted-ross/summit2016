#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import os
from proton import Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

class Timer(object):
    def __init__(self, parent):
        self.parent = parent

    def on_timer_task(self, event):
        self.parent.tick()


class Send(MessagingHandler):
    def __init__(self, url, rate):
        super(Send, self).__init__(prefetch=10)
        self.url = url
        self.rate = rate
        self.send_count = 0
        self.sent = 0

    def on_start(self, event):
        self.sender  = event.container.create_sender(self.url)
        self.reactor = event.reactor
        self.timer   = self.reactor.schedule(0.5, Timer(self))

    def on_sendable(self, event):
        self.send()

    def send(self):
        to_send = self.send_count
        if self.sender.credit < self.send_count:
            to_send = self.sender.credit
        self.send_count -= to_send
        for i in range(to_send):
            m = Message(body="Sequence: %d" % self.sent)
            self.sender.send(m)
            self.sent += 1

    def tick(self):
        self.timer = self.reactor.schedule(0.5, Timer(self))
        self.send_count = self.rate / 2
        self.send()

host = os.getenv("MESSAGING_SERVICE_HOST") or "127.0.0.1"
port = os.getenv("MESSAGING_SERVICE_PORT") or "5672"
rate = os.getenv("MESSAGE_RATE")           or "100"
addr = os.getenv("MESSAGE_ADDR")           or "example"

if not host:
    raise Exception("No Messaging Service in Environment")

url = "amqp://%s:%s/%s" % (host, port, addr)

try:
    Container(Send(url, int(rate))).run()
except KeyboardInterrupt: pass



