# README
This project was done for a music collector, who wanted insights in both their music collection as well as the relationship between certain songs (mostly in the form of samples).

## Goals
The goal was to make a one file graph based database with integrated UI.
The graph database is built with networkx, the UI is built with PyQT.

## File handling
The program uses its own file format .gdb to store the databases, the UI allows the user to create, open, edit and inspect the contents of the database and the relations between songs.
The program supports the fusion of two .gdb files, by importing multiple files into a new one. This means the user can have different small databases, but can also combine them to form a larger database.

The program also allows for importing of sample files. This functionality is tailored to the specific wishes of the client:
There are two example text files which the program can import as a database. An imported file should consist of tab separated columns:
```
ARTIST  TITLE  YEAR  RELATIONSHIP
```
with the main track in the first line, followed by a line with the word "samples", then lines of the sampled tracks. The sampled tracks are followed by a line with the word "sampled", then lines with tracks in which the main track is used.

There is _**unfinished**_ functionality for exporting the graph to the .mm format for use in the freemind and simplemind software, which uses code from [a different repository](https://github.com/wbolster/text-to-freemind/blob/master/text-to-freemind).

## Installation
On OSX one can convert the Python script into an standalone application using
```
pyinstaller GDB.spec
```
