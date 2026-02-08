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

        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            print("Successfully connected to Discord RPC")
        except Exception as e:
            # Only print error if it's not the generic "pipe closed" which happens when Discord isn't running
            # or specifically if it's an invalid ID
            if "Client ID is Invalid" in str(e) or "Invalid pipe" in str(e):
                print(f"Discord RPC Disabled: {e}")
                # Disable attempts to prevent spam if ID is bad
                self.connected = False
                return False
            
            print(f"Failed to connect to Discord RPC: {e}")
            self.connected = False
            return False

    def update(self, state, details=None, start=None, large_image=None, large_text=None):
        if not self.connected:
            # Try to connect, but if it fails (returns False), don't try to update
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
                # If update fails, we might have lost connection
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

