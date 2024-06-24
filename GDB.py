#Must have: None
#Should have: import only important parts of modules for app file size
#             edit all track data (search and replace)
#             automatic size updates (see TODO comment) -> i dont understand qt size hints
#Could have: draw album cover as nodes -> replace by simplemind?
print("Python is awake")
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtTest import *
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import networkx as nx
import os
import re
from texttofreemind import convert_lines_into_mm
print("modules loaded")

#function to display error message window with optional text
#param# text : any, default=None. Message to display. Optional.
def errorBox(text=None):
    errorBox = QMessageBox()
    errorBox.setWindowTitle("ERROR")
    if text != None:
        errorBox.setText(str(text))
    else:
        errorBox.setText("An error occurred. Please contact maintainer.")
    errorBox.setStandardButtons(QMessageBox.StandardButton.Close)
    errorBox.setIcon(QMessageBox.Icon.Critical)
    errorBox.exec()

#function to guarantee all input is capitalized
#param# token : str
#NB. does not cover all cases, not fully robust
def capitalizer(token) -> str:
    tmp = []
    split = token.split(" ")
    for word in split:
        if len(word) > 1:
            if word.startswith("("):
                tmp.append(word[0] + word[1].upper() + word[2:].lower())
            else:
                tmp.append(word[0].upper() + word[1:].lower())
        else:
            tmp.append(word.upper())
    return " ".join(tmp)

#QWidget for drawing graphs
class graphDrawer(QWidget):
    def __init__(self, graph):
        super(graphDrawer, self).__init__()
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.G = graph
        self.drawGraph()

        self.show()

    #calls nx draw with tracknames as labels
    def drawGraph(self):
        self.figure.clf()
        ax4 = self.figure.add_subplot(111)
        if self.G != None:
        #    img = mpimg.imread('/Users/Daan5Vinkel/Desktop/Programmeren/graphdatabase/3DIcon.png')
            layout = nx.spring_layout(self.G, seed=68)
        #    print(layout)
            tracknames = nx.get_node_attributes(self.G, 'trackname')
        #    nx.draw_networkx_edges(self.G, pos=layout)
        #    nx.draw_networkx_labels(self.G, pos=layout, labels=tracknames)
        #    trans = ax4.transData.transform
        #    trans2 = self.figure.transFigure.inverted().transform
        #    piesize=0.05 # this is the image size
        #    p2=piesize/2.0
        #    for n in self.G:
        #        xx,yy=trans(layout[n]) # figure coordinates
        #        xa,ya=trans2((xx,yy)) # axes coordinates
        #        a = plt.axes([xa-p2,ya-p2, piesize, piesize])
        #        a.set_aspect('equal')
        #        a.imshow(img)
        #        a.axis('off')
        #    ax4.axis('off')
            nx.draw(self.G, pos=layout, with_labels=True, labels=tracknames, node_shape='8')
            #limits=plt.axis('on')
            #ax4.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        self.canvas.draw_idle()

#class inheriting QTableWidget to overwrite keypressevent
class tableWidget(QTableWidget):
    def __init__(self):
        super(tableWidget, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Tab):
            return
        if event.key() == Qt.Key.Key_Down:
            self.selectRow(self.currentRow()+1)
            return
        if event.key() == Qt.Key.Key_Up:
            self.selectRow(self.currentRow()-1)
            return
        super().keyPressEvent(event)

