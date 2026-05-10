import win32serviceutil
import win32service
import win32event
import subprocess

class OreaonService(win32serviceutil.ServiceFramework):
    _svc_name_ = "OreaonService"
    _svc_display_name_ = "Oreaon Voice Assistant"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        subprocess.Popen(["python", r"C:\Users\mehdi\Desktop\Pythonfiles\Projects\Oreaon\main.py"])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(OreaonService)