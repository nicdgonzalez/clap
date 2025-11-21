# Clap

Work in progress.

A typed command-line argument parser.

While using my previous version of clap, I realized there were some limitations
with my previous design.

I don't like the way the built-in argparse library returns `Any` for all of the
command-line arguments, despite being handed the types ahead of time. I am
currently experimenting with a few different ideas:

1. Script-only version of previous Clap: Generates the command-line interface
   using only a single function (preferably, the `main` function).
1. Or, scrap the auto-definition from function concept and provide a better API
   for adding subparsers, options, and argumetns to the argument parser in a
   fashion similar to pydantic, using dataclasses.
1. Blend the previous two ideas and simply create an adapter that connects
   argparse to a typed version of their Namespace type.