#QWidget base class for all track tables
class baseTrackTable(QWidget):
    buttonEnabler = pyqtSignal(bool) #bool signal for table interaction button activation

    trackIds = [] #list of track ids in the table
    prevSortIndicator = -1 #flag for sorting per column

    def __init__(self, gdb):
        super(baseTrackTable, self).__init__()

        self.gdb = gdb
        self.attributes = gdb.attributes
        self.tableWidget = tableWidget()
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setSectionsMovable(True)
        self.tableWidget.horizontalHeader().setSortIndicatorShown(True)
        self.tableWidget.horizontalHeader().sectionPressed.disconnect(self.tableWidget.selectColumn)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self._setupFilter()

        self.tableWidget.horizontalHeader().sectionClicked.connect(self.sortColumnHeader)
        self.tableWidget.itemSelectionChanged.connect(self._activateButtons)

        #TODO, i dont understand qt size hints
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        #self.staticpolicy = self.sizePolicy()
        self.dynamicpolicy = QSizePolicy(QSizePolicy.Policy.Fixed,QSizePolicy.Policy.Fixed)

    #method to create a filterlayout to be added if wished
    def _setupFilter(self):
        self.filterLayout = QHBoxLayout()
        self.comboBox = QComboBox()
        items = self.gdb.attributes.copy()
        items.remove("vinyl")
        self.comboBox.addItems(items)

        self.filterText = QLineEdit()
        self.filterText.setPlaceholderText("Filter table...")
        self.filterText.textChanged.connect(self.filterTable)

        self.resetButton = QPushButton()
        self.resetButton.setText("Reset")
        self.resetButton.clicked.connect(self.resetFilter)
        self.filterLayout.addWidget(self.comboBox)
        self.filterLayout.addWidget(self.filterText)
        self.filterLayout.addWidget(self.resetButton)

    #method to emit activation of buttons attached to buttonenabler
    def _activateButtons(self):
        if self.tableWidget.currentRow() == -1:
            self.buttonEnabler.emit(False)
        else:
            self.buttonEnabler.emit(True)

    #method connected to click on column header for sorting the table
    #param# index : int, column index
    def sortColumnHeader(self, index):
        if self.prevSortIndicator == index:
            self.tableWidget.sortItems(index, Qt.SortOrder.DescendingOrder)
            self.prevSortIndicator = -1
        else:
            self.tableWidget.sortItems(index, Qt.SortOrder.AscendingOrder)
            self.prevSortIndicator = index

    #method to get the 3 key attributes for the given row
    #param# row : int, row index
    def getRowAttributes(self, row) -> dict:
        attributes = {}
        for c in range(self.tableWidget.columnCount()):
            attribute = self.tableWidget.horizontalHeaderItem(c).text()
            if attribute == "trackname" or attribute == "artist" or attribute == "year":
                value = self.tableWidget.item(row, c).text()
                attributes[attribute] = value
        return attributes

    #getter method, returns track id of selected row, or -1 if no row is selected
    def getSelectedId(self) -> int:
        row = self.tableWidget.currentRow()
        if row == -1:
            return -1
        else:
            attributes = self.getRowAttributes(row)
            trackId = self.gdb.attrToId(attributes)
            if trackId == None or trackId == -1:
                return -1
            else:
                return trackId

    #method connected to filter reset button
    def resetFilter(self):
        self.filterText.setText("")
        self.filterTable()

    #method for filtering selected column with filter query
    def filterTable(self):
        field = self.comboBox.currentText()
        mask = self.filterText.text()

        for c in range(self.tableWidget.columnCount()):
            if self.tableWidget.horizontalHeaderItem(c).text() == field:
                col = c
                break

        found = self.tableWidget.findItems(mask, Qt.MatchFlag.MatchContains)
        for n in range(self.tableWidget.rowCount()):
            if mask == "": #show all items when no text entered
                self.tableWidget.setRowHidden(n, False)
            elif self.tableWidget.item(n,col) in found: #item matched
                self.tableWidget.setRowHidden(n, False)
            else: #item not matched
                self.tableWidget.setRowHidden(n, True)

    #fill list with trackIds
    def fillList(self):
        self.tableWidget.setColumnCount(len(self.attributes))
        for col, attr in enumerate(self.attributes): #for all attributes (columns)
            header = QTableWidgetItem(attr)
            self.tableWidget.setHorizontalHeaderItem(col, header)
            for row, trackId in enumerate(self.trackIds): #for all tracks (rows)
                if col == 0:
                    self.tableWidget.insertRow(row)
                if attr == "vinyl": #vinyl is a boolean check button
                    item = QTableWidgetItem()
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    #item.setStyleSheet("margin-left:20%; margin-right:5%;") #<- doesnt work >:()
                    try:
                        if self.gdb.G.nodes[trackId][attr] == "True":
                            item.setCheckState(Qt.CheckState.Checked)
                        elif self.gdb.G.nodes[trackId][attr] == "False":
                            item.setCheckState(Qt.CheckState.Unchecked)
                    except:
                        item.setCheckState(Qt.CheckState.Unchecked)
                else: #everything except vinyl
                    try:
                        item = QTableWidgetItem(self.gdb.G.nodes[trackId][attr])
                    except:
                        item = QTableWidgetItem("")
                self.tableWidget.setItem(row, col, item)
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.sortItems(0)

    def emptyList(self):
        for _ in range(self.tableWidget.rowCount()):
            self.tableWidget.removeRow(0)

    #updates the table with given track ids
    #param# ids : list, track ids
    def updateList(self, ids):
        self.emptyList()
        self.trackIds = ids
        self.fillList()

#tracktable for inspector with less attributes, no filter and relation comment support
class inspectorTable(baseTrackTable):
    commentUpdated = pyqtSignal(bool) #emits true to notify that the gdb is now edited
    trackDoubleClicked = pyqtSignal(str) #emits str(trackid) to switch inspected track

    maintrackId = -1 #is updated after init from parent dialog, bit hacky
    selectedId = -1 #storage for selectedId

    def __init__(self, gdb, title):
        super(inspectorTable, self).__init__(gdb)
        self.attributes = ['artist', 'trackname', 'year'] #less attributes
        if title == "Sample sources:": #title determines on which side the table is on
            self.type = "left"
        else:
            self.type = "right"

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("<b>"+title+"</b>"))

        self.tableWidget.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.layout.addWidget(self.tableWidget)

        commentlabel = QLabel("<b>Relation comment:</b>")
        self.layout.addWidget(commentlabel)
        self.commentbox = QLineEdit()
        self.layout.addWidget(self.commentbox)
        
        self.tableWidget.currentCellChanged.connect(self.displayComment)
        self.tableWidget.itemDoubleClicked.connect(self.emitId)
        self.commentbox.textEdited.connect(self.saveComment)

        self.tableWidget.installEventFilter(self)

    #method to tell the gdb to update relation comment
    def saveComment(self, newtext):
        if self.selectedId == -1:
            QApplication.beep()
            self.commentbox.setText("")
            return
        if self.type == "left":
            self.gdb.updateEdgeComment(self.selectedId, self.maintrackId, newtext)
        else:
            self.gdb.updateEdgeComment(self.maintrackId, self.selectedId, newtext)
        self.commentUpdated.emit(True)

    #method connected to changing of current cell, displaying the correct edge comment
    #param# currentRow, currentCol, prevRow, prevCol : int
    def displayComment(self, currentRow, currentCol, prevRow, prevCol):
        if currentRow == prevRow:
            return #do nothing
        if currentRow == -1:
            self.selectedId = -1
            return
        self.selectedId = self.getSelectedId()
        if self.type == "left":
            self.commentbox.setText(self.gdb.getEdgeComment(self.selectedId, self.maintrackId))
        else:
            self.commentbox.setText(self.gdb.getEdgeComment(self.maintrackId, self.selectedId))

    #method connected to itemdoubleclicked, get id and emit
    #param# item : UNUSED
    def emitId(self, item):
        trackId = self.getSelectedId()
        self.trackDoubleClicked.emit(trackId)

    #event filter override to reset selected cell after focus leaves the window
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            if obj == self.tableWidget and not self.commentbox.hasFocus():
                self.tableWidget.setCurrentCell(-1,0)
        return super().eventFilter(obj, event)

