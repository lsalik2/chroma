from typing import Dict, List

# TODO eventually change this to a pillow powered image of the bracket
def create_tournament_bracket_text(tournament_name: str, teams: List[Dict], matches: List[Dict]) -> str:
    """
    Create an ASCII code block art bracket for tournament visualization.
    This is a simpler text-based solution since we can't create images directly (for now?).
    
    Parameters:
    - tournament_name: The name of the tournament
    - teams: List of team dictionaries with name and id keys
    - matches: List of match dictionaries with team1_id, team2_id, and winner_id keys
    
    Returns:
    - A string containing the ASCII bracket representation
    """
    # First organize matches by round
    max_round = 0
    matches_by_round = {}
    
    # Team lookup for easy access
    team_lookup = {team['id']: team['name'] for team in teams}
    
    for match in matches:
        round_num = match.get('round', 0)
        max_round = max(max_round, round_num)
        
        if round_num not in matches_by_round:
            matches_by_round[round_num] = []
        
        matches_by_round[round_num].append(match)
    
    # Sort matches in each round
    for round_num in matches_by_round:
        matches_by_round[round_num] = sorted(matches_by_round[round_num], key=lambda m: m.get('match_number', 0))
    
    # Create the bracket
    bracket_lines = []
    bracket_lines.append(f"```")
    bracket_lines.append(f"Tournament: {tournament_name}")
    bracket_lines.append(f"")
    
    for round_num in range(1, max_round + 1):
        bracket_lines.append(f"Round {round_num}:")
        
        # Skip if this round doesn't have any matches
        if round_num not in matches_by_round:
            bracket_lines.append("  No matches")
            continue
        
        for match in matches_by_round[round_num]:
            team1_id = match.get('team1_id')
            team2_id = match.get('team2_id')
            winner_id = match.get('winner_id')
            
            team1_name = team_lookup.get(team1_id, 'TBD')
            team2_name = team_lookup.get(team2_id, 'TBD')
            
            # Display winner with an indicator
            if winner_id:
                if winner_id == team1_id:
                    team1_name = f"{team1_name} ✓"
                elif winner_id == team2_id:
                    team2_name = f"{team2_name} ✓"
            
            match_str = f"  {team1_name} vs {team2_name}"
            bracket_lines.append(match_str)
        
        bracket_lines.append("")
    
    bracket_lines.append("```")
    return "\n".join(bracket_lines)

async def send_bracket_to_channel(channel, tournament):
    """
    Send a text bracket to a channel
    
    Parameters:
    - channel: The Discord channel to send to
    - tournament: The Tournament object
    """
    # Convert tournament data to the format expected by create_tournament_bracket_text
    teams = [
        {'id': team.id, 'name': team.name}
        for team in tournament.teams.values()
        if team.status.value == 'approved'
    ]
    
    matches = [
        {
            'round': match.round_number,
            'match_number': match.match_number,
            'team1_id': match.team1_id,
            'team2_id': match.team2_id,
            'winner_id': match.winner_id
        }
        for match in tournament.matches.values()
    ]
    
    bracket_text = create_tournament_bracket_text(tournament.name, teams, matches)
    
    # Send team list
    team_list = "# Registered Teams\n\n"
    approved_teams = [team for team in tournament.teams.values() if team.status.value == 'approved']
    
    for team in sorted(approved_teams, key=lambda t: t.seeding or 999):
        player_names = ", ".join([p.username for p in team.players])
        seed_text = f"Seed #{team.seeding}: " if team.seeding else ""
        team_list += f"**{seed_text}{team.name}** - {player_names}\n"
    
    await channel.send(team_list)
    
    # Send the bracket
    await channel.send(f"# Tournament Bracket\n{bracket_text}")