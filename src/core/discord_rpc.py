from pypresence import Presence
import time

class DiscordRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.rpc = None
        self.connected = False

    def connect(self):
        if self.connected:
            return

        def _connect_thread():
            try:
                self.rpc = Presence(self.client_id)
                self.rpc.connect()
                self.connected = True
                print("Successfully connected to Discord RPC")
            except Exception as e:
                if "Client ID is Invalid" in str(e) or "Invalid pipe" in str(e):
                    self.connected = False
                    return 
                
                print(f"Failed to connect to Discord RPC: {e}")
                self.connected = False

        import threading
        t = threading.Thread(target=_connect_thread, daemon=True)
        t.start()

    def update(self, state, details=None, start=None, large_image=None, large_text=None):
        if not self.connected:
            if self.connect() is False:
                return
        
        if self.connected:
            try:
                self.rpc.update(
                    state=state,
                    details=details,
                    start=start,
                    large_image=large_image,
                    large_text=large_text
                )
            except Exception as e:
                print(f"Lost connection to Discord RPC: {e}")
                self.connected = False

    def clear(self):
        if self.connected:
            try:
                self.rpc.clear()
            except:
                pass

    def close(self):
        if self.connected:
            try:
                self.rpc.close()
            except:
                pass

