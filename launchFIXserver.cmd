set pythonpath=C:\Users\fayca\OneDrive\Documents\FRDev\mimicLOB
set /p UserInput=Enter a port number for this server instance: 
python mimicLOB/agent/FIXserver.py %UserInput%