from django.core.management.base import BaseCommand
from api.supabase_utils import get_supabase_client
from api.sportradar_utils import get_sportradar_data
import pandas as pd
import uuid


class Command(BaseCommand):
    help = 'Fetch teams from Sportradar and populate the Supabase teams table'

    def handle(self, *args, **options):
        supabase = get_supabase_client()

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

        # Get existing teams
        existing_teams = supabase.table('teams').select('*').execute()
        existing_team_ids = {team['id'] for team in existing_teams.data}

        # Identify teams to insert, update, or delete
        teams_to_insert = [
            team for team in teams_data if team['id'] not in existing_team_ids]
        teams_to_update = [
            team for team in teams_data if team['id'] in existing_team_ids]
        teams_to_delete = existing_team_ids - \
            {team['id'] for team in teams_data}

        # Insert new teams
        if teams_to_insert:
            insert_result = supabase.table(
                'teams').insert(teams_to_insert).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Inserted {len(insert_result.data)} new teams."))

        # Update existing teams
        for team in teams_to_update:
            update_result = supabase.table('teams').update(
                {'name': team['name']}).eq('id', team['id']).execute()
        self.stdout.write(self.style.SUCCESS(
            f"Updated {len(teams_to_update)} existing teams."))

        # Delete teams not in the new data (careful with this operation)
        if teams_to_delete:
            self.stdout.write(self.style.WARNING(
                f"Found {len(teams_to_delete)} teams to delete. This operation may fail if there are related players."))
            for team_id in teams_to_delete:
                try:
                    delete_result = supabase.table(
                        'teams').delete().eq('id', team_id).execute()
                    self.stdout.write(self.style.SUCCESS(
                        f"Deleted team with ID: {team_id}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to delete team with ID: {team_id}. Error: {str(e)}"))

        # Verify the final state
        final_teams = supabase.table('teams').select('*').execute()
        self.stdout.write(self.style.SUCCESS(
            f"Final count of teams in database: {len(final_teams.data)}"))

        self.stdout.write(self.style.SUCCESS(
            'Finished populating teams table'))
