from __future__ import unicode_literals
import newcrawl
import yaml
from PyQt5 import QtCore, QtWidgets
from bs4 import BeautifulSoup
import youtube_dl
import csv,os,urllib.request

class MyLogger(object):
	def debug(self, msg):
		#print(msg)
		pass
	def warning(self, msg):
		pass
	def error(self, msg):
		print(msg)

class crawl(newcrawl.Ui_Dialog):
	def __init__(self, dial):
		super(crawl, self).__init__()
		self.setupUi(dial)
		self.retranslateUi(dial)
		
		self.removeButton.clicked.connect(self.removeRule)
		
		self.runButton.clicked.connect(self.collectPages)
		self.pageButton.clicked.connect(self.getPage)
		self.pagerButton.clicked.connect(self.collectPages)
		self.targetBrowser.loadFinished.connect(self.pageReady)
		
		self.testButton.clicked.connect(self.testelement)
		self.addRemoveButton.clicked.connect(self.addRemove)
		
		self.addButton.clicked.connect(self.addRule)
		self.goButton.clicked.connect(self.loadUrl)
		self.lineEdit.setText("https://el.wiktionary.org/wiki/%CE%9A%CE%B1%CF%84%CE%B7%CE%B3%CE%BF%CF%81%CE%AF%CE%B1:%CE%95%CF%80%CE%AF%CE%B8%CE%B5%CF%84%CE%B1_%28%CE%B5%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA%CE%AC%29")
		self.sourceBrowser.setUrl(QtCore.QUrl("https://el.wiktionary.org/wiki/%CE%9A%CE%B1%CF%84%CE%B7%CE%B3%CE%BF%CF%81%CE%AF%CE%B1:%CE%95%CF%80%CE%AF%CE%B8%CE%B5%CF%84%CE%B1_%28%CE%B5%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA%CE%AC%29"))
		self.sourceBrowser.selectionChanged.connect(self.sele)
		
		self.treeWidget.setColumnCount(2)
		header = QtWidgets.QTreeWidgetItem(["Element","Class"])
		self.treeWidget.setHeaderItem(header)
		self.treeWidget.itemClicked.connect(self.target)
		
		self.mframe = self.sourceBrowser.page().mainFrame()
		self.targetframe = self.targetBrowser.page().mainFrame()
		
		self.ruleTableWidget.setColumnCount(3)
		self.ruleTableWidget.setHorizontalHeaderLabels(["Selector","Role","URL"])
		self.ruleTableWidget.itemSelectionChanged.connect(self.ruleselect)
		self.ruleTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self.ruleTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		
		self.rulesLineEdit.textEdited.connect(self.detable)
		
		self.progressBar.setMaximum(100)
		self.progressBar.setMinimum(0)
		self.progressBar.setValue(0)
		
		self.currentRule = [{"el":"","class":[]},{"el":"","class":[]},{"el":"","class":[]}]
		self.topLvl = None
		
		self.selides = []
		self.rules = []
		self.video_name = ""
		if os.path.exists('crawl.yaml'):
			stream = open('crawl.yaml', 'r')
			self.rules = yaml.load(stream)
			stream.close()
			
			self.ruleTableWidget.setRowCount(len(self.rules))
			row = 0
			for rule in self.rules:
				self.ruleTableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(rule[0]))
				self.ruleTableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(rule[1]))
				self.ruleTableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(rule[2]))
				row+=1
		
	def collectPages(self):
		titles, page = "", ""
		print("phase 1")
		# Content Filter		
		rows = self.ruleTableWidget.rowCount()
		for row in range(rows):
			typ = self.ruleTableWidget.item(row, 1).text()
			value = self.ruleTableWidget.item(row, 0).text()
			if typ=="Titles Collector":
				titles = value
			elif typ=="Page Changer":
				page = value
		
		titls = self.mframe.findAllElements(titles+" a")
		for title in titls:
			selida = [title.toPlainText(), title.attribute("href")]
			self.selides.append(selida)
		
		
		pages = self.mframe.findAllElements(page+" a")
		for p in pages:
			self.sourceBrowser.setUrl(QtCore.QUrl(p.attribute("href")))
			
	def detable(self):
		row = self.ruleTableWidget.currentRow()
		if row>-1:
			self.ruleTableWidget.setCurrentCell(-1,-1)
		
	def saveRules(self):
		stream = open('crawl.yaml', 'w')
		yaml.safe_dump(self.rules, stream, encoding='utf-8', allow_unicode=True)
		stream.close()
		
	def removeRule(self):
		row = self.ruleTableWidget.currentRow()
		self.ruleTableWidget.removeRow(row)
		self.rules.remove(self.rules[row])
		self.saveRules()
	
	def ruleselect(self):
		row = self.ruleTableWidget.currentRow()
		if row<0:
			return
		self.rulesLineEdit.setText(self.ruleTableWidget.item(row,0).text())
		self.roleComboBox.setCurrentText(self.ruleTableWidget.item(row,1).text())
		self.lineEdit.setText(self.ruleTableWidget.item(row,2).text())
		
	def addRule(self):
		rule = self.rulesLineEdit.text()
		role = self.roleComboBox.currentText()
		url = self.lineEdit.text()
		row = self.ruleTableWidget.rowCount()+1
		self.ruleTableWidget.setRowCount(row)
		self.ruleTableWidget.setItem(row-1, 0, QtWidgets.QTableWidgetItem(rule))
		self.ruleTableWidget.setItem(row-1, 1, QtWidgets.QTableWidgetItem(role))
		self.ruleTableWidget.setItem(row-1, 2, QtWidgets.QTableWidgetItem(url))
		self.rules.append([rule, role, url])
		self.saveRules()
		
	def addRemove(self):
		cls = self.classComboBox.currentText()
		if not cls:
			self.updateTestLine()
			return
		item = self.treeWidget.currentItem()
		if not item:
			return
		c=2
		if not item.parent():
			c=0
		elif not item.parent().parent():
			c=1
		if cls in self.currentRule[c]["class"]:
			self.currentRule[c]["class"].remove(cls)
		else:
			self.currentRule[c]["class"].append(cls)
			
		self.updateTestLine()
		
	def target(self, item, col):
		if not item.parent():
			if self.topLvl != item:
				self.currentRule = [{"el":"","class":[]},{"el":"","class":[]},{"el":"","class":[]}]
				self.topLvl = item
				self.currentRule[0]["el"] =  item.text(0)
		elif not item.parent().parent():
			self.currentRule[1]["el"] = item.text(0)
		elif not item.parent().parent().parent():
			self.currentRule[2]["el"] =  item.text(0)
		
		self.classComboBox.clear()
		if item.text(1)!=None and item.text(1)!="None":
			self.classComboBox.addItems(eval(item.text(1)))
		self.updateTestLine()
		
	def updateTestLine(self):
		lvl1 = self.currentRule[0]["el"]
		if self.currentRule[0]["class"]:
			lvl1 +="."+".".join(self.currentRule[0]["class"])
		
		if self.currentRule[1]["el"]:
			lvl1 = lvl1+" > " + self.currentRule[1]["el"]
			#print("self.currentRule[1][class]:",self.currentRule[1]["class"])
			if self.currentRule[1]["class"]:
				lvl1 +="."+".".join(self.currentRule[1]["class"])
			
		if self.currentRule[2]["el"]:
			lvl1 = lvl1+" > " + self.currentRule[2]["el"]
			if self.currentRule[2]["class"]:
				lvl1 +="."+".".join(self.currentRule[2]["class"])
		
		self.rulesLineEdit.setText(lvl1)
		
	def my_hook(self, d):
		#print("progress",d.keys())
		#print("status",d["status"])
		#print("total_bytes",d["total_bytes"])
		if "downloaded_bytes" in d and "total_bytes" in d:
			p = int(100*d["downloaded_bytes"]/d["total_bytes"])
			self.progressBar.setValue(p)
		self.video_name = d["filename"]
		if d['status'] == 'finished':
			print('Done downloading, now converting ...')
			
	def testelement(self):
		main = self.rulesLineEdit.text()
		acc = ""
		for element in self.mframe.findAllElements(main):
			acc += element.toOuterXml()
		self.targetBrowser.setHtml(acc)
	
	def getPage(self):
		print("getpage")
		if self.selides:
			url = self.selides.pop()[1]
			self.targetBrowser.setUrl(QtCore.QUrl(url))
		
	def pageReady(self):
		rows = self.ruleTableWidget.rowCount()
		selector = ""
		for row in range(rows):
			typ = self.ruleTableWidget.item(row, 1).text()
			value = self.ruleTableWidget.item(row, 0).text()
			if typ=="Main Page":
				selector = value
			elif typ=="Remove Content":
				for element in self.targetframe.findAllElements(value):
					element.setOuterXml("")
		title = self.getTitle(self.targetframe, self.targetBrowser)
		path = title+"_files"
		if not os.path.exists(path):
			os.mkdir(path)
		refer= self.readRefer(path)
		acc = ""
		for elemen in self.targetframe.findAllElements(selector):
			element = elemen.clone()
			# Save images
			self.saveImages(element.findAll("img"),refer, path)
			# Save videos
			self.saveVideos(element.findAll("iframe.youtube-player"),refer,path)
			acc += element.toOuterXml()
		# Write refer
		self.writeRefer(path,refer)
		# Save Page
		self.writeHtml(title+".html",acc)
		self.getPage()
	
	def getTitle(self, frame, browser):
		elements = frame.findAllElements("title")
		title = browser.url().toString().split("://")
		if len(title)>1:
			title=title[1].replace("/","_").strip()
		else:
			title="title"
		for el in elements:
			title = el.toPlainText().strip()
			break
		return title
		
	def testpage(self):
		acc, main = "", ""
		# Content Filter
		row = self.ruleTableWidget.currentRow()
		if row>-1:
			laws = self.ruleTableWidget.selectedRanges()
			for law in laws:
				for row in range(law.topRow(),law.bottomRow()+1):
					typ = self.ruleTableWidget.item(row, 1).text()
					value = self.ruleTableWidget.item(row, 0).text()
					if typ=="Main Page":
						main = value
					elif typ=="Remove Content":
						for element in self.mframe.findAllElements(value):
							element.setOuterXml("")
		else:
			main = self.rulesLineEdit.text()
		# Title extractor
		title = self.getTitle(self.mframe, self.sourceBrowser)
		# Image Filter
		dr = title+"_files"
		if not os.path.exists(dr):
			os.mkdir(dr)
		refer= self.readRefer(dr)
		for elemen in self.mframe.findAllElements(main):
			element = elemen.clone()
			# Save images
			self.saveImages(element.findAll("img"),refer,dr)
			# Save videos
			self.saveVideos(element.findAll("iframe.youtube-player"),refer,dr)
			acc += element.toOuterXml()
		# Write refer
		self.writeRefer(dr,refer)
		# Save Page
		self.writeHtml(title+".html",acc)
		# Update target browser
		self.targetBrowser.setHtml(acc)
	
	def readRefer(self, dr):
		refer = {}
		ref = os.path.join(dr,'reference.csv')
		if os.path.exists(ref):
			with open(ref) as csvfile:
				for row in csv.reader(csvfile):
					refer[row[0]] = row[1]
		return refer
	
	def writeHtml(self,name,acc):
		f=open(name,'w')
		f.write(acc)
		f.close()
		
	def writeRefer(self,dr,refer):
		with open(os.path.join(dr,'reference.csv'), 'w') as csvfile:
			writer = csv.writer(csvfile)
			for k,v in refer.items():
				writer.writerow([k, v])
				
	def saveVideos(self, videos, refer, dr):
		for video in videos:
			video_src = video.attribute("src").split("?")[0]
			if video_src in refer:
				new_src = refer[video_src]
			else:
				ydl_opts = {
					'logger': MyLogger(),
					'progress_hooks': [self.my_hook],
				}
				with youtube_dl.YoutubeDL(ydl_opts) as ydl:
					ydl.extract_info(video_src, download=True )
					#for k,v in result.items():
						#print(k,"=",v)
					#ydl.download([video_src])
					old_src = video_src.split("/")[1]+".mp4"
					new_src = os.path.join(dr, old_src)
					if os.path.exists(old_src):
						os.rename(old_src, new_src)
					refer[video_src] = new_src
			video.setOuterXml('<video width="320" height="240" controls src="'+new_src+'"></video>')
						
	def saveImages(self, images, refer, dr):
		for image in images:
			original = image.attribute("src").split("?")[0]
			if original in refer:
				pass
			else:
				try:
					x = urllib.request.urlopen(original)
					filename = os.path.join(dr, original.split("/")[-1])
					refer[original] = filename
					saveFile = open(filename,'wb')
					saveFile.write(x.read())
					saveFile.close()
				except Exception as e:
					print(str(e))
			image.setAttribute("src", refer[original])
		
	def sele(self):
		html = self.sourceBrowser.selectedHtml() 
		#print(html)
		soup = BeautifulSoup(html, 'html.parser')
		
		self.treeWidget.clear()
		header = []
		for i in soup.contents:
			if i.name == None:
				continue
			item = QtWidgets.QTreeWidgetItem([i.name,str(i.get('class'))])
			for z in i.contents:
				try:
					item2 = QtWidgets.QTreeWidgetItem([z.name,str(z.get('class'))])
					for x in z.contents:
						item3 = QtWidgets.QTreeWidgetItem([x.name,str(x.get('class'))])
						item2.addChild(item3)
					item.addChild(item2)
				except:
					pass
			header.append(item)
			
		self.treeWidget.addTopLevelItems(header)
		#wel = soup.findAll("li","rr_method_list")
		
	def loadUrl(self):
		self.sourceBrowser.setUrl(QtCore.QUrl(self.lineEdit.text()))
	
if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication(sys.argv)
	Dialog = QtWidgets.QDialog()
	ui = crawl(Dialog)
	Dialog.show()
	
	sys.exit(app.exec_())