#QDialog for inspecting track information, has two tables for relation comments and graph navigation
class trackInspector(QDialog):
    relationUpdated = False #flag to check if we want to ask for saving

    def __init__(self, gdb, trackId):
        super().__init__()
        self.gdb = gdb

        self.outerLayout = QVBoxLayout()

        self.innerLayout = QHBoxLayout()
        self.leftList = inspectorTable(self.gdb, "Sample sources:")
        self.innerLayout.addWidget(self.leftList)

        self.middle = QVBoxLayout()
        self.innerLayout.addLayout(self.middle)

        self.rightList = inspectorTable(self.gdb, "Is sampled in:")
        self.innerLayout.addWidget(self.rightList)

        self.outerLayout.addLayout(self.innerLayout)

        QBtn = QDialogButtonBox.StandardButton.Close
        self.buttonBox = QDialogButtonBox(QBtn)
        self.removeButton = QPushButton("Remove relation")
        self.removeButton.setEnabled(False)
        self.buttonBox.addButton(self.removeButton, QDialogButtonBox.ButtonRole.ActionRole)
        self.outerLayout.addWidget(self.buttonBox)

        self.setLayout(self.outerLayout)

        self.leftList.trackDoubleClicked.connect(self.loadTrack)
        self.leftList.commentUpdated.connect(self._onRelationUpdated)
        self.leftList.buttonEnabler.connect(self.removeButton.setEnabled)
        self.rightList.trackDoubleClicked.connect(self.loadTrack)
        self.rightList.commentUpdated.connect(self._onRelationUpdated)
        self.rightList.buttonEnabler.connect(self.removeButton.setEnabled)
        self.buttonBox.rejected.connect(self._returner)
        self.removeButton.clicked.connect(self._removeRelation)

        self.loadTrack(trackId)

    #method connected to close button and closeEvent, returns if gdb has been changed
    def _returner(self):
        if self.relationUpdated == True:
            self.accept()
        else:
            self.reject()

    def closeEvent(self, event):
        self._returner()

    #method connected to commentUpdated for setting relationupdated flag
    def _onRelationUpdated(self, flag):
        self.relationUpdated = self.relationUpdated or flag

    #method connected to remove button to remove relation between main track and selected id
    def _removeRelation(self):
        if self.leftList.tableWidget.hasFocus():
            self.gdb.removeEdge(self.leftList.getSelectedId(), self.leftList.maintrackId)
            self.loadTrack(self.leftList.maintrackId)
            self.relationUpdated = True
        elif self.rightList.tableWidget.hasFocus():
            self.gdb.removeEdge(self.rightList.maintrackId, self.rightList.getSelectedId())
            self.loadTrack(self.rightList.maintrackId)
            self.relationUpdated = True

    #keypressevent override to support escape window close
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._returner()
            return
        super().keyPressEvent(event)

    #method for loading main track and changing the tables accordingly
    #param# trackId : str
    def loadTrack(self, trackId):
        self.trackAttributes = self.gdb.G.nodes[trackId]
        leftids = []
        for n in self.gdb.G.predecessors(trackId):
            leftids.append(n)
        self.leftList.updateList(leftids)
        self.leftList.maintrackId = trackId
        self.leftList.commentbox.setText("")
        rightids = []
        for n in self.gdb.G.successors(trackId):
            rightids.append(n)
        self.rightList.updateList(rightids)
        self.rightList.maintrackId = trackId
        self.rightList.commentbox.setText("")

        self.updateAttributes()

    #method for updating main track attributes and displaying
    def updateAttributes(self):
        for i in reversed(range(self.middle.count())): #destroy all current attributes
            self.middle.itemAt(i).widget().deleteLater()

        for attr in self.gdb.attributes: #create and display new attributes
            self.middle.addWidget(QLabel("<b>"+attr+":</b>\t"+self.trackAttributes[attr]))

        self.setWindowTitle("Inspect \""+self.trackAttributes["trackname"]+"\"")

