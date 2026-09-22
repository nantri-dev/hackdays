import asyncio
import time
import httpx
import logging

logger = logging.getLogger(__name__)

class ConnectivityMonitor:
    def __init__(self):
        self.is_online = True
        self._manual_override = None # True/False to force state for demo
        
    async def run(self):
        async with httpx.AsyncClient() as client:
            while True:
                await asyncio.sleep(2.0)
                
                if self._manual_override is not None:
                    self.is_online = self._manual_override
                    continue
                
                # Check actual connectivity by pinging Gemini or Google
                try:
                    # using google.com as a fast reliable ping
                    resp = await client.head('https://www.google.com', timeout=1.5)
                    self.is_online = resp.status_code < 500
                except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError):
                    self.is_online = False
                
    def force_offline(self):
        self._manual_override = False
        
    def force_online(self):
        self._manual_override = True
        
    def reset(self):
        self._manual_override = None
