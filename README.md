# Hooper Stats Backend

## 📊 A Proof of Concept Experiment

![NBA Stats](https://img.shields.io/badge/NBA-Stats-orange)
![Django](https://img.shields.io/badge/Django-5.0.7-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![Supabase](https://img.shields.io/badge/Supabase-Database-lightgrey)
![Sportradar](https://img.shields.io/badge/Sportradar-API-red)

## 🏀 Project Overview

Hooper Stats Backend is a proof of concept experiment designed to fetch, process, and store NBA game statistics, focusing primarily on the Phoenix Suns team. This Django-based project utilizes the Sportradar API for data retrieval and Supabase for data storage.

## ✨ Features

- 🏢 Fetch and store team information
- 👥 Retrieve and update player rosters
- 📅 Collect game schedules and results
- 📊 Gather player statistics for each game
- 🎯 Focus on 3-point shooting performance

## 🛠 Technologies Used

- Python 3.11
- Django 5.0.7
- Supabase
- Sportradar API
- Pandas for data manipulation

## 🚀 Setup and Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd hooperstats
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root and add the following:

   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SPORTRADAR_API_KEY=your_sportradar_api_key
   ```

5. Run migrations:
   ```
   python manage.py migrate
   ```

## 📋 Usage

The project includes several management commands to populate the database:

- Populate teams: `python manage.py populate_teams`
- Populate players: `python manage.py populate_players`
- Populate games: `python manage.py populate_games`
- Populate player stats by game: `python manage.py populate_player_stats_by_game`

## 📁 Project Structure

- `api/`: Main Django app containing models, views, and management commands
- `hooperstats/`: Project settings and configuration
- `notebooks/`: Jupyter notebooks for data exploration and testing
- `requirements.txt`: List of Python dependencies

## 💾 Data Model

The project uses the following main tables in Supabase:

| Table                | Description                                        |
| -------------------- | -------------------------------------------------- |
| teams                | Stores NBA team information                        |
| players              | Contains player details, associated with teams     |
| games                | Holds game schedules and results                   |
| player_stats_by_game | Stores player performance statistics for each game |

## 🔗 API Integration

This project integrates with the Sportradar API to fetch NBA data. The `api/sportradar_utils.py` file contains utility functions for making API requests.

## 🔄 Data Processing

Data processing is primarily done using Pandas. The project fetches data from Sportradar, transforms it, and then stores it in Supabase.

## ⚠️ Limitations and Future Improvements

- Currently focuses only on the Phoenix Suns team
- Limited to 3-point shooting statistics
- Could be expanded to include more teams and a wider range of statistics
- Potential for adding a frontend interface to visualize the data

## 🤝 Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