#QDialog for adding tracks
class trackAdder(QDialog):
    adderattributes = ['artist', 'trackname', 'year', 'vinyl', 'comments', 'comments2']

    def __init__(self, gdb):
        super().__init__()
        self.gdb = gdb
        self.setWindowTitle("Add track relation")

        self._createmain()

        self.buttonBox.accepted.connect(self.addRelation)
        self.buttonBox.rejected.connect(self.reject)
        self.fileButton.clicked.connect(self.addFromFile)

    #set up fields for all attributes and returns vertical layout
    #param# fielddict : dict, label : str
    def _createfields(self, fielddict, label) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.addWidget(QLabel(label))

        for attr in self.adderattributes:
            stringlist = []
            for node in self.gdb.G.nodes:
                stringlist.append(self.gdb.G.nodes[node][attr])
            completer = QCompleter(list(set(stringlist)))
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            if attr == "vinyl":
                fielddict[attr] = QCheckBox("vinyl")
                fielddict[attr].setChecked(False)
            else:
                fielddict[attr] = QLineEdit()
                fielddict[attr].installEventFilter(self)
                fielddict[attr].setPlaceholderText(attr)
                fielddict[attr].setCompleter(completer)
            layout.addWidget(fielddict[attr])

        return layout

    #set up main layout, with two vertical field layouts and edgecomment
    def _createmain(self):
        QBtn = QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.fileButton = QPushButton("Add from file")
        self.buttonBox.addButton(self.fileButton, QDialogButtonBox.ButtonRole.ActionRole)

        self.mainlayout = QVBoxLayout()
        self.mainlayout2 = QHBoxLayout()

        self.leftfields = {}
        self.leftlayout = self._createfields(self.leftfields, "Source")
        self.rightfields = {}
        self.rightlayout = self._createfields(self.rightfields, "Sample")

        self.mainlayout2.addLayout(self.leftlayout)
        self.mainlayout2.addLayout(self.rightlayout)

        self.mainlayout.addLayout(self.mainlayout2)

        stringlist = []
        for edge in self.gdb.G.edges:
            stringlist.append(self.gdb.G.edges[edge[0], edge[1]]["comment"])
        completer = QCompleter(list(set(stringlist)))
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.edgecomment = QLineEdit()
        self.edgecomment.setPlaceholderText("Relation comment")
        self.edgecomment.setCompleter(completer)
        self.mainlayout.addWidget(self.edgecomment)

        self.mainlayout.addWidget(self.buttonBox)
        self.setLayout(self.mainlayout)

    #method for adding tracks from GDB file
    #param# file : str
    def _addFromGDB(self, file):
        G = nx.read_gml(file)
        for edge in G.edges:
            source = G.nodes[edge[0]]
            sample = G.nodes[edge[1]]
            try:
                edgecomment = G.edges[edge[0], edge[1]]['comment']
                self.gdb.addEdge(source, sample, edgecomment)
            except:
                self.gdb.addEdge(source, sample)

    #super complicated method for parsing text file setup, very hacky
    #param# file : str
    def _addFromTextfile(self, file):
        maintrack = {}
        sourcetracks = []
        sampletracks = []
        keysfound = 0
        with open(file, "r") as f:
            lines = f.readlines()
            lines2 = []
            for i, line in enumerate(lines):
                lines2.append(line.split("\t"))
            for i, line in enumerate(lines):
                line = line.split("\t")
                if i != len(lines)-1:
                    if lines2[i+1][0][:1] == "-":
                        errorBox("Cannot parse file. Make sure all track data is on one line.")
                        return
                for i, token in enumerate(line): 
                    #remove weird rtf inserts
                    if "\\'92" in token: #skip rtf apostrophe
                        tmp = token.replace("\\'92", "'")
                    else:
                        tmp = re.sub("(\\\\)\S*\s", "", token) 
                    #remove endline and rtf end brackets
                    line[i] = tmp.replace("\n", "").replace("}", "")
                if line[0].split(" ")[0].upper()[:6] != "SAMPLE" \
                    and len(line) == 1 and len(line[0].split(" ")) == 1: 
                    #filter out most rtf artefacts
                    print("early filter", line)
                    continue

                print(line)

                if (keysfound == 1 or keysfound == 2) and \
                    (line[0].split(" ")[0].upper()[:6] == "SAMPLE" or \
                    line[0].split(" ")[0].upper()[:6] == "SOURCE"):
                    keysfound += 1
                    print("switching sample mode")
                elif keysfound == 2:
                    sourcetrack = {}
                    sourcetrack['artist'] = capitalizer(line[0])
                    sourcetrack['trackname'] = capitalizer(line[1])
                    sourcetrack['year'] = line[2]
                    if len(line) > 3:
                        sourcetrack['edgecomment'] = capitalizer(line[3])
                    sourcetrack['vinyl'] = "False"
                    sourcetracks.append(sourcetrack)
                elif keysfound == 3:
                    sampletrack = {}
                    sampletrack['artist'] = capitalizer(line[0])
                    sampletrack['trackname'] = capitalizer(line[1])
                    sampletrack['year'] = line[2]
                    if len(line) > 3:
                        sampletrack['edgecomment'] = capitalizer(line[3])
                    sampletrack['vinyl'] = "False"
                    sampletracks.append(sampletrack)
                elif keysfound == 0: #first line should be main track
                    maintrack['artist'] = capitalizer(line[0])
                    maintrack['trackname'] = capitalizer(line[1])
                    maintrack['year'] = line[2]
                    if len(line) > 3:
                        maintrack['comments'] = capitalizer(line[3])
                    else:
                        maintrack['comments'] = ""
                    keysfound = 1

        maintrack['comments2'] = ""
        maintrack['vinyl'] = "False"

        #optimization possible, put below code in above loop
        for sourcetrack in sourcetracks:
            for attr in self.gdb.attributes:
                try:
                    _ = sourcetrack[attr]
                except KeyError:
                    sourcetrack[attr] = ""
            self.gdb.addEdge(sourcetrack, maintrack)
        for sampletrack in sampletracks:
            for attr in self.gdb.attributes:
                try:
                    _ = sampletrack[attr]
                except KeyError:
                    sampletrack[attr] = ""
            self.gdb.addEdge(maintrack, sampletrack)

    #method for adding tracks from a GDB or text file, calls appropriate method for this
    def addFromFile(self):
        name = QFileDialog.getOpenFileName(self, 'Open File', \
                filter="Graph DataBase or Text files (*.gdb *.txt *.rtf)")[0]
        if name == "":
            return
        if name[-4:] == ".txt" or name[-4:] == ".rtf":
            self._addFromTextfile(name)
        elif name[-4:] == ".gdb":
            self._addFromGDB(name)
        else:
            errorBox("file type "+name[-4:]+" not supported")
            return
        self.accept()

    #event filter override to allow enter key functionality
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and (obj in self.leftfields.values()\
                                                  or obj == self.rightfields.values()):
            if event.key() == Qt.Key.Key_Return:
                self.addRelation()
        return super().eventFilter(obj, event)

    #QTimer method to toggle frame on fields repeatedly, connected from flashFields
    def toggleFrame(self):
        self.count += 1

        for attr in ["trackname", "artist", "year"]:
            self.leftfields[attr].setFrame(not self.leftfields[attr].hasFrame())
            self.rightfields[attr].setFrame(not self.rightfields[attr].hasFrame())

        if self.count == 6:
            self.timer.stop()

    #method to flash field frames to indicate incomplete entry
    def flashFields(self):
        self.count = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.toggleFrame)
        self.timer.start(100)

    #method for adding relation after entry of fields, parses fields and passes to gdb
    def addRelation(self):
        left = {}
        right = {}

        for attr in self.adderattributes:
            if attr == "vinyl":
                left[attr] = str(self.leftfields[attr].isChecked())
            else:
                if attr == "trackname" or attr == "artist" or attr == "year":
                    if self.leftfields[attr].text() == "" or self.leftfields[attr].text() == "-":
                        QApplication.beep()
                        self.flashFields()
                        return
                left[attr] = capitalizer(self.leftfields[attr].text())
            if attr == "vinyl":
                right[attr] = str(self.rightfields[attr].isChecked())
            else:
                if attr == "trackname" or attr == "artist" or attr == "year":
                    if self.rightfields[attr].text() == "" or self.rightfields[attr].text() == "-":
                        QApplication.beep()
                        self.flashFields()
                        return 
                right[attr] = capitalizer(self.rightfields[attr].text())

        self.gdb.addEdge(left, right, self.edgecomment.text())
        self.accept()

