from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QMainWindow, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, QPointF
import sys
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtChart import QChart, QChartView, QBarSet, QBarCategoryAxis, QValueAxis, QLineSeries
from daq_setup import DAQ 

import os
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
        
        
        # run front end layout builder
        self.configure_windows()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_series)
        self.timer.start(1000)  # update every 500ms (adjust as needed)
 
    # split up main window into two sections
    def configure_windows(self):
        

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
        
        
        chart_view = QChartView(leak_chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        # left layout is a grid for the chart
        left_layout = QGridLayout()
        left_widget = QWidget(self)
        left_widget.setFixedSize(512,500)
        left_widget.setLayout(left_layout)
        left_layout.addWidget(chart_view)
        
        
        # structure for the right side of screen
        right_layout = QVBoxLayout()
        self.right_label = QLabel("EOL data")
        right_layout.addWidget(self.right_label)
        
        # add buttons and other widgets to the right layout
        self.start_button = QPushButton("Get Pressure")
        self.start_button.setFixedSize(200,50)
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 20px;")
        self.start_button.clicked.connect(self.update_pressure)
        right_layout.addWidget(self.start_button, alignment=Qt.AlignTop)
        
        
        
        # Create labels for DAQ instance variables
         # update the instance variable then display to front end
        self.pressure_label = QLabel(f"Pressure: {self.daq.get_sample()} PSI")
        self.pressure_label.setStyleSheet("font-size: 16px;")
        right_layout.addWidget(self.pressure_label, alignment=Qt.AlignTop)
        
        
        # place layout items in widget
        right_widget = QWidget()
        right_widget.setFixedSize(512,500)
        right_widget.setLayout(right_layout)
        
        
        # add the widgets to the main layout
        self.layout.addWidget(left_widget)
        self.layout.addWidget(right_widget)
        
    def get_pressure(self) -> None:
        return self.daq.get_sample()  # Get the current pressure from the DAQ
    
    def update_pressure(self) -> None:
        # set both the instance variables and update the label
        self.current_pressure = self.get_pressure()
        self.pressure_label.setText(f"Pressure: {self.get_pressure()} PSI")  # Update the label with the current pressure
        
        
    def add_test_timer(self, minutes):
        time = self.daq.test_time
        self.timer_label = QLabel(f"Time Remaining: {minutes}:00")
        self.timer_label.setStyleSheet("font-size: 16px;")
        self.central_widget.layout().addWidget(self.timer_label, alignment=Qt.AlignTop)

        self.remaining_time = minutes * 60  # Convert minutes to seconds

        self.test_timer = QTimer(self)
        self.test_timer.timeout.connect(self.update_timer_label)
        self.test_timer.start(1000)  # Update every second

    def update_timer_label(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            minutes, seconds = divmod(self.remaining_time, 60)
            self.timer_label.setText(f"Time Remaining: {minutes}:{seconds:02d}")
        else:
            self.test_timer.stop()
            self.timer_label.setText("Time's up!")
            
    # update the chart on with update_series callback
    def update_series(self):
        self.pressure_data.pop(0)  # Remove the first (oldest) element from the data list
        self.pressure_data.append(self.daq.get_sample())  # Append a new random integer to the data list

        self.data.clear()  # Clear the current series
        for i, value in enumerate(self.pressure_data):
            self.data.append(QPointF(i, value))  # Add new data points to the series
    
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
    
        
    

        
if __name__ == "__main__":
    # Create the application and the main window
    app = QApplication(sys.argv)
    win = EolUI()
    win.show()
    sys.exit(app.exec_())