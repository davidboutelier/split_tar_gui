from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QObject, QThread, pyqtSignal,Qt
from PyQt5.uic import loadUi

import sys
import os
import tarfile
import humanize
import shutil
import io

proj_dict={}

class Worker(QObject):
    global proj_dict

    finished = pyqtSignal()
    countChanged = pyqtSignal(int)
    comm = pyqtSignal()

    def run(self):
        global proj_dict

        num_parts = proj_dict['parts']
        t = tarfile.open(proj_dict['archive_file'], "r")

        (total_file_size, chunk_size) = self.get_chunk_size(t, num_parts)

        msg = f"Total uncompressed file size: {humanize.naturalsize(total_file_size, binary = True)} bytes, " + f"num chunks: {num_parts}, chunk size: {humanize.naturalsize(chunk_size, binary = True)} bytes"
        proj_dict['msg'] = msg
        self.comm.emit()

        num_files = len(t.getmembers())
        num_files_done = 0
        size = 0
        current_chunk = 1
        num_files_in_current_chunk = 0

        (filename, out) = self.open_chunkfile(proj_dict['archive_file'], 1, num_parts)
        msg = f"Writing split tarfile: {current_chunk} of {num_parts}"
        proj_dict['msg'] = msg
        self.comm.emit()

        for f in t.getmembers():
            name = f.name
            size += f.size
            print(name)
            num_files_done += 1

            if name[len(name) - 1] == "/":
                msg = f"File {name} ends in Slash, skipping due to a bug in the tarfile module. (Directory will still be created by files within that directory)"
                proj_dict['msg'] = msg
                self.comm.emit()
                continue
            
            f = t.extractfile(name)
            info = t.getmember(name)
            out.addfile(info, f)
            num_files_in_current_chunk += 1

            if current_chunk < num_parts:
                if size >= chunk_size:
                    out.close()
                    msg = f"Successfully wrote {humanize.naturalsize(size, binary = True)}"+ f" bytes in {num_files_in_current_chunk} files to {filename}"
                    proj_dict['msg'] = msg
                    self.comm.emit()

                    size = 0
                    current_chunk += 1
                    num_files_in_current_chunk = 0
                    (filename, out) = self.open_chunkfile(proj_dict['archive_file'], current_chunk, num_parts)

                    msg = f"Writing split tarfile: {current_chunk} of {num_parts}"
                    proj_dict['msg'] = msg
                    self.comm.emit()

            percent = int(100 * num_files_done/num_files)
            self.countChanged.emit(percent)

        # after the last file    
        out.close()
        msg = f"Successfully wrote {humanize.naturalsize(size, binary = True)}"+ f" bytes in {num_files_in_current_chunk} files to {filename}"
        proj_dict['msg'] = msg
        self.comm.emit()

        self.finished.emit()




    def get_chunk_size(self,t, num):

        total_file_size = 0
        for f in t.getmembers():
            total_file_size += f.size

        retval = (total_file_size, int(total_file_size / num))
	
        return(retval)

    def open_chunkfile(self, file, part, num):
        global proj_dict

        folder = proj_dict['folder']
        num_len = len(str(num))
        #part_formatted = str(part).zfill(num_len)
        part_formatted = part
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
        self.buttonBox.accepted.connect(self.split)
        self.buttonBox.rejected.connect(self.close)
        
    def load_archive(self):
        global proj_dict
        self.archive_file = QFileDialog.getOpenFileName(self, "Choose archive file")[0]
        proj_dict['archive_file'] = self.archive_file
        self.archive_lineEdit.setText(self.archive_file)
        proj_dict['msg'] = None

    def split(self):
        global proj_dict
        self.parts = self.parts_spinBox.value()
        proj_dict['parts'] = self.parts
        self.textBrowser.append("<span>Welcome to Tarsplit!</span>")
        self.textBrowser.append("<span>Reading file "+self.archive_file+" </span>")

        path_file = os.path.split(proj_dict['archive_file'])
        basename = os.path.splitext(os.path.basename(proj_dict['archive_file']))[0]

        folder = path_file[0]
        folder = os.path.join(folder, basename)

        if not os.path.exists(folder):
            os.makedirs(os.path.join(folder))
        
        proj_dict['folder'] = folder

        self.thread = QThread()
        self.worker = Worker() 
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.complete)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.countChanged.connect(self.progress)
        self.worker.comm.connect(self.update_msg)
        self.thread.start()


    def progress(self, value):
        self.progressBar.setValue(value)



    def complete(self):
        self.progressBar.setValue(0)
        folder = proj_dict['folder']
        num_parts = proj_dict['parts']
        shutil.copy(instruction_file, os.path.join(folder, 'instructions.txt'))
        self.textBrowser.append("<span>Adding instruction on how to merge files back</span>")

        basename = os.path.basename(proj_dict['archive_file'])
        name = os.path.splitext(basename)[0]

        with open(os.path.join(folder, 'merge_parts.bat'), 'w') as f:
            f.write('@echo off\n')
            f.write('setlocal EnableDelayedExpansion\n')
            f.write('set "startTime=%time: =0%"\n')
            f.write('ECHO Creating folder: '+name+'\n')
            f.write('mkdir "'+name+'"\n')
            f.write('FOR /L %%A IN (1,1,'+str(num_parts)+') DO (\n')
            f.write('   mkdir part_%%A\n')
            f.write('   tar -xvf '+basename+'-part-%%A-of-'+str(num_parts)+' --strip-components 1 -C part_%%A'+chr(47)+'\n')
            f.write('   move part_%%A'+chr(92)+'* '+name+chr(92)+'\n')
            f.write('   rd /q part_%%A\n')
            f.write(')\n')
            
            f.write('set "endTime=%time: =0%"\n')
            f.write('set "end=!endTime:%time:~8,1%=%%100)*100+1!"\n')
            f.write('set "start=!startTime:%time:~8,1%=%%100)*100+1!"\n')
            f.write('set /A "elap=((((10!end:%time:~2,1%=%%100)*60+1!%%100)-((((10!start:%time:~2,1%=%%100)*60+1!%%100), elap-=(elap>>31)*24*60*60*100"\n')
            f.write('set /A "cc=elap%%100+100,elap/=100,ss=elap%%60+100,elap/=60,mm=elap%%60+100,hh=elap/60+100"\n')
            f.write('echo End:      %endTime%\n')
            f.write('echo Elapsed:  %hh:~1%%time:~2,1%%mm:~1%%time:~2,1%%ss:~1%%time:~8,1%%cc:~1%\n')

        self.textBrowser.append("<span>Adding .bat file</span>")

        # now we create the linux bash script to put it all together
        with io.open(os.path.join(folder, 'merge_parts.bash'), 'w', newline='\n') as f:
            f.write('#!/bin/bash\n')
            f.write('SECONDS=0\n')
            f.write('mkdir '+name+'\n')
            f.write('for i in {1..'+str(num_parts)+'}\n')
            f.write('do\n')
            f.write('   mkdir part_$i\n')
            f.write('   tar -xvf '+basename+'-part-$i-of-'+str(num_parts)+' --strip-components 1 --directory=part_$i\n')
            f.write('   mv part_$i'+chr(47)+'* '+name+chr(47)+'\n')
            f.write('   rm -rf part_$i\n')
            f.write('done\n')
            f.write('duration=$SECONDS\n')
            f.write('echo "Process complete. $((duration / 60)) minutes and $((duration % 60)) seconds elapsed."\n')

        self.textBrowser.append("<span>Adding .bash file</span>")


    def update_msg(self):
        global proj_dict
        msg = proj_dict['msg']
        self.textBrowser.append("<span>"+msg+"</span>")



if __name__ == '__main__':

    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext

    main_ui = appctxt.get_resource('splitar_gui.ui')
    instruction_file = appctxt.get_resource('instructions.txt')

    window = Splitar()
    window.show()
    exit_code = appctxt.app.exec()      # 2. Invoke appctxt.app.exec()
    sys.exit(exit_code)