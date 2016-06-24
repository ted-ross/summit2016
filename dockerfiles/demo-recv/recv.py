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
from proton.handlers import MessagingHandler
from proton.reactor import Container

class Timer(object):
    def __init__(self, parent):
        self.parent = parent

    def on_timer_task(self, event):
        self.parent.tick()


class Recv(MessagingHandler):
    def __init__(self, url, rate):
        super(Recv, self).__init__(prefetch=0, auto_accept=False)
        self.url = url
        self.rate = rate
        self.can_accept = self.rate / 2
        self.deliveries = []

    def on_start(self, event):
        self.receiver = event.container.create_receiver(self.url)
        self.reactor  = event.reactor
        self.timer    = self.reactor.schedule(0.5, Timer(self))
        self.receiver.flow(self.can_accept)

    def on_message(self, event):
        self.deliveries.insert(0, event.delivery)
        self.do_accept()

    def do_accept(self):
        while self.can_accept > 0 and len(self.deliveries) > 0:
            self.can_accept -= 1
            self.accept(self.deliveries.pop())
            self.receiver.flow(1)

    def tick(self):
        self.timer = self.reactor.schedule(0.5, Timer(self))
        self.can_accept = self.rate / 2
        self.do_accept()


host = os.getenv("MESSAGING_SERVICE_HOST") or "127.0.0.1"
port = os.getenv("MESSAGING_SERVICE_PORT") or "5672"
rate = os.getenv("MESSAGE_RATE")           or "50"
addr = os.getenv("MESSAGE_ADDR")           or "example"

if not host:
    raise Exception("No Messaging Service in Environment")

url = "amqp://%s:%s/%s" % (host, port, addr)

try:
    Container(Recv(url, int(rate))).run()
except KeyboardInterrupt: pass