#tracktable for main window, with track info edit interactivity
class mainTable(baseTrackTable):
    trackUpdated =  pyqtSignal(bool) #emits if gdb has been edited
    trackDoomed = pyqtSignal() #emits if a track has been designated for destruction

    dontupdategdb = True #safeguard to prevent gdb updates when performing some changes

    def __init__(self, gdb):
        super(mainTable, self).__init__(gdb)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.filterLayout)
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.tableWidget.itemChanged.connect(self.updateGraph)
        self.tableWidget.cellPressed.connect(self.savePressedItem)
        self.tableWidget.horizontalHeader().sectionClicked.connect(self.sortColumnHeader)
        self.tableWidget.installEventFilter(self)

    #method for updating gdb, collects new track info and passes it to gdb
    #param# item : QItem
    def updateGraph(self, item):
        if self.dontupdategdb == False:
            trackId = self.getEditedId(item)
            if trackId == -1:
                errorBox("no bueno señor, track id = " + str(trackId))
                return
            newAttributes = {}
            for c in range(self.tableWidget.columnCount()):
                attribute = self.tableWidget.horizontalHeaderItem(c).text()
                if attribute == "vinyl":
                    state = self.tableWidget.item(item.row(), c).checkState()
                    if state == Qt.CheckState.Checked:
                        value = "True"
                    else:
                        value = "False"
                else:
                    value = self.tableWidget.item(item.row(), c).text()
                newAttributes[attribute] = value
            self.tableWidget.resizeColumnsToContents()
            self.gdb.updateTrack(trackId, newAttributes)
            self.trackUpdated.emit(False)

    #method connected to cellPressed
    #exists only to make sure key field id matching works after editing
    def savePressedItem(self, row, column): 
        self.prevPressed = self.tableWidget.item(row, column).clone()

    #get the id of the edited item or return -1 if not matched
    #param# item : QItem
    def getEditedId(self, item):
        attributes = self.getRowAttributes(item.row())
        coltext = self.tableWidget.horizontalHeaderItem(item.column()).text()
        if coltext == "trackname" or coltext == "artist" or coltext == "year":
            attributes[coltext] = self.prevPressed.text()
        trackId = self.gdb.attrToId(attributes)
        if trackId == None or trackId == -1:
            return -1
        else:
            return trackId

    #event filter override to allow backspace track deletion
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and obj == self.tableWidget:
            if event.key() == Qt.Key.Key_Backspace:
                self.trackDoomed.emit()
        return super().eventFilter(obj, event)

