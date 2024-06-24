This project was done for a music collector, who wanted insights in both their music collection as well as the relationship between certain songs (mostly in the form of samples).

The goal was to make a one file graph based database with integrated UI.
The graph database is built with networkx, the UI is built with PyQT.

The program uses its own file format .gdb to store the databases, the UI allows the user to create, open, edit and inspect the contents of the database and the relations between songs.

There is **unfinished** functionality for exporting the graph to the .mm format for use in the freemind and simplemind software

On OSX one can convert the Python script into an standalone application using
```
pyinstaller GDB.spec
```
