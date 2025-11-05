"""
Meshtastic Service - Device connection and messaging

Handles all interactions with Meshtastic devices including:
- Auto-detection and connection
- Message sending (DMs and channels)
- Channel discovery
- Node information retrieval
"""
import threading
import time
import meshtastic
import meshtastic.serial_interface
from pubsub import pub


class MeshtasticService:
    """
    Service for interacting with Meshtastic mesh network devices.
    
    Provides a clean interface for device connectivity, messaging,
    and channel management. Handles connection in background thread
    to allow for interruption.
    """
    
    def __init__(self):
        self.interface = None
        self.channels = []
        self.my_node_name = "Unknown"
        self.device_path = None
        
    def connect(self, on_receive=None, on_connection=None, on_connection_lost=None, timeout=30):
        """
        Connect to Meshtastic device with auto-detection
        
        Args:
            on_receive: Callback for incoming messages (packet, interface)
            on_connection: Callback for connection established (interface)
            on_connection_lost: Callback for connection lost (interface)
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected, False otherwise
        """
        # Subscribe to events
        if on_receive:
            pub.subscribe(on_receive, "meshtastic.receive")
        if on_connection:
            pub.subscribe(on_connection, "meshtastic.connection.established")
        if on_connection_lost:
            pub.subscribe(on_connection_lost, "meshtastic.connection.lost")
        
        # Connect in background thread
        result = {}
        error = {}
        
        def _connect():
            try:
                print("🔌 Auto-detecting Meshtastic device...")
                result['interface'] = meshtastic.serial_interface.SerialInterface()
            except Exception as e:
                error['error'] = e
        
        connect_thread = threading.Thread(target=_connect, daemon=True)
        connect_thread.start()
        
        # Wait for connection with timeout
        start_time = time.time()
        while connect_thread.is_alive():
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Connection timeout after {timeout} seconds")
            time.sleep(0.1)
        
        # Check results
        if 'error' in error:
            raise error['error']
        if 'interface' not in result:
            raise Exception("Connection failed for unknown reason")
        
        self.interface = result['interface']
        
        # Get device info
        if hasattr(self.interface, 'devPath'):
            self.device_path = self.interface.devPath
        elif hasattr(self.interface, 'stream') and hasattr(self.interface.stream, 'name'):
            self.device_path = self.interface.stream.name
        
        return True
    
    def send_text(self, text, destination=None, channel_index=None):
        """
        Send a text message
        
        Args:
            text: Message text
            destination: Node ID for DM (if None, sends to channel)
            channel_index: Channel index for broadcasts (ignored for DMs)
        """
        if not self.interface:
            raise Exception("Not connected to device")
        
        # For DMs, don't specify channel_index (let Meshtastic handle it)
        # For channel messages, must specify channel_index
        if destination:
            # Direct message - don't use channelIndex
            self.interface.sendText(
                text=text,
                destinationId=destination
            )
        else:
            # Channel broadcast - requires channelIndex
            self.interface.sendText(
                text=text,
                channelIndex=channel_index
            )
    
    def get_channels(self):
        """Get list of channels"""
        if not self.interface:
            return []
        
        # Access channels through localNode
        if hasattr(self.interface, 'localNode') and hasattr(self.interface.localNode, 'channels'):
            channels = self.interface.localNode.channels
            if isinstance(channels, list):
                return channels
            elif isinstance(channels, dict):
                return list(channels.values())
        
        return []
    
    def find_channel_by_name(self, channel_name):
        """
        Find channel index by name (case-insensitive)
        
        Args:
            channel_name: Name to search for
            
        Returns:
            Channel index or None if not found
        """
        channels = self.get_channels()
        
        for idx, channel in enumerate(channels):
            if hasattr(channel, 'settings') and hasattr(channel.settings, 'name'):
                name = channel.settings.name
                if name and name.lower() == channel_name.lower():
                    return idx
        
        return None
    
    def get_my_node_info(self):
        """Get information about our own node"""
        if not self.interface:
            return None
        
        myInfo = self.interface.myInfo
        if not myInfo:
            return None
        
        my_node_num = myInfo.my_node_num
        nodes = self.interface.nodes
        
        # Nodes is a dict, need to iterate to find our node
        for _, node_info in nodes.items():
            if node_info.get('num') == my_node_num:
                user_info = node_info.get('user', {})
                return {
                    'node_num': my_node_num,
                    'long_name': user_info.get('longName', 'Unknown'),
                    'short_name': user_info.get('shortName', 'UNK')
                }
        
        return {'node_num': my_node_num, 'long_name': 'Unknown', 'short_name': 'UNK'}
    
    def close(self):
        """Close the connection"""
        if self.interface:
            self.interface.close()
            self.interface = None
