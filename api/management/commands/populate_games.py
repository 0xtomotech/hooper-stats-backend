from django.core.management.base import BaseCommand
from api.sportradar_utils import get_sportradar_data
from api.supabase_utils import get_supabase_client
import pandas as pd
from datetime import datetime, date
import json


def serialize_dates(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class Command(BaseCommand):
    help = 'Fetch Phoenix Suns games from Sportradar and populate the Supabase games table'

    def handle(self, *args, **options):
        supabase = get_supabase_client()

        # Fetch Phoenix Suns team ID from the teams table
        suns_team = supabase.table('teams').select(
            '*').eq('name', 'Phoenix Suns').execute()
        suns_id = suns_team.data[0]['id']
        suns_name = suns_team.data[0]['name']
        self.stdout.write(self.style.SUCCESS(f"Phoenix Suns ID: {suns_id}"))
        self.stdout.write(self.style.SUCCESS(
            f"Phoenix Suns Name: {suns_name}"))

        # Fetch schedule data from Sportradar API
        schedule_data = get_sportradar_data('games/2023/REG/schedule.json')

        # Process games data
        games_data = []
        for game in schedule_data['games']:
            if game['home']['id'] == suns_id or game['away']['id'] == suns_id:
                games_data.append({
                    'id': game['id'],
                    'date': datetime.strptime(game['scheduled'][:10], '%Y-%m-%d').date(),
                    'season': schedule_data['season']['year'],
                    'home_team_id': game['home']['id'],
                    'away_team_id': game['away']['id'],
                    'home_team_name': game['home']['name'],
                    'away_team_name': game['away']['name'],
                    'home_points': game.get('home_points', 0),
                    'away_points': game.get('away_points', 0),
                })

        # Convert to DataFrame
        df = pd.DataFrame(games_data)

        # Sort by date and add game number
        df = df.sort_values('date')
        df['game_number'] = range(1, len(df) + 1)

        # Determine winner
        df['winner_team_id'] = df.apply(
            lambda row: row['home_team_id'] if row['home_points'] > row['away_points'] else row['away_team_id'], axis=1)
        df['winner_team_name'] = df.apply(
            lambda row: row['home_team_name'] if row['home_points'] > row['away_points'] else row['away_team_name'], axis=1)

        # Convert date to string
        df['date'] = df['date'].astype(str)

        # Prepare data for Supabase insertion
        games_to_insert = json.loads(json.dumps(
            df.to_dict('records'), default=serialize_dates))

        # Clear existing games for the Suns
        existing_games = supabase.table('games').select('id').or_(
            f"home_team_id.eq.{suns_id},away_team_id.eq.{suns_id}").execute()
        if existing_games.data:
            delete_result = supabase.table('games').delete().or_(
                f"home_team_id.eq.{suns_id},away_team_id.eq.{suns_id}").execute()
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {len(delete_result.data)} existing game records."))
        else:
            self.stdout.write(self.style.SUCCESS(
                "No existing games to delete."))

        # Insert new games
        result = supabase.table('games').insert(games_to_insert).execute()

        # Check the result
        if result.data:
            self.stdout.write(self.style.SUCCESS(
                f"Successfully inserted {len(result.data)} games."))
        else:
            self.stdout.write(self.style.ERROR("Failed to insert games."))
            self.stdout.write(self.style.ERROR(f"Error: {result.error}"))

        # Verify the insertion
        final_games = supabase.table('games').select(
            '*').or_(f"home_team_id.eq.{suns_id},away_team_id.eq.{suns_id}").execute()
        self.stdout.write(self.style.SUCCESS(
            f"Final count of Suns games in database: {len(final_games.data)}"))

        self.stdout.write(self.style.SUCCESS(
            'Finished populating games table'))
