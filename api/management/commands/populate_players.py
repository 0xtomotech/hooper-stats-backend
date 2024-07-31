from django.core.management.base import BaseCommand
from api.sportradar_utils import get_sportradar_data
from api.supabase_utils import get_supabase_client


class Command(BaseCommand):
    help = 'Fetch Phoenix Suns players from Sportradar and populate the Supabase players table'

    def handle(self, *args, **options):
        supabase = get_supabase_client()

        # Step 1: Fetch Phoenix Suns team ID from the teams table
        suns_team = supabase.table('teams').select(
            'id').eq('name', 'Phoenix Suns').execute()
        suns_id = suns_team.data[0]['id']
        self.stdout.write(self.style.SUCCESS(f"Phoenix Suns ID: {suns_id}"))

        # Step 2: Fetch Phoenix Suns players from Sportradar API
        suns_data = get_sportradar_data(f'teams/{suns_id}/profile.json')

        # Step 3: Extract players data
        players_data = suns_data['players']

        # Step 4: Transform players data into the format we need
        players_to_insert = [
            {
                'id': player['id'],
                'name': player['full_name'],
                'team_id': suns_id
            }
            for player in players_data
        ]

        # Step 5: Check for existing players and handle updates/deletions
        existing_players = supabase.table('players').select(
            '*').eq('team_id', suns_id).execute()
        existing_ids = set(player['id'] for player in existing_players.data)
        new_ids = set(player['id'] for player in players_to_insert)

        players_to_delete = existing_ids - new_ids
        players_to_insert = [player for player in players_to_insert if player['id'] in (
            new_ids - existing_ids)]
        players_to_update = [player for player in players_to_insert if player['id'] in (
            new_ids & existing_ids)]

        self.stdout.write(self.style.SUCCESS(
            f"Found {len(existing_ids)} existing players for the Suns."))
        self.stdout.write(self.style.SUCCESS(
            f"Fetched {len(new_ids)} players from the API."))
        self.stdout.write(self.style.SUCCESS(
            f"Will delete {len(players_to_delete)} players."))
        self.stdout.write(self.style.SUCCESS(
            f"Will insert {len(players_to_insert)} new players."))
        self.stdout.write(self.style.SUCCESS(
            f"Will update {len(players_to_update)} existing players."))

        # Delete players not in the new set
        if players_to_delete:
            delete_result = supabase.table('players').delete().in_(
                'id', list(players_to_delete)).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {len(delete_result.data)} players no longer on the team."))

        # Insert new players
        if players_to_insert:
            insert_result = supabase.table('players').insert(
                players_to_insert).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Inserted {len(insert_result.data)} new players."))

        # Update existing players
        if players_to_update:
            for player in players_to_update:
                update_result = supabase.table('players').update(
                    player).eq('id', player['id']).execute()
            self.stdout.write(self.style.SUCCESS(
                f"Updated {len(players_to_update)} existing players."))

        # Verify the final state
        final_players = supabase.table('players').select(
            '*').eq('team_id', suns_id).execute()
        self.stdout.write(self.style.SUCCESS(
            f"Final count of Suns players in database: {len(final_players.data)}"))

        self.stdout.write(self.style.SUCCESS(
            'Finished populating players table'))
