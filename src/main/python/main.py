from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QObject, QThread, pyqtSignal,Qt
from PyQt5.uic import loadUi

import sys
import os
import tarfile

proj_dict={}

class Worker(QObject):
    finished = pyqtSignal()
    countChanged = pyqtSignal(int)

    def run(self):
        num_parts = proj_dict['parts']
        t = tarfile.open(proj_dict['archive_file'], "r")

        (total_file_size, chunk_size) = self.get_chunk_size(t, num_parts)

        print(total_file_size)
        print(chunk_size)

        size = 0
        current_chunk = 1
        num_files_in_current_chunk = 0
        num_files = len(t.getmembers())
        num_files_done = 0

        for f in t.getmembers():
            name = f.name
            size += f.size
            print(name)

            if name[len(name) - 1] == "/":
                pass
            else:

                f = t.extractfile(name)
                info = t.getmember(name)
                out.addfile(info, f)

                if current_chunk < num_parts:
                    if size >= chunk_size:
                        out.close()

                        size = 0
                        current_chunk += 1
                        num_files_done += 1
                        num_files_in_current_chunk = 0
                        (filename, out) = self.open_chunkfile(original_tar_file, current_chunk, num_parts)
                    
                    percent = int(100 * num_files_done/num_files)
                    self.countChanged.emit(percent)
            



    def get_chunk_size(t, num):

        total_file_size = 0
        for f in t.getmembers():
            total_file_size += f.size

        retval = (total_file_size, int(total_file_size / num))
	
        return(retval)

    def open_chunkfile(file, part, num):
        global proj_dict

        folder = proj_dict['folder']
        num_len = len(str(num))
        part_formatted = str(part).zfill(num_len)
        filename = os.path.join(folder, f"{os.path.basename(file)}-part-{part_formatted}-of-{num}")
        out = tarfile.open(filename, "w")

        return(filename, out)

class Splitar(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()

    def setupUI(self):  
        loadUi(main_ui, self)  
        self.setWindowTitle('Splitar')
        self.setContentsMargins(12,6,12,6)
        self.load_pushButton.clicked.connect(self.load_archive)
        
    def load_archive(self):
        global proj_dict
        self.archive_file = QFileDialog.getOpenFileName(self, "Choose archive file")[0]
        proj_dict['archive_file'] = self.archive_file
        self.archive_lineEdit.setText(self.archive_file)
        self.buttonBox.accepted.connect(self.run)

    def run(self):
        global proj_dict
        self.parts = self.parts_spinBox.value()
        proj_dict['part'] = self.parts
        self.textBrowser.append("<span>Welcome to Tarsplit!</span>")
        self.textBrowser.append("<span>Reading file "+self.archive_file+" </span>")

        path_file = os.path.split(proj_dict['archive_file'])
        basename = os.path.splitext(os.path.basename(proj_dict['archive_file']))[0]


        folder = path_file[0]
        os.makedirs(os.path.join(folder, basename))
        folder = os.path.join(folder, basename)
        proj_dict['folder'] = folder

        self.thread = QThread()
        self.worker = Worker() 
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.countChanged.connect(self.progress)


    def progress(self, value):
        self.progressBar.setValue(value)





        






    

if __name__ == '__main__':

    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

    main_ui = appctxt.get_resource('splitar_gui.ui')
    instruction_file = appctxt.get_resource('instructions.txt')

    window = Splitar()
    window.show()
    exit_code = appctxt.app.exec()      # 2. Invoke appctxt.app.exec()
    sys.exit(exit_code)