#MainWindow
class MainWindow(QMainWindow):
    openfile = ""
    funcButtons = ['Add', 'Inspect', 'Remove', 'New', 'Open', 'Save', 'Save As', 'Export', 'Exit'] #'Draw'

    saveable = pyqtSignal(bool) #emits if the file is saveable

    def __init__(self, gdb, path=None):
        super(MainWindow, self).__init__()
        self.updateTitle(None)
        self.gdb = gdb
        self.menuBar = QMenuBar()
        self.centralWidget = QWidget()
        self.layout = QHBoxLayout()

        self.setCentralWidget(self.centralWidget)
        self.centralWidget.setLayout(self.layout)

        self.mainTable = mainTable(gdb)

        self._createVerticalGroupBox() 
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.verticalGroupBox)

        self.layout.addLayout(buttonLayout)
        self.layout.addWidget(self.mainTable)

        self.mainTable.trackUpdated.connect(self.updateTitle)
        self.mainTable.trackUpdated.connect(self.updateDrawer)
        self.mainTable.trackDoomed.connect(self.Remove)

        self._createShortcuts()

        if path != None:
            self.Open(path)
            self.updateTitle(True)
        else:
            self.New()

        self.show()

    #method to create left button column
    def _createVerticalGroupBox(self):
        self.verticalGroupBox = QGroupBox()

        layout = QVBoxLayout()
        for i in self.funcButtons:
                button = QPushButton(i)
                button.setObjectName(i)
                layout.addWidget(button)
                layout.setSpacing(10)
                self.verticalGroupBox.setLayout(layout)
                button.clicked.connect(self._submitCommand)
                if i == "Inspect" or i == "Remove":
                    button.setEnabled(False)
                    self.mainTable.buttonEnabler.connect(button.setEnabled)
                elif i == "Save" or i == "Save As":
                    button.setEnabled(False)
                    self.saveable.connect(button.setEnabled)

    #method connected to left columns buttons to execute function on click
    def _submitCommand(self):
        if str(self.sender().objectName()) == "Save As":
            self.SaveAs()
        else:
            eval('self.' + str(self.sender().objectName()) + '()')

    #method to create top toolbar menus and key combination hints
    def _createShortcuts(self):
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.New)
        self.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.Open)
        self.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.Save)
        self.addAction(save_action)

        saveas_action = QAction("&Save As...", self)
        saveas_action.setShortcut("Ctrl+Shift+S")
        saveas_action.triggered.connect(self.SaveAs)
        self.addAction(saveas_action)

        self.file_menu = self.menuBar.addMenu("&File")
        self.file_menu.addAction(new_action)
        self.file_menu.addAction(open_action)
        self.file_menu.addAction(save_action)
        self.file_menu.addAction(saveas_action)
        
        add_action = QAction("&Add", self)
        add_action.setShortcut("Ctrl+A")
        add_action.triggered.connect(self.Add)
        self.addAction(add_action)

        inspect_action = QAction("&Inspect", self)
        inspect_action.setShortcut("Ctrl+I")
        inspect_action.triggered.connect(self.Inspect)
        self.addAction(inspect_action)

        export_action = QAction("&Export", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.Export)
        self.addAction(export_action)

        self.gdb_menu = self.menuBar.addMenu("&GDB")
        self.gdb_menu.addAction(add_action)
        self.gdb_menu.addAction(inspect_action)
        self.gdb_menu.addAction(export_action)

        reset_action = QAction("&Reset", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.mainTable.resetFilter)
        self.addAction(reset_action)

        find_action = QAction("&Find", self)
        find_action.setShortcut("Ctrl+F")
        find_action.triggered.connect(self.mainTable.filterText.setFocus)
        self.addAction(find_action)

        fnr_action = QAction("&Find and replace", self)
        fnr_action.setShortcut("Ctrl+Shift+F")
        fnr_action.triggered.connect(self.findAndReplace)
        self.addAction(fnr_action)

        self.table_menu = self.menuBar.addMenu("&Table")
        self.table_menu.addAction(find_action)
        self.table_menu.addAction(fnr_action)
        self.table_menu.addAction(reset_action)

    #method to update the main table with stored gdb ids, to be called after every change
    def updateTable(self): #optimization possible
        self.mainTable.updateList(list(self.gdb.G.nodes))

    #method to tell gdb to change node attributes, unused (maybe delete?)
    def updateNode(self, changes):
        if changes[0] != changes[1]:
            self.gdb.updateNode(changes[0], changes[1])
            self.updateDrawer()
            self.updateTable()

    #method to update drawn graph after changes, deprecated since simplemind replaced drawer
    def updateDrawer(self):
        try:
            self.drawer.G = self.gdb.G
            self.drawer.drawGraph()
        except:
            pass

    #method to update window title to indicate which file is currently open and if any changes have been made (*)
    #param# saved : None or bool
    def updateTitle(self, saved):
        if saved == None: #nothing opened
            self.setWindowTitle("Graph DataBase")
            self.saveable.emit(False) #empty file not saveable
        elif saved == True: #file opened, no unsaved changes
            self.setWindowTitle("Graph Database (" + self.openfile + ")")
            self.saveable.emit(True)
        else: #file opened, unsaved changes
            self.setWindowTitle("*Graph Database (" + self.openfile + ")")
            self.saveable.emit(True)

    #method connected to New button, load empty graph into gdb and runs update routines
    def New(self):
        check = self.checkSaved()

        if check == "Cancel":
            return
        else:
            self.openfile = ""
            self.gdb.loadGraph(nx.DiGraph())
            self.updateTitle(None)
            self.updateTable()
            self.updateDrawer()
            self.mainTable.dontupdategdb = True
            #self.mainTable.setSizePolicy(self.mainTable.staticpolicy)

    #method connected to Open button, opens file dialog and loads gdb file, then runs update routines
    #param# name : str, default=None. optional path to file, when provided does not open file dialog
    def Open(self, name=None):
        self.mainTable.dontupdategdb = True
        if type(name) != str:
            name = QFileDialog.getOpenFileName(self, 'Open File', filter="*.gdb")[0]
            if name == "":
                return
        self.openfile = name
        G = nx.read_gml(name)
        self.gdb.loadGraph(G)
        self.updateTable()
        self.updateDrawer()
        self.updateTitle(True)
        self.mainTable.dontupdategdb = False
        self.mainTable.setSizePolicy(self.mainTable.dynamicpolicy)

    #method connected to Save button, tells gdb to write the graph, if no file is open calls SaveAs
    def Save(self):
        if self.openfile == "":
            self.SaveAs()
            if self.openfile == "":
                return False
            else:
                return True
        if self.windowTitle()[:1] == "*":
            self.gdb.writeGraph(self.openfile)
            self.updateTitle(True)
            return True

    #method connected to SaveAs button, can be called through Save. Opens file dialog and saves the gdb
    def SaveAs(self):
        if self.windowTitle()[:1] == "*":
            name = QFileDialog.getSaveFileName(self, 'Save GDB', filter="*.gdb")[0]
            if name == "":
                return
            self.openfile = name
            self.gdb.writeGraph(name)
            self.updateTitle(True)

    #method connected to Add button, opens trackAdder dialog
    def Add(self):
        adder = trackAdder(self.gdb)
        self.mainTable.dontupdategdb = True
        if adder.exec():
            self.updateTable()
            self.updateDrawer()
            self.updateTitle(False)
        self.mainTable.dontupdategdb = False

    #method connected to Inspect button, opens trackInspector dialog for selected track
    def Inspect(self):
        trackId = self.mainTable.getSelectedId()
        if trackId == -1:
            QApplication.beep()
            return
        else:
            inspector = trackInspector(self.gdb, trackId)
            if inspector.exec():
                self.mainTable.dontupdategdb = True
                self.updateDrawer()
                self.updateTitle(False)
                self.gdb.updateSampleCounts()
                self.updateTable()
                self.mainTable.dontupdategdb = False

    #method connected to Remove button, removes selected track and its relations
    def Remove(self):
        trackId = self.mainTable.getSelectedId()
        if trackId == -1:    
            QApplication.beep()
            return
        else:
            self.mainTable.dontupdategdb = True
            for sourceid in list(self.gdb.G.predecessors(trackId)):
                self.gdb.removeEdge(sourceid, trackId)
            for sampleid in list(self.gdb.G.successors(trackId)):
                self.gdb.removeEdge(trackId, sampleid)
            self.gdb.removeNode(trackId)
            self.updateTable()
            self.updateDrawer()
            self.updateTitle(False)
            self.mainTable.dontupdategdb = False

    #method connected to Draw button, draws graph, deprecated since Simplemind replaced Draw
    def Draw(self):
        self.drawer = graphDrawer(self.gdb.G)

    #method connected to Export button, opens file dialog and tells gdb to export to .mm file
    def Export(self):
        name = QFileDialog.getSaveFileName(self, 'Export GDB', filter="*.mm")[0]
        if name == "":
            return
        else:
            self.gdb.exportGraph(name)

    #method to find and replace text in gdb, unfinished
    def findAndReplace(self):
        print("bla")

    def Exit(self):
        self.close()

    #method to check if the current file had unsaved changed, used to safeguard before file operations
    def checkSaved(self):
        if self.windowTitle()[:1] == "*":
            notSavedCheck = QMessageBox(self)
            notSavedCheck.setWindowTitle("File not saved")
            notSavedCheck.setText("The file is not saved, do you want to still save?")
            notSavedCheck.setStandardButtons(QMessageBox.StandardButton.Discard | \
                QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Save)
            notSavedCheck.setIcon(QMessageBox.Icon.Warning)
            response = notSavedCheck.exec()

            if response == QMessageBox.StandardButton.Cancel:
                return "Cancel"
            elif response == QMessageBox.StandardButton.Save:
                saved = self.Save()
                if saved == True:
                    return "Saved"
                else:
                    return "Cancel"
            else:
                return "Discard"
        else:
            return "Saved"

    #closeevent override to prevent accidental closure
    def closeEvent(self, event):
        print("closing down")
        check = self.checkSaved()

        if check == "Cancel":
            event.ignore()
            return
        else:
            QApplication.closeAllWindows()
            event.accept()

