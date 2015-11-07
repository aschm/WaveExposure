import tkinter as tk
from tkinter.filedialog import FileDialog

import os
import time

import logging
import logging.config

import xml.etree.ElementTree as ET


from WaveExposure import WaveExposure

logging.config.fileConfig('logging.conf')


class ExposureGui(tk.Frame):
	headerSetting = {}
	headerSetting['ipadx'] = 10

	entrySettings = {}
	entrySettings['sticky'] = tk.E+tk.W

	labelSettings = {}
	labelSettings ['ipadx'] = 5
	labelSettings ['sticky'] = tk.W

	buttonSettings = {}
	buttonSettings ['padx'] = 5
	#buttonSettings ['sticky'] = tk.E

	def __init__(self, master = None):
		self.logger = logging.getLogger(__name__)
		self.logger.debug('Create MainFrame')
		tk.Frame.__init__(self,master)
		self.top = self.winfo_toplevel()
		"""
		self.top.rowconfigure(0,weight=1)
		self.top.columnconfigure(0,weight=1)

		self.rowconfigure(0,weight=1)
		self.columnconfigure(0,weight=1)
		self.rowconfigure(1,weight=1)
		self.columnconfigure(1,weight=1)

		"""
		self.exposure = WaveExposure()

		#self.top.geometry('640x480+10+10')
		self.master.title('Wave Exposure Calculation')
		self.pack()
		self.createWidgets()

	def createWidgets(self):

		self.start = tk.Button(self,text='Start',
			command=self.startCalculation)
		self.start.grid(column=0, row=2)

		self.createSettingsFrame()

		self.QUIT = tk.Button(self, text='QUIT', command=self.quit)
		self.QUIT.grid(column=1,row=2)


	def startCalculation(self):
		self.logger.debug('Start Wave Exposure Calculation')
		self.start['state'] = tk.DISABLED

		self.exposure.setDegree(self.degVar.get())
		self.exposure.setRayLength(self.lengthVar.get())
		self.exposure.setFilter(self.filterVar.get())

		self.exposure.setSourceFile(self.sourceFile.get())

		start = time.time()
		self.exposure.startExposureCalculation()


		if self.savingLines.get():
			self.exposure.saveMultiLineLayer(self.lineFile.get())

		if self.savingPoints.get():
			self.exposure.savePointLayer(self.pointFile.get())

		end = time.time()
		self.start['state'] = tk.NORMAL

		self.logger.debug('It took %s s' % (end-start))


	def createSettingsFrame(self):

		self.savingLines = tk.IntVar()
		self.savingLines.set(1)
		self.savingPoints = tk.IntVar()
		self.savingPoints.set(1)


		self.lineFile = tk.StringVar()
		self.lineFile.set('')

		self.pointFile = tk.StringVar()
		self.pointFile.set('')

		self.sourceFile = tk.StringVar()
		self.sourceFile.set('')

		self.filterVar = tk.StringVar()
		self.filterVar.set('Visited = 1')

		self.lengthVar = tk.IntVar()
		self.lengthVar.set(2000)

		self.degVar = tk.DoubleVar()
		self.degVar.set(15)

		self.logger.debug('Create createSettingsFrame')

		self.settingsFrame = tk.Frame(self)
		self.settingsFrame.grid(column=0,row=1,columnspan=2,sticky=tk.W+tk.E)

		self.inputSettingsFrame = tk.LabelFrame(self.settingsFrame,
				text = 'Input settings',
				padx = 5,
				pady = 5)
		self.inputSettingsFrame.grid(column=0,row=1,sticky=tk.W+tk.E)

		self.outputSettingsFrame = tk.LabelFrame(self.settingsFrame,
				text = 'Output settings',
				padx = 5,
				pady = 5)		
		self.outputSettingsFrame.grid(column=0,row=2,sticky=tk.W+tk.E)

		


		#Create Source File settings
		self.sourceFileLabel = tk.Label(self.inputSettingsFrame,
										text='Source file:')
		self.sourceFileLabel.grid(column=1,row=1,**self.labelSettings)


		
		validateCommand = self.register(self.validateSourceFile)
		self.sourceFileEntry = tk.Entry(self.inputSettingsFrame,
				width=40,
				textvariable = self.sourceFile,
				validate='focus',
				validatecommand=(validateCommand,'%P'))
		self.sourceFileEntry.grid(column=2,row=1, columnspan=1, **self.entrySettings)

		#Creates button to open FileMenu
		self.selectSourceFileButton = tk.Button(self.inputSettingsFrame,
												text='Select File',
												command=self.selectSourceFile)
		self.selectSourceFileButton.grid(column=4,row=1, **self.buttonSettings)


		self.lengthLabel = tk.Label(self.inputSettingsFrame,
			text='Ray length: ')
		self.lengthLabel.grid(column=1, row=2, **self.labelSettings)

		self.setLengthBox = tk.Spinbox(self.inputSettingsFrame,
			textvariable = self.lengthVar,
			from_= 1,
			to=50000,
			increment=1,
			width=10)
		self.setLengthBox.grid(column=2, row=2)


		self.degLabel = tk.Label(self.inputSettingsFrame,
			text='Degree: ')
		self.degLabel.grid(column=3, row=2, **self.labelSettings)

		self.setDegBox = tk.Spinbox(self.inputSettingsFrame,
			textvariable = self.degVar,
			from_= 0.1,
			to=359,
			increment=0.1,
			width=10)
		self.setDegBox.grid(column=4, row=2)

		self.filterFrame = tk.Frame(self.inputSettingsFrame)
		self.filterFrame.grid(column=1, row=3, columnspan=4)

		self.filterLabel = tk.Label(self.filterFrame,
			text='Filter by Attribute (e.g. Visited = 1): ')
		self.filterLabel.grid(column=1, row=1, **self.labelSettings)
		self.filterEntry = tk.Entry(self.filterFrame,
			textvariable = self.filterVar,
			width=40)
		self.filterEntry.grid(column=2, row=1)
		
		#Setting output files

		#Create labels
		self.activeLabel = tk.Label(self.outputSettingsFrame, text='Active')
		self.activeLabel.grid(column=0,row=0,**self.headerSetting)

		self.destinationLabel = tk.Label(self.outputSettingsFrame, text='Geometry Type')
		self.destinationLabel.grid(column=1,row=0,**self.headerSetting)

		self.filePathLabel = tk.Label(self.outputSettingsFrame, text='Destination file')
		self.filePathLabel.grid(column=2,row=0,**self.headerSetting)		

		#Output in Point shape
		self.pointFileCheckBox = tk.Checkbutton(self.outputSettingsFrame,
				text='',
				variable = self.savingPoints)
		self.pointFileCheckBox.grid(column=0,row=1,sticky=tk.N+tk.S)

		self.pointFileLabel = tk.Label(self.outputSettingsFrame,
										text='Point File')
		self.pointFileLabel.grid(column=1,row=1,**self.labelSettings)


		
		validatePoint = self.register(self.validatePointFile)
		self.pointFileEntry = tk.Entry(self.outputSettingsFrame,
				width=40,
				textvariable = self.pointFile,
				validate='all',
				validatecommand=(validatePoint,'%P'))
		self.pointFileEntry.grid(column=2,row=1,**self.entrySettings)

		#Creates button to open FileMenu
		self.pointSourceFileButton = tk.Button(self.outputSettingsFrame,
												text='Select File',
												command=self.savePointFileAs)
		self.pointSourceFileButton.grid(column=3,row=1, **self.buttonSettings)

		
		#Output MultiLine shape
		self.lineFileCheckBox = tk.Checkbutton(self.outputSettingsFrame,
				text='',
				variable = self.savingPoints)
		self.lineFileCheckBox.grid(column=0,row=2,sticky=tk.N+tk.S)

		self.lineFileLabel = tk.Label(self.outputSettingsFrame,
										text='MultiLine File')
		self.lineFileLabel.grid(column=1,row=2,**self.labelSettings)


		
		validateLine = self.register(self.validateLineFile)
		saveLineFileAs = self.register(self.saveFileAs)
		self.lineFileEntry = tk.Entry(self.outputSettingsFrame,
				width=40,
				textvariable = self.lineFile,
				validate='all',
				validatecommand=(validateLine,'%P'))
		self.lineFileEntry.grid(column=2,row=2,**self.entrySettings)

		#Creates button to open FileMenu
		self.lineSourceFileButton = tk.Button(self.outputSettingsFrame,
												text='Select File',
												command=self.saveLineFileAs)
		self.lineSourceFileButton.grid(column=3,row=2, **self.buttonSettings)

	def setDir(self,path):
		dirDict = {}
		if os.path.isdir(path):
			dirDict ['initialdir'] = path
		elif os.path.isfile(path):
			dirDict ['initialdir'] = os.path.dirname(path)
			dirDict ['initialfile'] = path
		else:
			dirDict ['initialdir'] = os.getcwd()
		return dirDict


	def savePointFileAs(self):
		self.saveFileAs(self.pointFile,fileName='Points.shp')
	
	def saveLineFileAs(self):
		self.saveFileAs(self.lineFile,fileName='MultLine.shp')
		


	def saveFileAs(self,variable,fileName='Output.shp',title = 'Save file as...'):
		options = {}
		options ['defaultextension'] = '.shp'
		options	['filetypes'] = [('Shape files', '.shp')]
		options	['parent'] = self
		options	['title'] = title

		if 'initialfile' not in options:
			options ['initialfile'] = fileName

		fname = tk.filedialog.asksaveasfilename(**options)

		if fname:

			variable.set(fname)
		else:
			self.logger.debug('Source file selections seems to be canceled')


	def selectSourceFile(self):
		options = {}
		options ['defaultextension'] = '.shp'
		options	['filetypes'] = [('Shape files', '.shp')]
		options	['multiple'] = False
		options	['parent'] = self
		options	['title'] = 'Open source file...'

		options.update(self.setDir(self.sourceFile.get()))

		fname = tk.filedialog.askopenfilename(**options)

		if fname:
			self.setSourceFile(fname)
		else:
			self.logger.debug('Source file selections seems to be canceled')

		

	def setSourceFile(self,fname):
		self.logger.debug('Set source file to %s' % fname)
		self.sourceFile.set(fname)
		
	
	def setPointFile(self,fname):
		self.logger.debug('Set point file to %s' % fname)
		self.pointFile.set(fname)

	def setLineFile(self,fname):
		self.logger.debug('Set MultiLine file to %s' % fname)
		self.lineFile.set(fname)


	def validateSourceFile(self,value):
		self.logger.debug('Validate if Source File string is a file: %s' % value)
		valid = os.path.isfile(value) and os.path.splitext(value)[1] == '.shp' and value != self.lineFile.get() and value != self.pointFile.get()
		if not valid:
			self.bell()
		else:
			self.logger.debug('Source File \'%s\' is a file' % value)
			self.setSourceFile(value)
			return valid

	def validatePointFile(self,value):
		self.logger.debug('Validate if Point File string is a file: %s' % value)
		valid = os.path.splitext(value)[1] == '.shp' and value != self.lineFile.get() and value != self.sourceFile.get()
		if not valid:
			self.bell()
		else:
			self.logger.debug('Point File \'%s\' is a file' % value)
			self.setPointFile(value)
			return valid

	def validateLineFile(self,value):
		self.logger.debug('Validate if MultiLine File string is a file: %s' % value)
		valid = os.path.splitext(value)[1] == '.shp' and  value != self.pointFile.get() and value != self.sourceFile.get()
		if not valid:
			self.logger.debug('MultiLine file is not valid!!!')
			self.bell()
		else:
			self.logger.debug('MultiLine File \'%s\' is a file' % value)
			self.setLineFile(value)
			return valid

	def saveSettings(self):
		open 
		json.dumps(self.settings)




if __name__ == '__main__':
	
	
	gui = ExposureGui()
	
	gui.mainloop()