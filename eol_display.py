from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QMainWindow, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, QPointF
import sys
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries
from daq_setup import DAQ
from qasync import QEventLoop
import asyncio

import os
# os.system("systemctl stop lightdm") # stop the display manager
os.environ["QT_QPA_PLATFORM"] = "linuxfb" 




class EolUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # QT setup 
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.setFixedSize(1024,600)
        self.setWindowTitle("Leak test EOL")
        self.data = QLineSeries() # for the front end chart

        
        
        # configure daq library
        
        self.daq = DAQ()
        self.pressure_data = [0] * 150
        self.current_pressure = 0
        
        
        # timer for chart
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: asyncio.create_task(self.update_series()))
        self.timer.start(1000)  # update every 500ms (adjust as needed)
        
        # timer for test
        # self.test_timer = QTimer(self)
        # self.test_timer.timeout.connect(self.update_test)
        # self.test_timer.start(1000)
        
        
 
    # split up main window into two sections
    async def configure_windows(self):
        #########################
        ####### LEFT SIDE #######
        #########################
        
        # QChart setup
        leak_chart = QChart()
        leak_chart.addSeries(self.data)
        leak_chart.setTitle("Leak test chart")
        leak_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # x axis time
        x_axis = QValueAxis()
        x_axis.setTickCount(20)
        x_axis.setLabelFormat("%d")
        x_axis.setTitleText("Time (s)")
        leak_chart.addAxis(x_axis, Qt.AlignBottom)
        self.data.attachAxis(x_axis)
        x_axis.setRange(0, 150)
        
        # y axis pressure
        y_axis = QValueAxis()
        y_axis.setTickCount(10)
        y_axis.setLabelFormat("%d")
        y_axis.setTitleText("Pressure (PSI)")
        leak_chart.addAxis(y_axis, Qt.AlignLeft)
        self.data.attachAxis(y_axis)
        y_axis.setRange(0, 20)
        
        # add pressure threshold line
        self.add_horizontal_line(leak_chart, 10, 0, 150)
        
        # create a view and add it to the layout
        chart_view = QChartView(leak_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        left_layout = QGridLayout()
        left_widget = QWidget(self)
        left_widget.setFixedSize(512,500)
        left_widget.setLayout(left_layout)
        left_layout.addWidget(chart_view)
        
        ##########################
        ####### RIGHT SIDE #######
        ##########################
        
        # right side is a box, just stuff buttons and labels in, TODO: grid layout to align items
        right_layout = QVBoxLayout()
        self.right_label = QLabel("EOL User Interface")
        self.right_label.setStyleSheet("font-size: 20px; font-weight: bold; color: black;")
        
        pressure_button_layout = QHBoxLayout() # box for label and button
        # add button to get instantaneous pressure
        self.pressure_button = QPushButton("Get Pressure")
        self.pressure_button.setFixedSize(200,50)
        self.pressure_button.setStyleSheet("background-color: green; color: white; font-size: 20px;")
        self.pressure_button.clicked.connect(lambda: asyncio.create_task(self.update_pressure()))
        
        # current pressure label
        pressure = await self.daq.get_sample()
        self.pressure_label = QLabel(f"Pressure: {pressure} PSI")
        self.pressure_label.setStyleSheet("font-size: 16px;")
        
        # start button box
        start_button_layout = QVBoxLayout() # box for label and button
        self.start_button = QPushButton("Start Test")
        self.start_button.setFixedSize(200,50)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 20px;")
        self.start_button.clicked.connect(lambda: self.daq.run("2"))
        
        # labels for test
        self.initial_pressure_label = QLabel(f"Initial Pressure: {self.daq.initial_pressure} PSI")
        self.initial_pressure_label.setStyleSheet("font-size: 16px;")
        self.final_pressure_label = QLabel(f"Final Pressure: {self.daq.final_pressure} PSI")
        self.final_pressure_label.setStyleSheet("font-size: 16px;")
        self.difference_label = QLabel(f"Difference: {self.daq.final_pressure - self.daq.initial_pressure} PSI")
        self.timer_label = QLabel("Test Timer: 0:00")
        self.timer_label.setStyleSheet("font-size: 16px;")
        
        
        # add the widgets to the right layout
        right_layout.addWidget(self.right_label, Qt.AlignTop)
        pressure_button_layout.addWidget(self.pressure_button, Qt.AlignTop)
        pressure_button_layout.addWidget(self.pressure_label, Qt.AlignTop)
        right_layout.addLayout(pressure_button_layout, Qt.AlignTop) # add a layout within the right_layout
        start_button_layout.addWidget(self.start_button, Qt.AlignTop)
        start_button_layout.addSpacing(20)
        start_button_layout.addWidget(self.initial_pressure_label)
        start_button_layout.addSpacing(20)
        start_button_layout.addWidget(self.final_pressure_label)
        start_button_layout.addSpacing(20)
        start_button_layout.addWidget(self.difference_label)
        start_button_layout.addSpacing(20)
        start_button_layout.addWidget(self.timer_label)
        start_button_layout.addSpacing(20)
        right_layout.addLayout(start_button_layout, Qt.AlignTop) # add test layout within the right_layout
        
        
        # place layout items in widget
        right_widget = QWidget()
        right_widget.setFixedSize(512,500)
        right_widget.setLayout(right_layout)
        
        # add the widgets to the main layout
        self.layout.addWidget(left_widget)
        self.layout.addWidget(right_widget)
        
    async def get_pressure(self) -> None:
        return await self.daq.get_sample()  # Get the current pressure from the DAQ
    
    async def update_pressure(self) -> None:
        # set both the instance variables and update the label
        self.current_pressure = await self.get_pressure()
        self.pressure_label.setText(f"Pressure: {self.current_pressure} PSI")  # Update the label with the current pressure
        
    # def update_timer(self):
    #     self.timer.timeout.connect(self.update_pressure)
        
        
            
    # use circular buffer to update the chart on with update_series callback
    async def update_series(self):
        self.pressure_data.pop(0)  # Remove the first (oldest) element from the data list
        data_point = await self.daq.get_sample()  # Get a new sample from the DAQ
        self.pressure_data.append(data_point)  # Append a new random integer to the data list

        self.data.clear()  # Clear the current series
        for i, value in enumerate(self.pressure_data):
            self.data.append(QPointF(i, value))  # Add new data points to the series
            
    def update_test(self):
        # update the test results
        self.initial_pressure_label.setText(f"Initial Pressure: {self.daq.initial_pressure} PSI")
        self.final_pressure_label.setText(f"Final Pressure: {self.daq.final_pressure} PSI")
        self.difference_label.setText(f"Difference: {self.daq.final_pressure - self.daq.initial_pressure} PSI")
        
    
    # threshold line for pressure drop
    def add_horizontal_line(self, chart, y_value, x_start, x_end):
        line_series = QLineSeries()
        line_series.append(x_start, y_value)  
        line_series.append(x_end, y_value)    
        chart.addSeries(line_series)
        
        
        for axis in chart.axes(Qt.Horizontal):
            line_series.attachAxis(axis)
        for axis in chart.axes(Qt.Vertical):
            line_series.attachAxis(axis)
    
    def cleanup(self):
        # Stop the timers when the window is closed
        os.system("systemctl start lightdm") # restart the display manager
        self.timer.stop()
        self.test_timer.stop()
        super().cleanup()
        
    

        
if __name__ == "__main__":
    # Create the application and the main window
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    win = EolUI()
    win.show()
    async def main():
        await win.configure_windows()
        
    
    with loop:
        loop.create_task(main())
        loop.run_forever()
