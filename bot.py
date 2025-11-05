#!/usr/bin/env python3
"""
Meshtastic Bot - Mesh network game bot with AI chat

A bot that runs on Meshtastic mesh networks, providing trivia games
and AI chat capabilities. Built with a modular personality system
for easy extension.

Features:
- Trivia game with leaderboard
- Local AI chat via Ollama
- Channel-based routing
- SQLite persistence
- Anti-cheat system

Usage:
    python bot.py                              # Auto-detect device
    python bot.py --ollama-model llama3.2:3b   # Custom model
    python bot.py --ollama-host http://...:11434  # Remote Ollama
"""
import sys
import argparse
import signal
import time

from services.database import BotDatabase
from personalities.trivia import TriviaPersonality
from services.meshtastic import MeshtasticService
from services.ollama import OllamaService
from services import config


class MeshtasticBot:
    """
    Main bot orchestrator.
    
    Coordinates between Meshtastic device, personality modules,
    and external services like Ollama.
    """
    
    def __init__(self, ollama_host=None, ollama_model=None):
        """
        Initialize bot with optional configuration overrides.
        
        Args:
            ollama_host: Ollama API URL (overrides .env)
            ollama_model: Ollama model name (overrides .env)
        """
        # Initialize services
        self.meshtastic = MeshtasticService()
        self.ollama = OllamaService(
            host=ollama_host or config.OLLAMA_HOST,
            model=ollama_model or config.OLLAMA_MODEL
        )
        
        # Store config for display
        self.ollama_host = self.ollama.host
        self.ollama_model = self.ollama.model
        
        # Initialize database and personality
        self.db = BotDatabase(db_path=config.DATABASE_PATH)
        self.personality = TriviaPersonality(
            self.db, 
            questions_file=config.TRIVIA_QUESTIONS_FILE,
            ollama_service=self.ollama
        )
        
        # Runtime state
        self.ollama_channel_name = config.OLLAMA_CHANNEL_NAME
        self.ollama_channel_index = None
        self.shutdown_requested = False
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n" + "="*60)
        print("👋 INTERRUPT RECEIVED - SHUTTING DOWN")
        print("="*60)
        self.shutdown_requested = True
        self.meshtastic.close()
        sys.exit(0)
    
    def on_receive(self, packet, interface):
        """
        Handle incoming messages from the mesh network.
        
        Routes messages based on channel:
        - DMs (channel 0): All commands (!trivia, !leaderboard, !ollama, !help)
        - Configured channel: !ollama only (for public AI chat)
        - Other channels: Ignored
        
        Args:
            packet: Message packet from Meshtastic
            interface: Meshtastic interface (unused, required by pubsub)
        """
        # Only process text messages
        if 'decoded' not in packet:
            return
        if 'text' not in packet['decoded']:
            return
        
        text = packet['decoded']['text']
        sender_id = packet.get('fromId', 'unknown')
        
        # Get the channel
        channel = packet.get('channel', 0)
        
        # Get sender name from packet
        sender_name = 'Unknown'
        if 'from' in packet:
            sender_name = str(packet['from'])
        
        # Try to get a better name from the nodes database
        if hasattr(interface, 'nodes') and sender_id in interface.nodes:
            node_info = interface.nodes[sender_id]
            if 'user' in node_info:
                user_info = node_info['user']
                if 'longName' in user_info:
                    sender_name = user_info['longName']
                elif 'shortName' in user_info:
                    sender_name = user_info['shortName']
        
        print(f"📨 [Ch {channel}] [{sender_name}]: {text}")
        
        # Check if this is a DM (channel 0) or the configured Ollama channel
        is_dm = channel == 0
        is_ollama_command = text.lower().strip().startswith('!ollama ')
        is_ollama_channel = (self.ollama_channel_index is not None and 
                            channel == self.ollama_channel_index)
        
        # Handle !ollama command
        # - On DMs: always respond via DM (for testing)
        # - On configured channel: respond to that channel
        if is_ollama_command:
            response = self.personality.handle_message(text, sender_id, sender_name)
            if response:
                if is_dm:
                    # DM response
                    print(f"🤖 Replying to {sender_name} (DM): {response}")
                    if len(response) > 200:
                        chunks = [response[i:i+200] for i in range(0, len(response), 200)]
                        for chunk in chunks:
                            self.meshtastic.send_text(chunk, destination=sender_id)
                            time.sleep(0.5)
                    else:
                        self.meshtastic.send_text(response, destination=sender_id)
                elif is_ollama_channel:
                    # Channel response
                    print(f"🤖 Replying to channel {channel} ({self.ollama_channel_name}): {response}")
                    if len(response) > 200:
                        chunks = [response[i:i+200] for i in range(0, len(response), 200)]
                        for chunk in chunks:
                            self.meshtastic.send_text(chunk, channel_index=channel)
                            time.sleep(0.5)
                    else:
                        self.meshtastic.send_text(response, channel_index=channel)
                else:
                    # !ollama on wrong channel, ignore
                    print(f"⚠️  Ignoring !ollama on channel {channel} (not DM or '{self.ollama_channel_name}')")
            return
        
        # For all other commands (trivia, leaderboard, etc.), only respond to DMs
        # Skip if it's a channel message (not a DM)
        if not is_dm:
            return
        
        # Let personality handle trivia commands (DM only)
        response = self.personality.handle_message(text, sender_id, sender_name)
        
        if response:
            print(f"🤖 Replying to {sender_name} (DM): {response}")
            
            # Reply directly to the sender (DM)
            # Meshtastic has message size limits, split if needed
            if len(response) > 200:
                # Split into chunks
                chunks = [response[i:i+200] for i in range(0, len(response), 200)]
                for chunk in chunks:
                    self.meshtastic.send_text(chunk, destination=sender_id)
                    time.sleep(0.5)  # Small delay between messages
            else:
                self.meshtastic.send_text(response, destination=sender_id)
    
    def on_connection(self, interface, topic=None):
        """
        Handle successful connection to Meshtastic device.
        
        - Displays connection info
        - Finds configured channel
        - Asks initial trivia question
        - Shows available commands
        
        Args:
            interface: Meshtastic interface (unused, for pubsub compatibility)
            topic: PubSub topic (unused, for pubsub compatibility)
        """
        # Get node name from service
        node_info = self.meshtastic.get_my_node_info()
        node_name = node_info.get('long_name', 'Unknown') if node_info else 'Unknown'
        
        # Display device path if available
        print("\n" + "="*60)
        print(f"✅ CONNECTED: {node_name}")
        print("="*60)
        if self.meshtastic.device_path:
            print(f"Device Path: {self.meshtastic.device_path}")
        
        # Find the channel by name
        self.ollama_channel_index = self.meshtastic.find_channel_by_name(self.ollama_channel_name)
        if self.ollama_channel_index is not None:
            print(f"✅ Found channel '{self.ollama_channel_name}' at index {self.ollama_channel_index}")
        else:
            print(f"⚠️  Channel '{self.ollama_channel_name}' not found - !ollama will only work in DMs")
        
        # Ask first question (for internal state, don't broadcast)
        msg, _ = self.personality.ask_new_question()
        
        print("\n📡 LISTENING FOR:")
        print(f"  • DMs: !trivia, !leaderboard, !ollama, !help")
        
        if self.ollama_channel_index is not None:
            print(f"  • #{self.ollama_channel_name}: !ollama commands")
        
        print(f"\n💡 Ready! Current question: {msg}")
        print("="*60 + "\n")
    
    def on_connection_lost(self, interface, topic=None):
        """
        Handle device disconnection.
        
        Exits the bot - mesh network connection is essential.
        
        Args:
            interface: Meshtastic interface (unused, for pubsub compatibility)
            topic: PubSub topic (unused, for pubsub compatibility)
        """
        # Don't show message if we're already shutting down
        if self.shutdown_requested:
            return
            
        print("\n" + "="*60)
        print("❌ CONNECTION LOST TO DEVICE")
        print("="*60)
        print("\nExiting bot...")
        self.meshtastic.close()
        sys.exit(1)
    
    def run(self):
        """
        Start the bot.
        
        Main event loop that:
        1. Sets up signal handlers
        2. Connects to Meshtastic device
        3. Runs until interrupted or disconnected
        """
        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print("="*60)
        print("🚀 MESHTASTIC BOT STARTING")
        print("="*60)
        print(f"Personality: {self.personality.name}")
        print(f"Ollama Host: {self.ollama_host}")
        print(f"Ollama Model: {self.ollama_model}")
        print(f"Target Channel: '{self.ollama_channel_name}'")
        print(f"Database: {config.DATABASE_PATH}")
        print("="*60)
        
        print("\nConnecting to Meshtastic device...")
        print("(Press Ctrl+C to cancel)\n")
        
        try:
            # Connect using the service
            self.meshtastic.connect(
                on_receive=self.on_receive,
                on_connection=self.on_connection,
                on_connection_lost=self.on_connection_lost,
                timeout=30
            )
            
            # Keep running
            while not self.shutdown_requested:
                time.sleep(1)
                
        except KeyboardInterrupt:
            # This catches Ctrl+C during the main loop
            print("\n\n" + "="*60)
            print("👋 SHUTTING DOWN")
            print("="*60)
            self.meshtastic.close()
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("\nTroubleshooting:")
            print("  • Is the device connected?")
            print("  • Check USB connection")
            print("  • Try restarting the device")
            self.meshtastic.close()
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Meshtastic Bot - Trivia and AI chat for mesh networks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run with auto-detected device
  python bot.py
  
  # Specify device path
  python bot.py --device /dev/ttyUSB0
  
  # Use custom Ollama settings
  python bot.py --ollama-host http://192.168.1.100:11434 --ollama-model llama2
        '''
    )
    
    parser.add_argument(
        '--ollama-host',
        metavar='URL',
        help=f'Ollama server URL (default: {config.OLLAMA_HOST})'
    )
    
    parser.add_argument(
        '--ollama-model', '-m',
        metavar='MODEL',
        help=f'Ollama model to use (default: {config.OLLAMA_MODEL})'
    )
    
    args = parser.parse_args()
    
    bot = MeshtasticBot(
        ollama_host=args.ollama_host,
        ollama_model=args.ollama_model
    )
    bot.run()
