"""
Base Personality Class

Defines the interface for personality modules.
All game modes/personalities should inherit from this class.
"""


class Personality:
    """
    Base class for bot personalities.
    
    A personality defines how the bot responds to messages.
    Subclass this to create new game modes or interaction styles.
    
    Example:
        class RiddlePersonality(Personality):
            def handle_message(self, text, sender_id, sender_name):
                # Riddle game logic here
                pass
    """
    
    def __init__(self, database):
        """
        Initialize personality with database access.
        
        Args:
            database: BotDatabase instance for persistence
        """
        self.db = database
        self.name = "Base"
    
    def handle_message(self, text, sender_id, sender_name):
        """
        Process incoming message, return response (or None)
        
        Args:
            text: Message text
            sender_id: Node ID of sender
            sender_name: Username of sender
        
        Returns:
            String to send back, or None for no response
        """
        raise NotImplementedError
    
    def get_help(self):
        """Return help text for this personality"""
        return "No help available"
