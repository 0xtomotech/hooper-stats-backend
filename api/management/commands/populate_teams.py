from django.core.management.base import BaseCommand
from api.supabase_utils import get_supabase_client
from api.sportradar_utils import get_sportradar_data
import pandas as pd
import uuid


class Command(BaseCommand):
    help = 'Fetch teams from Sportradar and populate the Supabase teams table'

    def handle(self, *args, **options):
        supabase = get_supabase_client()

        # Check and clear existing data
        existing_teams = supabase.table('teams').select('id').execute()
        if existing_teams.data:
            # Generate a random UUID that won't match any existing id
            non_existent_uuid = str(uuid.uuid4())
            delete_result = supabase.table('teams').delete().neq(
                'id', non_existent_uuid).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {len(delete_result.data)} existing team records."))
        else:
            self.stdout.write(self.style.SUCCESS(
                "The teams table was already empty."))

        # Fetch schedule data from Sportradar
        schedule_data = get_sportradar_data('games/2023/REG/schedule.json')

        # Extract teams
        teams = {}
        for game in schedule_data['games']:
            home_team = game['home']
            away_team = game['away']
            teams[home_team['id']] = home_team['name']
            teams[away_team['id']] = away_team['name']

        # Convert to DataFrame
        teams_df = pd.DataFrame(list(teams.items()), columns=['id', 'name'])

        # List of team IDs to remove (non-NBA teams)
        teams_to_remove = [
            '2674a061-2cb1-4a0b-b0b6-e237ff267f45',
            '739e187c-5d96-477d-a2fb-5f40439138fc',
            '849c6b54-2cdc-4242-b194-7f7edd2ee341',
            'd64e9292-0b2b-4c21-a623-fcadad5496f5',
            '592d3144-895b-43e9-ab15-e84666a845d5',
            '787ff06f-f0cc-484e-8114-04e0cdc444fa'
        ]

        # Remove non-NBA teams
        teams_df = teams_df[~teams_df['id'].isin(teams_to_remove)]
        teams_df = teams_df.reset_index(drop=True)

        # Convert DataFrame to list of dictionaries
        teams_data = teams_df.to_dict('records')

        # Insert data into Supabase
        result = supabase.table('teams').insert(teams_data).execute()

        # Check the result
        if result.data:
            self.stdout.write(self.style.SUCCESS(
                f"Successfully inserted {len(result.data)} teams."))
        else:
            self.stdout.write(self.style.ERROR("Failed to insert teams."))
            self.stdout.write(self.style.ERROR(f"Error: {result.error}"))

        # Verify the insertion
        fetched_teams = supabase.table('teams').select('*').execute()
        self.stdout.write(self.style.SUCCESS(
            f"Total teams in Supabase after insertion: {len(fetched_teams.data)}"))

        self.stdout.write(self.style.SUCCESS(
            'Finished populating teams table'))
