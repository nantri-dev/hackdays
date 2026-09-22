import asyncio
import time

class ConnectivityMonitor:
    def __init__(self):
        self.is_online = True
        self._manual_override = None # True/False to force state for demo
        
    async def run(self):
        while True:
            # Simulate a quick lightweight ping
            # In a real system: await asyncio.to_thread(requests.get, 'http://8.8.8.8', timeout=1)
            await asyncio.sleep(1.0)
            
            if self._manual_override is not None:
                self.is_online = self._manual_override
            else:
                self.is_online = True # Default to true
                
    def force_offline(self):
        self._manual_override = False
        
    def force_online(self):
        self._manual_override = True
        
    def reset(self):
        self._manual_override = None
