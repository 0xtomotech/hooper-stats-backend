from django.core.management.base import BaseCommand
from api.sportradar_utils import get_sportradar_data
from api.supabase_utils import get_supabase_client
import pandas as pd
from datetime import datetime, date
import time
import uuid
import json


def serialize_dates(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class Command(BaseCommand):
    help = 'Fetch Phoenix Suns player stats from Sportradar and populate the Supabase player_stats_by_game table'

    def handle(self, *args, **options):
        supabase = get_supabase_client()

        # Fetch Phoenix Suns team ID
        suns_team = supabase.table('teams').select(
            '*').eq('name', 'Phoenix Suns').execute()
        suns_id = suns_team.data[0]['id']
        self.stdout.write(self.style.SUCCESS(f"Phoenix Suns ID: {suns_id}"))

        # Fetch Booker and Durant player IDs
        players = supabase.table('players').select(
            '*').in_('name', ['Devin Booker', 'Kevin Durant']).execute()
        player_ids = {player['name']: player['id'] for player in players.data}
        self.stdout.write(self.style.SUCCESS(f"Player IDs: {player_ids}"))

        # Fetch all Suns games
        suns_games = supabase.table('games').select(
            '*').or_(f"home_team_id.eq.{suns_id},away_team_id.eq.{suns_id}").execute()
        games_df = pd.DataFrame(suns_games.data)
        self.stdout.write(self.style.SUCCESS(
            f"Total Suns games: {len(games_df)}"))

        # Process all games
        all_stats = []
        for index, game in games_df.iterrows():
            self.stdout.write(f"Processing game {index + 1}/{len(games_df)}")
            game_stats = self.fetch_game_summary(game['id'], player_ids)
            for stats in game_stats:
                stats['team_game_number'] = game['game_number']
                stats['date'] = game['date']
                stats['team_won'] = (game['winner_team_id'] == suns_id)

                # Check if record already exists
                existing_record = supabase.table('player_stats_by_game')\
                    .select('id')\
                    .eq('player_id', stats['player_id'])\
                    .eq('game_id', stats['game_id'])\
                    .execute()

                if not existing_record.data:
                    all_stats.append(stats)
                else:
                    self.stdout.write(self.style.WARNING(
                        f"Skipping existing record for player {stats['player_name']} in game {stats['game_id']}"))

            time.sleep(1)  # Add delay to avoid API rate limits

        player_stats_df = pd.DataFrame(all_stats)

        if not player_stats_df.empty:
            # Prepare data for insertion
            required_columns = [
                'id', 'player_id', 'player_name', 'game_id', 'team_game_number',
                'date', 'team_won', 'three_points_made', 'three_points_att', 'three_points_pct'
            ]

            for column in required_columns:
                if column not in player_stats_df.columns:
                    if column == 'id':
                        player_stats_df['id'] = [
                            str(uuid.uuid4()) for _ in range(len(player_stats_df))]
                    else:
                        player_stats_df[column] = None

            player_stats_df = player_stats_df[required_columns]

            # Convert data types
            player_stats_df['team_game_number'] = player_stats_df['team_game_number'].astype(
                int)
            player_stats_df['date'] = pd.to_datetime(
                player_stats_df['date']).dt.date
            player_stats_df['team_won'] = player_stats_df['team_won'].astype(
                bool)
            player_stats_df['three_points_made'] = player_stats_df['three_points_made'].astype(
                int)
            player_stats_df['three_points_att'] = player_stats_df['three_points_att'].astype(
                int)
            player_stats_df['three_points_pct'] = player_stats_df['three_points_pct'].astype(
                float)

            # Convert date to string format for JSON serialization
            player_stats_df['date'] = player_stats_df['date'].astype(str)

            # Convert DataFrame to list of dictionaries
            player_stats_records = json.loads(json.dumps(
                player_stats_df.to_dict('records'), default=serialize_dates))

            # Insert data into Supabase
            result = supabase.table('player_stats_by_game').insert(
                player_stats_records).execute()

            self.stdout.write(self.style.SUCCESS(
                f"Inserted {len(result.data)} new records into player_stats_by_game table"))
        else:
            self.stdout.write(self.style.WARNING("No new records to insert"))

        # Verify the insertion
        final_stats = supabase.table(
            'player_stats_by_game').select('*').execute()
        self.stdout.write(self.style.SUCCESS(
            f"Final count of player stats in database: {len(final_stats.data)}"))

    def fetch_game_summary(self, game_id, player_ids):
        try:
            summary_data = get_sportradar_data(f'games/{game_id}/summary.json')
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to fetch game summary for game {game_id}: {str(e)}"))
            return []

        player_stats = []
        for team in ['home', 'away']:
            if team not in summary_data:
                self.stdout.write(self.style.WARNING(
                    f"Team data '{team}' not found in game summary for game {game_id}"))
                continue

            for player in summary_data[team].get('players', []):
                try:
                    if player['id'] in player_ids.values():
                        stats = {
                            'player_id': player['id'],
                            'player_name': next((name for name, pid in player_ids.items() if pid == player['id']), None),
                            'game_id': game_id,
                            'three_points_made': player['statistics'].get('three_points_made', 0),
                            'three_points_att': player['statistics'].get('three_points_att', 0),
                            'three_points_pct': player['statistics'].get('three_points_pct', 0)
                        }
                        if stats['player_name'] is None:
                            self.stdout.write(self.style.WARNING(
                                f"Player name not found for ID {player['id']} in game {game_id}"))
                        player_stats.append(stats)
                except KeyError as e:
                    self.stdout.write(self.style.ERROR(
                        f"Missing key in player data for game {game_id}: {str(e)}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error processing player in game {game_id}: {str(e)}"))

        return player_stats
