#!/usr/bin/python

import pprint
import logging
import sys

import clap

logging.basicConfig(level=logging.DEBUG)

app = clap.Application()
app.extend("tests.fuji.fuji.commands")
app.parse_args("_ server hello Nic --favorite-no 7".split())
sys.exit(0)

pprint.pprint(app.all_commands)

command = app.all_commands.get("server").all_commands.get("hello")
command("Nic", favorite_no=7)
