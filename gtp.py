from ui_gtp import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets
import time,os,csv
import yaml

class crawl(Ui_MainWindow):
	def __init__(self, dial):
		super(Ui_MainWindow, self).__init__()
		self.setupUi(dial)
		self.retranslateUi(dial)
		# TODO: data dict, avoid duplicates, continue????
		# TODO: save data
		
		# Main
		self.urlLineEdit.setText("")
		self.goButton.clicked.connect(self.urlGo)
		self.getButton.clicked.connect(self.getData)
		
		# Project
		self.projectNameLineEdit.setText("")
		self.newProjectButton.clicked.connect(self.newProject)
		self.openProjectButton.clicked.connect(self.openProjectGUI)
		self.saveProjectButton.clicked.connect(self.saveProjectGUI)
		
		# Navigation
		self.linksQueryLineEdit.setText("")
		self.linksButton.clicked.connect(self.getLinks)
		self.nextQueryLineEdit.setText("")
		self.nextTextLineEdit.setText("")
		self.testLinksButton.clicked.connect(self.nextPage)
		self.baseURLineEdit.setText("")
		self.delaySpinBox.valueChanged.connect(self.delay)
		self.linksTableWidget.setRowCount(1000)
		self.linksTableWidget.setColumnCount(2)
		self.removeLinksButton.clicked.connect(self.removeLinks)
		self.clearLinksButton.clicked.connect(self.clearLinks)
		self.autoLinksButton.clicked.connect(self.autoLinks)
		
		# Data Collection
		#
		self.dataQueryLineEdit.setText("")
		self.addDataQueryButton.clicked.connect(self.addDataQuery)
		self.testDataQueryButton.clicked.connect(self.testDataQuery)
		self.dataQueryListWidget.clear()
		self.removeDataQueryButton.clicked.connect(self.dataQueryRemove)
		self.clearDataQueryButton.clicked.connect(self.clearDataQuery)
		
		# Data
		#
		self.dataTableWidget.setRowCount(1000)
		self.dataTableWidget.setColumnCount(2)
		self.removeDataButton.clicked.connect(self.removeData)
		self.clearDataButton.clicked.connect(self.clearData)
		# self.saveDataButton
		
		self.status = dial.statusBar()
		self.gtpWebView.loadFinished.connect(self.autoSelector)
		self.pageDelay = 0
		self.linksCounter = 0
		self.currentLink = 0
		self.data = {} # url:[]
		self.links = {}
		self.project = ""
		self.mode = "" # "links" or "data"
		if os.path.exists("lastProject.conf"):
			f = open("lastProject.conf")
			self.project = f.read()
			self.projectNameLineEdit.setText(self.project)
			self.openProject()
			f.close()
	
	# Main
	def urlGo(self):
		self.gtpWebView.setUrl(QtCore.QUrl(self.urlLineEdit.text()))
		
	# Project
	def newProject(self):
		self.project = ""
		self.projectNameLineEdit.setText("")
		f = open("lastProject.conf",'w')
		f.write("")
		f.close()
		
		self.clearLinks()
		self.urlLineEdit.setText("")
		self.linksQueryLineEdit.setText("")
		self.nextQueryLineEdit.setText("")
		self.baseURLineEdit.setText("")
	
	def openProjectGUI(self):
		dlg = QtWidgets.QFileDialog()
		fileName = dlg.getOpenFileName(dlg, "Open File",".", "Projects (*.proj)")
		
		if fileName:
			self.project = fileName[0]
			f = open("lastProject.conf",'w')
			f.write(self.project)
			f.close()
			self.projectNameLineEdit.setText(fileName[0])
			self.openProject()
			
	def saveProjectGUI(self):
		if self.project:
			f = open("lastProject.conf",'w')
			f.write(self.project)
			f.close()
			self.saveProject()
			return
			
		dlg = QtWidgets.QFileDialog()
		fileName = dlg.getSaveFileName(dlg, "Save File",".", "Projects (*.proj)")
		if fileName:
			# create dir
			oldpath, name = os.path.split(fileName[0])
			parts = name.split(".")
			parts = ".".join(parts[:-1])
			newFolder = os.path.join(oldpath, parts)
			if not os.path.exists(newFolder):
				os.mkdir(newFolder)
			
			self.project = os.path.join(newFolder,name)
			self.projectNameLineEdit.setText(self.project)

			f = open("lastProject.conf",'w')
			f.write(self.project)
			f.close()
			
			self.saveProject()
	
	def openProject(self):
		if os.path.exists(self.project):
			
			folder, name = os.path.split(self.project)
			f = open(self.project,'r')
			data = yaml.load(f)
			f.close()
			
			self.urlLineEdit.setText(data["URL"])# save URL in proj yaml
			self.linksQueryLineEdit.setText(data["links query"])# save link query in proj yaml
			self.nextQueryLineEdit.setText(data["next css query"])# save next query in proj yaml
			self.nextTextLineEdit.setText(data["next text query"])# save next query in proj yaml
			self.baseURLineEdit.setText(data["base URL"])
			self.delaySpinBox.setValue(data["delay"])
			for d in data["data query"]:
				self.dataQueryListWidget.addItem(d)
			self.dataTableWidget.setColumnCount(self.dataQueryListWidget.count()+1)

			pth,name = os.path.split(self.project)
			newPath = os.path.join(pth,"links.csv")
			
			self.clearLinks()
			with open(newPath, 'r') as f:
				reader = csv.reader(f)
				for el in reader:
					self.links[el[1]] = el[0]
					a=QtWidgets.QTableWidgetItem(el[1])
					b=QtWidgets.QTableWidgetItem(el[0])
					self.linksTableWidget.setItem(self.linksCounter,0,a)
					self.linksTableWidget.setItem(self.linksCounter,1,b)
					self.linksCounter+=1
					
					if self.linksTableWidget.rowCount()<self.linksCounter+1000:
						self.linksTableWidget.setRowCount(1000+self.linksTableWidget.rowCount())
					
			self.dataTableWidget.setRowCount(1000+self.linksCounter)
			self.gtpWebView.setUrl(QtCore.QUrl(self.urlLineEdit.text()))
			
	def saveProject(self):
		data = {
			# Page Navigation
			"URL":self.urlLineEdit.text(),# save URL in proj yaml
			"links query":self.linksQueryLineEdit.text(),# save link query in proj yaml
			"next css query":self.nextQueryLineEdit.text(),# save next query in proj yaml
			"next text query":self.nextTextLineEdit.text(),# save next query in proj yaml
			"base URL":self.baseURLineEdit.text(),
			"delay":self.delaySpinBox.value(),
			# Data Collection
			"data query":[],# save data query in proj yaml
		}
		for n in range(self.dataQueryListWidget.count()):
			data["data query"].append(self.dataQueryListWidget.item(n).text())
			
		folder, name = os.path.split(self.project)
		f = open(self.project,'w')
		yaml.dump(data, f)
		f.close()
		
		# save links to csv
		pth,name = os.path.split(self.project)
		newPath = os.path.join(pth,"links.csv")
		with open(newPath, 'w') as f:
			writer = csv.writer(f)
			for k,v in self.links.items():
				writer.writerow([k,v])
		# create data.csv csv
		
	#Navigation
	def delay(self):
		self.pageDelay = self.delaySpinBox.value()
		
	def removeLinks(self):
		for item in self.linksTableWidget.selectedItems():
			row = item.row()
			href = self.linksTableWidget.item(row,1).text()
			del self.links[href] 
			self.linksCounter -= 1
			self.linksTableWidget.removeRow(row)
		
	def nextPage(self):
		query = self.nextQueryLineEdit.text()
		txt = self.nextTextLineEdit.text()
		found = False
		for element in self.gtpWebView.page().mainFrame().findAllElements(query):
			el_txt = element.toPlainText()
			if txt in el_txt:
				href = element.attribute("href")
				newURL = self.baseURLineEdit.text()+href
				self.gtpWebView.setUrl(QtCore.QUrl(newURL))
				found = True
				break
		if not found:
			self.mode = ""
		
	def clearLinks(self):
		self.linksCounter = 0
		self.links = {}
		self.linksTableWidget.clear()
		
	def getLinks(self):
		query = self.linksQueryLineEdit.text()
		
		for element in self.gtpWebView.page().mainFrame().findAllElements(query):
			txt = element.toPlainText()
			href = element.attribute("href")
			if href not in self.links:
				a=QtWidgets.QTableWidgetItem(txt)
				b=QtWidgets.QTableWidgetItem(href)
			
				self.links[href] = txt
				self.linksTableWidget.setItem(self.linksCounter,0,a)
				self.linksTableWidget.setItem(self.linksCounter,1,b)
				self.linksCounter+=1
				if self.linksTableWidget.rowCount()<self.linksCounter+1000:
					self.linksTableWidget.setRowCount(1000+self.linksTableWidget.rowCount())
			
	
	def getEmails(self):
		if len(self.sorras)>0:
			href = self.sorras.pop()
			self.dat = [href,]
			self.gtpWebView.loadFinished.connect(self.lfinish)
			self.gtpWebView.setUrl(QtCore.QUrl(href))
	
	def autoLinks(self):
		self.mode = "links"
		self.getLinks()
		self.status.showMessage("Links:"+str(self.linksCounter))
		self.nextPage()
		
	def autoSelector(self):
		time.sleep(self.pageDelay)
		if self.mode == "links":
			self.autoLinks()
		elif self.mode == "data":
			self.autoData()
		
	# Data Collection
	def testDataQuery(self, row=0):
		if row==False:
			row = 0
		if row==0:
			self.clearData()
		url = self.baseURLineEdit.text()+self.linksTableWidget.item(row,1).text()
		self.data[url] = []
		self.dataTableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(url))
		for column in range(self.dataQueryListWidget.count()):
			query = self.dataQueryListWidget.item(column)
			txt = []
			for element in self.gtpWebView.page().mainFrame().findAllElements(query.text()):
				txt.append(element.toPlainText())
			data = QtWidgets.QTableWidgetItem(", ".join(txt))
			self.data[url].append(data)
			self.dataTableWidget.setItem(row, column+1, data)
				
	def addDataQuery(self):
		self.dataQueryListWidget.addItem(self.dataQueryLineEdit.text())
		self.dataTableWidget.setColumnCount(self.dataQueryListWidget.count()+1)
		self.dataQueryLineEdit.setText("")
	
	def dataQueryRemove(self):
		row = self.dataQueryListWidget.currentRow()
		self.dataQueryListWidget.takeItem(row)
		self.dataTableWidget.setColumnCount(self.dataQueryListWidget.count()+1)
	
	def clearDataQuery(self):
		self.dataQueryListWidget.clear()
		self.dataTableWidget.setColumnCount(1)
		
	# Data
	def clearData(self):
		self.data.clear()
		self.dataTableWidget.clear()
		
	def removeData(self):
		for item in self.dataTableWidget.selectedItems():
			row = item.row()
			url = self.dataTableWidget.item(row,0).text()
			del self.data[url]
			self.dataTableWidget.removeRow(row)
	
	def getData(self):
		self.currentLink = 0
		self.mode = "data"
		self.dataTableWidget.setRowCount(1000+self.linksCounter)
		url = self.baseURLineEdit.text()+self.linksTableWidget.item(self.currentLink,1).text()
		while url in self.data:
			self.currentLink += 1
			url = self.baseURLineEdit.text()+self.linksTableWidget.item(self.currentLink,1).text()
		self.gtpWebView.setUrl(QtCore.QUrl(url))
		
	def autoData(self):
		self.status.showMessage("Data:"+str(self.currentLink))
		# get Data
		self.testDataQuery(self.currentLink)
		self.currentLink += 1
		if self.currentLink>self.linksCounter :
			self.mode = ""
			return
		# load link
		url = self.baseURLineEdit.text()+self.linksTableWidget.item(self.currentLink,1).text()
		while url in self.data:
			self.currentLink += 1
			url = self.baseURLineEdit.text()+self.linksTableWidget.item(self.currentLink,1).text()
		self.gtpWebView.setUrl(QtCore.QUrl(url))
		
if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()
	ui = crawl(MainWindow)
	MainWindow.show()
	
	sys.exit(app.exec_())