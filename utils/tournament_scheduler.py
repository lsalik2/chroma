import asyncio

class TournamentScheduler:
    """Handles scheduled tasks for tournaments like reminders and auto-starting matches"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduled_tasks = {}  # task_id -> asyncio.Task
        self.running = False
    
    async def start(self):
        """Start the scheduler background task"""
        if self.running:
            return
        
        self.running = True
        asyncio.create_task(self._scheduler_loop())