"""
<name>Radviz</name>
<description>Shows data using radviz visualization method</description>
<category>Classification</category>
<icon>icons/Radviz.png</icon>
<priority>3130</priority>
"""
# Radviz.py
#
# Show data using radviz visualization method
# 

from OWWidget import *
from OWRadvizOptions import *
from random import betavariate 
from OWRadvizGraph import *
from OData import *
import orngFSS
import statc
import orngCI


###########################################################################################
##### WIDGET : Radviz visualization
###########################################################################################
class OWRadviz(OWWidget):
    settingsList = ["pointWidth", "attrContOrder", "attrDiscOrder", "jitteringType", "graphCanvasColor"]
    def __init__(self,parent=None):
        self.spreadType=["none","uniform","triangle","beta"]
        self.attributeContOrder = ["None","RelieF"]
        self.attributeDiscOrder = ["None","RelieF","GainRatio","Gini"]
        self.attributeOrdering  = ["Original", "Optimized class separation"]
        OWWidget.__init__(self,
        parent,
        "Radviz",
        "Show data using Radviz visualization method",
        TRUE,
        TRUE)

        #set default settings
        self.pointWidth = 3
        self.attrDiscOrder = "RelieF"
        self.attrContOrder = "RelieF"
        self.jitteringType = "none"
        self.attrOrdering = "Original"
        
        self.graphCanvasColor = str(Qt.white.name())
        self.data = None

        #load settings
        self.loadSettings()

        # add a settings dialog and initialize its values
        self.options = OWRadvizOptions()        

        #GUI
        #add a graph widget
        self.box = QVBoxLayout(self.mainArea)
        self.graph = OWRadvizGraph(self.mainArea)
        self.box.addWidget(self.graph)
        self.connect(self.graphButton, SIGNAL("clicked()"), self.graph.saveToFile)

        # graph main tmp variables
        self.addInput("cdata")

        #connect settingsbutton to show options
        self.connect(self.options.widthSlider, SIGNAL("valueChanged(int)"), self.setPointWidth)
        self.connect(self.settingsButton, SIGNAL("clicked()"), self.options.show)
        self.connect(self.options.spreadButtons, SIGNAL("clicked(int)"), self.setSpreadType)
        self.connect(self.options.attrContButtons, SIGNAL("clicked(int)"), self.setAttrContOrderType)
        self.connect(self.options.attrDiscButtons, SIGNAL("clicked(int)"), self.setAttrDiscOrderType)
        self.connect(self.options.attrOrderingButtons, SIGNAL("clicked(int)"), self.setAttrOrdering)
        self.connect(self.options, PYSIGNAL("canvasColorChange(QColor &)"), self.setCanvasColor)

        #add controls to self.controlArea widget
        self.selClass = QVGroupBox(self.controlArea)
        self.shownAttribsGroup = QVGroupBox(self.space)
        self.addRemoveGroup = QHButtonGroup(self.space)
        self.hiddenAttribsGroup = QVGroupBox(self.space)
        self.selClass.setTitle("Class attribute")
        self.shownAttribsGroup.setTitle("Shown attributes")
        self.hiddenAttribsGroup.setTitle("Hidden attributes")

        self.classCombo = QComboBox(self.selClass)
        self.showContinuousCB = QCheckBox('show continuous', self.selClass)
        self.connect(self.showContinuousCB, SIGNAL("clicked()"), self.setClassCombo)

        self.shownAttribsLB = QListBox(self.shownAttribsGroup)
        self.shownAttribsLB.setSelectionMode(QListBox.Extended)

        self.hiddenAttribsLB = QListBox(self.hiddenAttribsGroup)
        self.hiddenAttribsLB.setSelectionMode(QListBox.Extended)
        
        self.attrButtonGroup = QHButtonGroup(self.shownAttribsGroup)
        #self.attrButtonGroup.setFrameStyle(QFrame.NoFrame)
        #self.attrButtonGroup.setMargin(0)
        self.buttonUPAttr = QPushButton("Attr UP", self.attrButtonGroup)
        self.buttonDOWNAttr = QPushButton("Attr DOWN", self.attrButtonGroup)

        self.attrAddButton = QPushButton("Add attr.", self.addRemoveGroup)
        self.attrRemoveButton = QPushButton("Remove attr.", self.addRemoveGroup)

        #connect controls to appropriate functions
        self.connect(self.classCombo, SIGNAL('activated ( const QString & )'), self.updateGraph)

        self.connect(self.buttonUPAttr, SIGNAL("clicked()"), self.moveAttrUP)
        self.connect(self.buttonDOWNAttr, SIGNAL("clicked()"), self.moveAttrDOWN)

        self.connect(self.attrAddButton, SIGNAL("clicked()"), self.addAttribute)
        self.connect(self.attrRemoveButton, SIGNAL("clicked()"), self.removeAttribute)

        # add a settings dialog and initialize its values
        self.setOptions()

        #self.repaint()

    # #########################
    # OPTIONS
    # #########################
    def setOptions(self):
        self.options.spreadButtons.setButton(self.spreadType.index(self.jitteringType))
        self.options.attrContButtons.setButton(self.attributeContOrder.index(self.attrContOrder))
        self.options.attrDiscButtons.setButton(self.attributeDiscOrder.index(self.attrDiscOrder))
        self.options.gSetCanvasColor.setNamedColor(str(self.graphCanvasColor))
        self.options.attrOrderingButtons.setButton(self.attributeOrdering.index(self.attrOrdering))
        self.options.widthSlider.setValue(self.pointWidth)
        self.options.widthLCD.display(self.pointWidth)
        
        self.graph.setJitteringOption(self.jitteringType)
        self.graph.setPointWidth(self.pointWidth)
        self.graph.setCanvasColor(self.options.gSetCanvasColor)

    def setPointWidth(self, n):
        self.pointWidth = n
        self.graph.setPointWidth(n)
        self.updateGraph()
        
    # jittering options
    def setSpreadType(self, n):
        self.graph.setJitteringOption(self.spreadType[n])
        self.graph.setData(self.data)
        self.updateGraph()


    # continuous attribute ordering
    def setAttrContOrderType(self, n):
        self.attrContOrder = self.attributeContOrder[n]
        if self.data != None:
            self.setShownAttributeList(self.data)
        self.updateGraph()

    # discrete attribute ordering
    def setAttrDiscOrderType(self, n):
        self.attrDiscOrder = self.attributeDiscOrder[n]
        if self.data != None:
            self.setShownAttributeList(self.data)
        self.updateGraph()

    def setAttrOrdering(self, n):
        self.attrOrdering = self.attributeOrdering[n]
        if self.attrOrdering == "Optimized class separation" and self.data != None:
            list = self.graph.getOptimalAttrOrder(self.getShownAttributeList(), str(self.classCombo.currentText()))
            self.shownAttribsLB.clear()
            for item in list:
                self.shownAttribsLB.insertItem(item)
        elif self.data != None:
            ex_list = self.getShownAttributeList()
            self.shownAttribsLB.clear()
            for attr in self.data.domain:
                try:
                    ind = ex_list.index(attr.name)
                    self.shownAttribsLB.insertItem(attr.name)
                except: pass
                
        self.updateGraph()
        
    def setCanvasColor(self, c):
        self.graphCanvasColor = c
        self.graph.setCanvasColor(c)
        
    # ####################
    # LIST BOX FUNCTIONS
    # ####################

    # move selected attribute in "Attribute Order" list one place up
    def moveAttrUP(self):
        for i in range(self.shownAttribsLB.count()):
            if self.shownAttribsLB.isSelected(i) and i != 0:
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, i-1)
                self.shownAttribsLB.setSelected(i-1, TRUE)
        self.updateGraph()

    # move selected attribute in "Attribute Order" list one place down  
    def moveAttrDOWN(self):
        count = self.shownAttribsLB.count()
        for i in range(count-2,-1,-1):
            if self.shownAttribsLB.isSelected(i):
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, i+1)
                self.shownAttribsLB.setSelected(i+1, TRUE)
        self.updateGraph()

    def addAttribute(self):
        count = self.hiddenAttribsLB.count()
        pos   = self.shownAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.hiddenAttribsLB.isSelected(i):
                text = self.hiddenAttribsLB.text(i)
                self.hiddenAttribsLB.removeItem(i)
                self.shownAttribsLB.insertItem(text, pos)
        self.updateGraph()
        self.graph.replot()

    def removeAttribute(self):
        count = self.shownAttribsLB.count()
        pos   = self.hiddenAttribsLB.count()
        for i in range(count-1, -1, -1):
            if self.shownAttribsLB.isSelected(i):
                text = self.shownAttribsLB.text(i)
                self.shownAttribsLB.removeItem(i)
                self.hiddenAttribsLB.insertItem(text, pos)
        self.updateGraph()
        self.graph.replot()

    # #####################

    def updateGraph(self):
        self.graph.updateData(self.getShownAttributeList(), str(self.classCombo.currentText()))
        #self.graph.replot()
        self.graph.update()
        self.repaint()

    # set combo box values with attributes that can be used for coloring the data
    def setClassCombo(self):
        exText = str(self.classCombo.currentText())
        self.classCombo.clear()
        if self.data == None:
            return

        # add possible class attributes
        self.classCombo.insertItem('(One color)')
        for i in range(len(self.data.domain)):
            attr = self.data.domain[i]
            if attr.varType == orange.VarTypes.Discrete or self.showContinuousCB.isOn() == 1:
                self.classCombo.insertItem(attr.name)

        for i in range(self.classCombo.count()):
            if str(self.classCombo.text(i)) == exText:
                self.classCombo.setCurrentItem(i)
                return

        for i in range(self.classCombo.count()):
            if str(self.classCombo.text(i)) == self.data.domain.classVar.name:
                self.classCombo.setCurrentItem(i)
                return
        self.classCombo.insertItem(self.data.domin.classVar.name)
        self.classCombo.setCurrentItem(self.classCombo.count()-1)


    # ###### SHOWN ATTRIBUTE LIST ##############
    # set attribute list
    def setShownAttributeList(self, data):
        self.shownAttribsLB.clear()
        self.hiddenAttribsLB.clear()
        if data == None: return

        self.hiddenAttribsLB.insertItem(data.domain.classVar.name)
        
        ## RELIEF
        if self.attrContOrder == "RelieF" and self.attrDiscOrder == "RelieF":
            newAttrs = orngFSS.attMeasure(data, orange.MeasureAttribute_relief(k=20, m=50))
            for item in newAttrs:
                if float(item[1]) > 0.01:   self.shownAttribsLB.insertItem(item[0])
                else:                       self.hiddenAttribsLB.insertItem(item[0])
            return
        ## NONE
        elif self.attrContOrder == "None" and self.attrDiscOrder == "None":
            for item in data.domain.attributes:    self.shownAttribsLB.insertItem(item.name)
            return

        ###############################
        # sort continuous attributes
        if self.attrContOrder == "None":
            for item in data.domain:
                if item.varType == orange.VarTypes.Continuous: self.shownAttribsLB.insertItem(item.name)
        elif self.attrContOrder == "RelieF":
            newAttrs = orngFSS.attMeasure(data, orange.MeasureAttribute_relief(k=20, m=50))
            for item in newAttrs:
                if data.domain[item[0]].varType != orange.VarTypes.Continuous: continue
                if float(item[1]) > 0.01:   self.shownAttribsLB.insertItem(item[0])
                else:                       self.hiddenAttribsLB.insertItem(item[0])
        else:
            print "Incorrect value for attribute order"

        ################################
        # sort discrete attributes
        if self.attrDiscOrder == "None":
            for item in data.domain.attributes:
                if item.varType == orange.VarTypes.Discrete: self.shownAttribsLB.insertItem(item.name)
        elif self.attrDiscOrder == "RelieF":
            newAttrs = orngFSS.attMeasure(data, orange.MeasureAttribute_relief(k=20, m=50))
            for item in newAttrs:
                if data.domain[item[0]].varType != orange.VarTypes.Discrete: continue
                if item[0] == data.domain.classVar.name: continue
                if float(item[1]) > 0.01:   self.shownAttribsLB.insertItem(item[0])
                else:                       self.hiddenAttribsLB.insertItem(item[0])
        elif self.attrDiscOrder == "GainRatio" or self.attrDiscOrder == "Gini":
            if self.attrDiscOrder == "GainRatio":   measure = orange.MeasureAttribute_gainRatio()
            else:                                   measure = orange.MeasureAttribute_gini()
            if data.domain.classVar.varType != orange.VarTypes.Discrete:
                measure = orange.MeasureAttribute_relief(k=20, m=50)

            # create new table with only discrete attributes
            attrs = []
            for attr in data.domain.attributes:
                if attr.varType == orange.VarTypes.Discrete: attrs.append(attr)
            dataNew = data.select(attrs)
            newAttrs = orngFSS.attMeasure(dataNew, measure)
            for item in newAttrs:
                    self.shownAttribsLB.insertItem(item[0])
        else:
            print "Incorrect value for attribute order"

        #################################
        # if class attribute hasn't been added yet, we add it
        foundClass = 0
        for i in range(self.shownAttribsLB.count()):
            if str(self.shownAttribsLB.text(i)) == data.domain.classVar.name:
                foundClass = 1
        for i in range(self.hiddenAttribsLB.count()):
            if str(self.hiddenAttribsLB.text(i)) == data.domain.classVar.name:
                foundClass = 1
        if not foundClass:
            self.shownAttribsLB.insertItem(data.domain.classVar.name)

        self.setAttrOrdering(self.attributeOrdering.index(self.attrOrdering))

        
    def getShownAttributeList (self):
        list = []
        for i in range(self.shownAttribsLB.count()):
            list.append(str(self.shownAttribsLB.text(i)))
        return list
    ##############################################
    
    
    ####### CDATA ################################
    # receive new data and update all fields
    def cdata(self, data):
        self.data = orange.Preprocessor_dropMissing(data.data)
        self.graph.setData(self.data)
        self.shownAttribsLB.clear()
        self.hiddenAttribsLB.clear()
        self.setClassCombo()

        if self.data == None:
            self.repaint()
            return
        
        self.setShownAttributeList(self.data)
        self.updateGraph()
    #################################################

#test widget appearance
if __name__=="__main__":
    a=QApplication(sys.argv)
    ow=OWRadviz()
    a.setMainWidget(ow)
    ow.show()
    a.exec_loop()

    #save settings 
    ow.saveSettings()