#backend networkx digraph manipulator
class GraphDatabase():
    hastracks = False #unused
    attributes = ['artist', 'trackname', 'year', 'vinyl', 'hassample', \
                  'issource', 'comments', 'comments2']

    def __init__(self):
        self.G = nx.DiGraph()

    #method to load new graph
    #param# g : nx.DiGraph
    def loadGraph(self, g):
        self.G = g
        stringer = {}
        for node in self.G.nodes():
            stringer[node] = str(node)
            for attr in self.attributes:
                if attr != "hassample" and attr != "issource":
                    try: #hacky way to ensure all attributes are present
                        _ = self.G.nodes[node][attr]
                    except KeyError:
                        self.G.nodes[node][attr] = ""
        self.G = nx.relabel_nodes(self.G, stringer)
        #self._splitGraph()
        self.updateSampleCounts()
        if self.G.number_of_nodes() > 0:
            self.hastracks = True

    #method to record which tracks are sources and which are samples. deprecated
    def _splitGraph(self): 
        sources = []
        samples = []
        for edge in self.G.edges(data=True):
            sources.append(edge[0])
            samples.append(edge[1])

        self.sources = list(set(sources))
        self.samples = list(set(samples))

    #method to determine id based on key attributes, returns None if no match, else track id
    #param# attributes : dict with at least trackname, artist, year keys
    def attrToId(self, attributes):
        IDs = [x for x,y in self.G.nodes(data=True) if y['trackname']==attributes['trackname'] \
                                                    and y['artist']==attributes['artist'] \
                                                    and y['year']==attributes['year']]

        if len(IDs) == 0: #no match
            return None
        elif len(IDs) > 1:
            return -1 #something went wrong
        else: #match!
            return IDs[0]

    #method to count for each track how many sources and samples it has
    def updateSampleCounts(self):
        for n in self.G.nodes:
            sampled = len(self.G._succ[n])
            samples = len(self.G._pred[n])
            self.G.nodes[n]['issource'] = str(sampled)
            self.G.nodes[n]['hassample'] = str(samples)

    #setter method to update track information through robust nx adding
    #param# trackId : str, newAttributes : dict
    def updateTrack(self, trackId, newAttributes):
        self.G.add_node(trackId, trackname=newAttributes['trackname'], \
            artist=newAttributes['artist'], year=newAttributes['year'], \
            vinyl=newAttributes['vinyl'], hassample=newAttributes['hassample'], \
            issource=newAttributes['issource'], comments=newAttributes['comments'], \
            comments2=newAttributes['comments2'])
        #self._splitGraph() #optimization possible

    #setter method to update relation comment
    #param# sourceid, sampleid : str
    def updateEdgeComment(self, sourceid, sampleid, edgecomment):
        self.G.edges[sourceid, sampleid]['comment'] = edgecomment

    #getter method to get relation comment
    #param# sourceid, sampleid : str
    def getEdgeComment(self, sourceid, sampleid) -> str:
        return self.G.edges[sourceid, sampleid]['comment']

    #method to remove track
    #param# trackId : str
    def removeNode(self, trackId):
        self.G.remove_node(trackId)

    #method to remove relation
    #param# source, sample : str
    def removeEdge(self, source, sample):
        self.G.remove_edge(source, sample)

    #method to add relation, very robust
    #param# source, sample : str, edgecomment : str, default=""
    def addEdge(self, source, sample, edgecomment=""):
        potentialsourceid = self.attrToId(source)
        potentialsampleid = self.attrToId(sample)

        if potentialsourceid == -1 or potentialsampleid == -1:
            errorBox()
            return

        if self.G.number_of_nodes() == 0:
            self.hastracks = True

        if potentialsampleid == None:
            if potentialsourceid == None:
                sampleid = str(self.G.number_of_nodes()+1)
            else:
                sampleid = str(self.G.number_of_nodes())
        else:
            sampleid = potentialsampleid

        if potentialsourceid == None:
            sourceid = str(self.G.number_of_nodes())
        else:
            sourceid = potentialsourceid

        #really ugly code
        if edgecomment == "":
            try:
                edgecomment += capitalizer(source['edgecomment'])
            except:
                pass
            try:
                edgecomment += capitalizer(sample['edgecomment'])
            except:
                pass

        self.G.add_edge(sourceid, sampleid, comment=edgecomment)

        for attr in self.attributes:
            if attr == "vinyl":
                try:
                    self.G.nodes[sourceid][attr] = str(eval(source[attr]) or \
                                                       eval(self.G.nodes[sourceid][attr]))
                except KeyError:
                    self.G.nodes[sourceid][attr] = "False"
                try:
                    self.G.nodes[sampleid][attr] = str(eval(sample[attr]) or \
                                                       eval(self.G.nodes[sampleid][attr]))
                except KeyError:
                    self.G.nodes[sampleid][attr] = "False"
            elif attr[:8] == "comments":
                try:
                    self.G.nodes[sourceid][attr] += " " + capitalizer(source[attr])
                except KeyError:
                    self.G.nodes[sourceid][attr] = capitalizer(source[attr])
                try:
                    self.G.nodes[sampleid][attr] += " " + capitalizer(sample[attr])
                except KeyError:
                    self.G.nodes[sampleid][attr] = capitalizer(sample[attr])
            elif attr != 'hassample' and attr != 'issource':
                self.G.nodes[sourceid][attr] = capitalizer(source[attr])
                self.G.nodes[sampleid][attr] = capitalizer(sample[attr])

        #optimization possible, not call this every time but only when necessary
        self.updateSampleCounts()

        #self._splitGraph()

    #method to save graph to gdb file
    #param# path : str
    def writeGraph(self, path):
        nx.write_gml(self.G, path)

    #recursive method for depth first search from root, used for export parsing to .mm file
    #param# lines : list, tabs : str of repeated \t, root : str
    def _dfs(self, lines, tabs, root): #recursive dfs
        tracknames = nx.get_node_attributes(self.G, 'trackname')
        artists = nx.get_node_attributes(self.G, 'artist')
        years = nx.get_node_attributes(self.G, 'year')
        print(tabs + artists[root] + " - " + tracknames[root] + " - " + years[root])
        lines.append(tabs + artists[root] + " - " + tracknames[root] + " - " + years[root])
        for node in self.G._succ[root]:
            if node != root:
                self._dfs(lines, tabs+"\t", node)

    #method for exporting graph to mm file
    #param# path : str
    def exportGraph(self, path):
        lines = []
        for n in self.G.nodes:
            if len(self.G._pred[n]) == 0: #no predecessors = is root
                self._dfs(lines, "\t", n)
        with open(path, "w") as f:
            convert_lines_into_mm(lines, f)

if __name__ == '__main__':

    import sys
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    app.setWindowIcon(QIcon("3DIcon.png")) 
    #app.setStyle(QStyleFactory.create("gtk"))
    graphdatabase = GraphDatabase()
    if len(sys.argv) > 1:
        mainwindow = MainWindow(graphdatabase, sys.argv[1])
    else:
        mainwindow = MainWindow(graphdatabase)
    sys.exit(app.exec())