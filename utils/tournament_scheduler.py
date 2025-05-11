import asyncio
from datetime import datetime

from utils.tournament_db import TournamentDatabase
from models.tournament import Tournament

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
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        
        # Cancel all tasks
        for task_id, task in self.scheduled_tasks.items():
            if not task.done():
                task.cancel()
        
        self.scheduled_tasks = {}
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks for scheduled actions"""
        while self.running:
            try:
                # Get all active tournaments
                tournaments = TournamentDatabase.get_active_tournaments()
                
                for tournament in tournaments:
                    # Process reminders
                    await self._process_tournament_reminders(tournament)
                    
                    # If tournament is started but not ended, check for timed forfeit
                    if tournament.started_at and not tournament.ended_at:
                        await self._process_match_timeouts(tournament)
                
                # Sleep for a bit before checking again
                await asyncio.sleep(60)  # Check every minute
            
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Still sleep on errors
    
    async def _process_tournament_reminders(self, tournament: Tournament):
        """Check and send reminders for a tournament"""
        now = datetime.now()
        reminders_to_remove = []
        
        for i, reminder in enumerate(tournament.reminders):
            reminder_time = datetime.fromisoformat(reminder["time"])
            
            # Check if reminder time has passed
            if reminder_time <= now:
                # Create a task to send the reminder
                task_id = f"reminder_{tournament.id}_{i}"
                if task_id not in self.scheduled_tasks:
                    task = asyncio.create_task(self._send_reminder(tournament, reminder))
                    self.scheduled_tasks[task_id] = task
                    
                    # Add callback to remove task when done
                    task.add_done_callback(lambda t, tid=task_id: self._task_done_callback(tid))
                
                # Mark for removal
                reminders_to_remove.append(i)
        
        # Remove sent reminders (in reverse to preserve indices)
        for i in sorted(reminders_to_remove, reverse=True):
            tournament.reminders.pop(i)
        
        # Save if we removed any reminders
        if reminders_to_remove:
            TournamentDatabase.save_tournament(tournament)