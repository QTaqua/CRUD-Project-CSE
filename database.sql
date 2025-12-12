CREATE DATABASE IF NOT EXISTS GAMEofJAB_db;
USE GAMEofJAB_db;

CREATE TABLE Teams (
    team_id INTEGER PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE Matches (
    match_id INTEGER PRIMARY KEY,
    match_date DATE NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    winner_team_id INTEGER, -- Nullable until the match is played
    score_home INTEGER,
    score_away INTEGER,
    FOREIGN KEY (home_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES Teams(team_id),
    FOREIGN KEY (winner_team_id) REFERENCES Teams(team_id)
);


CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    team_id INTEGER, 
    position VARCHAR(50),
    skill_rating INTEGER, 
    FOREIGN KEY (team_id) REFERENCES Teams(team_id)
);

INSERT INTO Teams (team_id, team_name, region) VALUES
(101, 'Ironclad Vipers', 'North America'),
(102, 'Crimson Dragons', 'Europe'),
(103, 'Stellar Knights', 'Asia'),
(104, 'Desert Foxes', 'North America'),
(105, 'Arctic Wolves', 'Europe');

INSERT INTO players (player_id, player_name, team_id, position, skill_rating) VALUES
(1, 'Astraeus', 101, 'Attacker', 1850),
(2, 'Blaze', 101, 'Defender', 1790),
(3, 'Cipher', 101, 'Midlaner', 1920),
(4, 'Drifter', 101, 'Support', 1680),
(5, 'Echo', 102, 'Attacker', 1800),
(6, 'Fantom', 102, 'Defender', 1750),
(7, 'Goliath', 102, 'Midlaner', 1900),
(8, 'Havoc', 102, 'Support', 1700),
(9, 'Ignis', 103, 'Attacker', 1950),
(10, 'Jinx', 103, 'Defender', 1880),
(11, 'Krypton', 103, 'Midlaner', 1770),
(12, 'Lumin', 103, 'Support', 1650),
(13, 'Maverick', 104, 'Attacker', 1720),
(14, 'Nova', 104, 'Defender', 1690),
(15, 'Ozone', 104, 'Midlaner', 1810),
(16, 'Pulse', 104, 'Support', 1760),
(17, 'Quasar', 105, 'Attacker', 1910),
(18, 'Rogue', 105, 'Defender', 1820),
(19, 'Specter', 105, 'Midlaner', 1730),
(20, 'Titan', 105, 'Support', 1990);

INSERT INTO Matches (match_id, match_date, home_team_id, away_team_id, winner_team_id, score_home, score_away) VALUES
(1, '2025-11-10', 101, 102, 101, 3, 1),
(2, '2025-11-11', 103, 104, 104, 0, 2),
(3, '2025-11-12', 105, 101, 105, 4, 3);