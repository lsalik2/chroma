import asyncio
from datetime import datetime, timedelta
from typing import Dict

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
    
    async def _process_match_timeouts(self, tournament: Tournament):
        """Check for match timeouts and handle forfeits"""
        # Get all in-progress matches
        in_progress_matches = [
            match for match in tournament.matches.values()
            if match.status.value == 'pending'
        ]
        
        now = datetime.now()
        timeout_threshold = timedelta(minutes=10)  # 10 minute timeout
        
        # Create forfeit tasks for matches that have timed out
        for match in in_progress_matches:
            # Skip if both teams are checked in
            if all(match.checked_in.values()):
                continue
            
            # Skip if created less than threshold ago
            if now - match.created_at < timeout_threshold:
                continue
            
            # Create a task to handle the forfeit
            task_id = f"forfeit_{tournament.id}_{match.id}"
            if task_id not in self.scheduled_tasks:
                task = asyncio.create_task(self._handle_match_forfeit(tournament, match))
                self.scheduled_tasks[task_id] = task
                
                # Add callback to remove task when done
                task.add_done_callback(lambda t, tid=task_id: self._task_done_callback(tid))
    
    def _task_done_callback(self, task_id: str):
        """Called when a scheduled task completes"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
    
    async def _send_reminder(self, tournament: Tournament, reminder: Dict):
        """Send a reminder for a tournament"""
        # Get announcement channel
        if not tournament.announcement_channel_id:
            return
        
        channel = self.bot.get_channel(tournament.announcement_channel_id)
        if not channel:
            return
        
        # Get all player mentions
        mentions = []
        for team in tournament.teams.values():
            if team.status.value == "approved":
                for player in team.players:
                    mentions.append(f"<@{player.user_id}>")
        
        mentions_text = " ".join(mentions)
        
        await channel.send(
            f"# 📢 Tournament Reminder 📢\n\n"
            f"{reminder['message']}\n\n"
            f"{mentions_text}"
        )
    
    async def _handle_match_forfeit(self, tournament: Tournament, match):
        """Handle forfeits for matches where teams didn't check in"""
        # Get channel
        if not match.channel_id:
            return
        
        channel = self.bot.get_channel(match.channel_id)
        if not channel:
            return
        
        # Determine which team(s) forfeited
        team1_checked_in = match.checked_in.get(match.team1_id, False)
        team2_checked_in = match.checked_in.get(match.team2_id, False)
        
        # Both teams forfeited
        if not team1_checked_in and not team2_checked_in:
            await channel.send(
                f"# ⚠️ Both teams have forfeited! ⚠️\n\n"
                f"Neither team checked in within the time limit."
            )
            
            # No winner, both teams eliminated
            match.status = "forfeit"
            TournamentDatabase.save_tournament(tournament)
            return
        
        # Team 1 forfeited
        if not team1_checked_in and team2_checked_in:
            team1 = tournament.get_team(match.team1_id)
            team2 = tournament.get_team(match.team2_id)
            
            await channel.send(
                f"# ⚠️ Team Forfeit ⚠️\n\n"
                f"**{team1.name}** has forfeited for not checking in within the time limit.\n"
                f"**{team2.name}** wins by default!"
            )
            
            # Advance team 2
            next_match = tournament.advance_match(match.id, match.team2_id)
            TournamentDatabase.save_tournament(tournament)
            return
        
        # Team 2 forfeited
        if team1_checked_in and not team2_checked_in:
            team1 = tournament.get_team(match.team1_id)
            team2 = tournament.get_team(match.team2_id)
            
            await channel.send(
                f"# ⚠️ Team Forfeit ⚠️\n\n"
                f"**{team2.name}** has forfeited for not checking in within the time limit.\n"
                f"**{team1.name}** wins by default!"
            )
            
            # Advance team 1
            next_match = tournament.advance_match(match.id, match.team1_id)
            TournamentDatabase.save_tournament(tournament)
            return

# This function will be called from the main bot.py to start the scheduler
async def start_tournament_scheduler(bot):
    scheduler = TournamentScheduler(bot)
    await scheduler.start()
    return scheduler