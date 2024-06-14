#!/usr/bin/python

import pprint

import clap

app = clap.Application()
app.extend("tests.fuji.fuji.commands")

pprint.pprint(app.all_commands)

command = app.all_commands.get("server").all_commands.get("hello")
command("Nic")
