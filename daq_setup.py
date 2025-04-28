import piplates.DAQC2plate as daq
import time, asyncio


class DAQ():
    def __init__(self, test_time=5):
        # test time in minutes
        self.test_time = test_time
        
        # store these in instance variables to access from front end
        self.initial_pressure = 0
        self.final_pressure = 0
        self.current_pressure = 0
        self.run_flag = False
        
    def print_timer(self, time):
        # use mod math to manually set the time
        tot_seconds = self.test_time * 60
        minutes = tot_seconds // 60
        seconds = tot_seconds % 60
        return f'{minutes:02d}:{seconds:02d}'
        
        
    def calc_pressure(self, adc_volts):
        return ((adc_volts - .5) / 4) * 30
    
    
    async def take_sample(self): # async timer for adc 
        # take average of first few measurements and then average of last few 
        adc = 0
        for i in range(5):
            adc += daq.getADC(0,7)
            await asyncio.sleep(.1)
        adc /= 5
        return adc

    async def get_sample(self): # async runner 
        adc = await self.take_sample()
        return round(self.calc_pressure(adc), 2)

    async def test_timer(self, minutes):
        await asyncio.sleep(minutes * 60)
        

    async def test1(self, test_time=None):
        if test_time is None:
            test_time = self.test_time
        a = await self.take_sample()
        self.initial_pressure = self.calc_pressure(a)
        await asyncio.sleep(300)
        b = await self.take_sample()
        
        self.final_pressure = self.calc_pressure(b)
        print(f"Initial: {a:.2f} Final: {b:.2f}")
        print(f"Difference: {a-b:.2f}")
    

    def print_psi(self):
        while True:
            adc_volts = daq.getADC(0,7)
            pressure = self.calc_pressure(adc_volts)
            print(f"Pressure: {pressure:.2f} PSI")
            time.sleep(1)



    def run(self, request):
        
        # request 1 takes a sample
        if request == '1':
            print("taking sample")
            adc =  asyncio.create_task(self.take_sample())
            print(f"ADC: {adc:.2f}")
            pressure = self.calc_pressure(adc)
            return pressure
            
            
        elif request == '2':
            print("Starting test")
            asyncio.create_task(self.test1())

        
    