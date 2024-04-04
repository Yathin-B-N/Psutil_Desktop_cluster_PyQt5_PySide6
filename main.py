import sys
import os

from PySide6 import  *
from PyQt6.QtWidgets import QMainWindow, QApplication, QGraphicsDropShadowEffect, QSizeGrip,QTableWidgetItem,QPushButton,QProgressBar
from PyQt6.QtCore import QObject,QRunnable,QThreadPool
from PySide6 import QtCore
from output import *
from qt_material import *
import psutil
import PySideExtn 
import time
import datetime
from PySide6.QtCore import Signal,Slot
import shutil
from time import sleep


platforms = {
    'linux' : 'Linux',
    'linux1': 'Linux',
    'linux2': 'Linux',
    'darwin' : 'OS X',
    'win32' : 'Windows'
}

class WorkerSignals(QObject):
    finished = Signal()
    error  = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)

class Worker(QRunnable):
    def __init__(self,fn,*args,**kwargs):
        super(Worker,self).__init__
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args,**self.kwargs)
        except:
            tarceback.print_exc()
            exctype,value  =sys.exc_info()[:2]
            self.signals.error.emit((exctype,value,traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #Load style sheet ,this will override and fonts selectes in qt
        # apply_stylesheet(app, theme='blue.xml')

        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(50)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)

        #apply shadow to centrai wedget

        #set window Icon
        #This icon and Titke will not appear on our app main window
        #becaue no title bar

        self.setWindowTitle("Desktop Cluster")

        self.shadow = QGraphicsDropShadowEffect(self)


        # window size grip to resize window
        QSizeGrip(self.ui.size_grip)

        self.ui.minimize_window_button.clicked.connect(lambda:self.showMinimized())#minimize window 
        self.ui.close_window_button.clicked.connect(lambda:self.close())#close window button
        self.ui.restore_window_button.clicked.connect(lambda:self.maximize_or_minimize())#restore window button

        #######################
        #stacked pages navigations
        #########################

        #to cpu and memory page
        self.ui.cpu_memory_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.cpu_and_memory))

         #to battery page
        self.ui.battery_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.battery))

        self.ui.Sys_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.system_information))

        self.ui.activity_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.activites))

        self.ui.storage_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.storage))
        

        self.ui.network_frame.clicked.connect(lambda:self.ui.stackedWidget.setCurrentWidget(self.ui.networks))


        self.threadpool = QThreadPool()
        self.show()

        self.battery()
        self.cpu_ram()
        self.system_info()
        self.processes()
        self.Storage()
        self.Networks()
        # self.psutil_thread()

    #thread functions

    def psutil_thread(self):
        worker = Worker(self.cpu_ram)

        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progresss.connect(self.progress_fn)

        self.threadpool.start(worker)

        battery_worker = Worker(self.battery)
        battery_worker.signals.result.connect(self.print_output)
        battery_worker.signals.finished.connect(self.thread_complete)
        battery_worker.signals.progresss.connect(self.progress_fn)

        self.threadpool.start(battery_worker)

    


    def print_output(self,s):
        print(s)
    def thread_complete(self):
        print("THREAD COMPLETE")

    def progress_fn(self,n):
        print("%d%% done" % n)


    
    def battery(self):
        batt = psutil.sensors_battery()

        if not hasattr(psutil,"sensors_battery"):
            self.ui.battery_status.settext("platoform not Supported")
        if batt is None :
            self.ui.battery_status.setText("No battery installed")
        if batt.power_plugged:
            self.ui.battery_charge.setText(str(round(batt.percent,2))+"%")
            self.ui.battery_time_left.setText("N/A")
            if batt.percent < 100:
                self.ui.battery_status.setText("Charging")
            else:
                self.ui.battery_status.setText("fully charged")
            self.ui.battery_plugged.setText("Yes")
        else:
            self.ui.battery_charge.setText(str(round(batt.percent,2))+"%")
            self.ui.battery_time_left.setText(self.sec2(batt.secsleft))
            if batt.percent < 100:
                self.ui.battery_status.setText("Discharging")
            else:
                self.ui.battery_status.setText("Fully Charged")
            self.ui.battery_plugged.setText("No")
   
    def cpu_ram(self):
        totalRam = 1.0
        totalRam = psutil.virtual_memory()[0] * totalRam
        totalRam = totalRam/(1024 * 1024 *1024)
        self.ui.total_ram.setText(str("{:.4f}".format(totalRam) +'GB'))

        availRam = 1.0
        availRam = psutil.virtual_memory()[1] * availRam
        availRam = availRam / (1024 * 1024 * 1024)
        self.ui.available_ram.setText(str("{:.4f}".format(availRam) +'GB'))

        ramUsed = 1.0
        ramUsed = psutil.virtual_memory()[3] * ramUsed
        ramUsed = ramUsed / (1024 * 1024 * 1024)
        self.ui.used_ram.setText(str("{:.4f}".format(ramUsed) + 'GB'))

        ramFree = 1.0
        ramFree = psutil.virtual_memory()[3] * ramFree
        ramFree = ramFree / (1024 * 1024 * 1024)
        self.ui.free_ram.setText(str("{:.4f}".format(ramUsed) + 'GB'))

        core = psutil.cpu_count()
        self.ui.cpu_count.setText(str(core))

        ramUsage = str(psutil.virtual_memory()[2]) + '%'
        self.ui.ram_usage.setText(str("{:.4f}".format(totalRam) + 'GB'))

        cpuPer = psutil.cpu_percent()
        self.ui.cpu_per.setText(str(cpuPer) + "%")

        cpuMainCore = psutil.cpu_count(logical = False)
        self.ui.cpu_main_core.setText(str(cpuMainCore))


    def system_info(self):
        time = datetime.datetime.now().strftime("%I:%M:%S %p")
        self.ui.system_time.setText(str(time))
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.ui.system_date.setText(str(date))

        self.ui.system_machine.setText(platform.machine())
        self.ui.system_version.setText(platform.version())

        self.ui.system_platform.setText(platform.platform())
        self.ui.system_system.setText(platform.system())
        self.ui.system_p.setText(platform.processor())
    def create_table_widget(self,rowPosition,columnPosition,text,tableName):
        qtablewidgetitem = QTableWidgetItem()

        getattr(self.ui,tableName).setItem(rowPosition,columnPosition,qtablewidgetitem)
        qtablewidgetitem = getattr(self.ui,tableName).item(rowPosition,columnPosition)

        qtablewidgetitem.setText(text);
    def processes(self):
        for x in psutil.pids():
            rowPosition = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rowPosition)

            try:
                process = psutil.Process(x)

                self.create_table_widget(rowPosition,0,str(process.pid),"tableWidget")
                self.create_table_widget(rowPosition,1,process.name(),"tableWidget")
                self.create_table_widget(rowPosition,2,process.status(),"tableWidget")
                self.create_table_widget(rowPosition,3,str(datetime.datetime.utcfromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')),"tableWidget")


                suspend_btn = QPushButton(self.ui.tableWidget)
                suspend_btn.setText('Suspend')
                suspend_btn.setStyleSheet("color:orange")
                self.ui.tableWidget.setCellWidget(rowPosition,4,suspend_btn)

                resume_btn = QPushButton(self.ui.tableWidget)
                resume_btn.setText("Resume")
                resume_btn.setStyleSheet("color:green")
                self.ui.tableWidget.setCellWidget(rowPosition,5,resume_btn)

                terminate_btn = QPushButton(self.ui.tableWidget)
                terminate_btn.setText("Terminate")
                terminate_btn.setStyleSheet("color:Blue")
                self.ui.tableWidget.setCellWidget(rowPosition,6,terminate_btn)

                kill_btn = QPushButton(self.ui.tableWidget)
                kill_btn.setText("Kill")
                kill_btn.setStyleSheet("color:red")
                self.ui.tableWidget.setCellWidget(rowPosition,7,kill_btn)

            except Exception as e:
                print(e)
        self.ui.activity_search.textChanged.connect(self.findName)

    def findName(self):
        name = self.ui.activity_search.text().lower()
        for row in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(row,1)
            self.ui.tableWidget.setRowHidden(row,name not in item.text().lower())
     #for storage frame
    def Storage(self):
        global platforms
        storage_device = psutil.disk_partitions(all = False)
        z = 0 
        for x in storage_device:
            rowPosition = self.ui.storageTable.rowCount()
            self.ui.storageTable.insertRow(rowPosition)

            self.create_table_widget(rowPosition,0,x.device,"storageTable")
            self.create_table_widget(rowPosition,1,x.mountpoint,"storageTable")
            self.create_table_widget(rowPosition,2,x.fstype,"storageTable")
            self.create_table_widget(rowPosition,3,x.opts,"storageTable")

            if sys.platform == 'linux' or sys.platform == 'linux2' or sys.platform == 'linux1':
                self.create_table_widget(rowPosition,4,str(x.maxfile),"storageTable")
                self.create_table_widget(rowPosition,5,str(x.maxpath),"storageTable")
            else:
                self.create_table_widget(rowPosition,4,"function not available on"+platforms[sys.platform],"storageTable")
                self.create_table_widget(rowPosition,5,"Function not available on" + platforms[sys.platform],"storageTable")

            disk_usage = shutil.disk_usage(x.mountpoint)
            self.create_table_widget(rowPosition,6,str((disk_usage.total/(1024*1024*1024)))+"GB","storageTable")
            self.create_table_widget(rowPosition,7,str((disk_usage.used/(1024*1024*1024)))+"GB","storageTable")
            self.create_table_widget(rowPosition,8,str((disk_usage.free/(1024*1024*1024)))+"GB","storageTable")

            full_disk = (disk_usage.used / disk_usage.total)* 100
            progressBar = QProgressBar(self.ui.storageTable)
            progressBar.setObjectName(u"progressBar")
            progressBar.setValue(int(full_disk))
            self.ui.storageTable.setCellWidget(rowPosition,9,progressBar)


                

    def Networks(self):
        for x in psutil.net_if_stats():
            z = psutil.net_if_stats()

            rowPosition = self.ui.net_stats_table.rowCount()
            self.ui.net_stats_table.insertRow(rowPosition)

            self.create_table_widget(rowPosition,0,x,"net_stats_table")
            self.create_table_widget(rowPosition,1,str(z[x].isup),"net_stats_table")
            self.create_table_widget(rowPosition,2,str(z[x].duplex),"net_stats_table")
            self.create_table_widget(rowPosition,3,str(z[x].speed),"net_stats_table")
            self.create_table_widget(rowPosition,4,str(z[x].mtu),"net_stats_table")

        for x in psutil.net_io_counters(pernic=True):
            z = psutil.net_io_counters(pernic=True)

            rowPosition = self.ui.net_io_table.rowCount()
            self.ui.net_io_table.insertRow(rowPosition)
            self.create_table_widget(rowPosition,0,x,"net_io_table")
            self.create_table_widget(rowPosition,1,str(z[x].bytes_sent),"net_io_table")
            self.create_table_widget(rowPosition,2,str(z[x].bytes_recv),"net_io_table")
            self.create_table_widget(rowPosition,3,str(z[x].packets_sent),"net_io_table")
            self.create_table_widget(rowPosition,4,str(z[x].packets_recv),"net_io_table")
            self.create_table_widget(rowPosition,5,str(z[x].errin),"net_io_table")
            self.create_table_widget(rowPosition,6,str(z[x].errout),"net_io_table")
            self.create_table_widget(rowPosition,7,str(z[x].dropin),"net_io_table")
            self.create_table_widget(rowPosition,8,str(z[x].dropout),"net_io_table")

        for x in psutil.net_if_addrs():
            z = psutil.net_if_addrs()
            for y in z[x]:
                rowPosition = self.ui.net_address_table.rowCount()
                self.ui.net_address_table.insertRow(rowPosition)

                self.create_table_widget(rowPosition,0,str(x),"net_address_table")
                self.create_table_widget(rowPosition,1,str(y.family),"net_address_table")
                self.create_table_widget(rowPosition,2,str(y.address),"net_address_table")
                self.create_table_widget(rowPosition,3,str(y.netmask),"net_address_table")
                self.create_table_widget(rowPosition,4,str(y.broadcast),"net_address_table")
                self.create_table_widget(rowPosition,5,str(y.ptp),"net_address_table")

        for x in psutil.net_connections():
            z = psutil.net_connections()

            rowPosition = self.ui.net_connections_table.rowCount()
            self.ui.net_connections_table.insertRow(rowPosition)

            self.create_table_widget(rowPosition,0,str(x.fd),"net_connections_table")
            self.create_table_widget(rowPosition,1,str(x.family),"net_connections_table")
            self.create_table_widget(rowPosition,2,str(x.type),"net_connections_table")
            self.create_table_widget(rowPosition,3,str(x.laddr),"net_connections_table")
            self.create_table_widget(rowPosition,4,str(x.raddr),"net_connections_table")
            self.create_table_widget(rowPosition,5,str(x.status),"net_connections_table")
            self.create_table_widget(rowPosition,6,str(x.pid),"net_connections_table")




    def maximize_or_minimize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
     
    def sec2(self,seconds):
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
         
        return "%d:%02d:%02d" % (hour, minutes, seconds)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())