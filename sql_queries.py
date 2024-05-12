import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
CREATE TABLE IF NOT EXISTS staging_events
    (
        artist          VARCHAR      NULL,
        auth            VARCHAR      NULL,
        firstName       VARCHAR      NULL,
        gender          VARCHAR      NULL,
        itemInSession   INT          NULL,
        lastName        VARCHAR      NULL,
        length          DECIMAL      NULL,
        level           VARCHAR      NULL,
        location        VARCHAR      NULL,
        method          VARCHAR      NULL,
        page            VARCHAR      NULL,
        registration    DECIMAL      NULL,
        sessionId       INT          NOT NULL   PRIMARY KEY,
        song            VARCHAR      NULL,
        status          INTEGER      NULL,
        ts              BIGINT       NOT NULL,
        userAgent       VARCHAR      NULL,
        userId          INTEGER      NULL                      
                              
    )
""")

staging_songs_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_songs
    (
        num_songs        INT            NULL,
        artist_id        VARCHAR        NULL,
        artist_longitude DECIMAL        NULL,
        artist_latitude  DECIMAL        NULL,
        artist_location  VARCHAR        NULL,
        artist_name      VARCHAR        NULL,
        song_id          VARCHAR        NOT NULL    PRIMARY KEY,
        title            VARCHAR        NULL,
        duration         DECIMAL        NULL,
        year             INT            NULL                           
                              
    )                         
""")

songplay_table_create = ("""
CREATE TABLE IF NOT EXISTS songplays
    (
        songplay_id INTEGER IDENTITY(0,1)       NOT NULL    PRIMARY KEY,
        start_time TIMESTAMP                    NOT NULL,
        user_id    INTEGER                      NOT NULL,
        level      VARCHAR                      NOT NULL,
        song_id    VARCHAR                      NOT NULL,
        artist_id  VARCHAR                      NOT NULL,
        session_id INTEGER                      NOT NULL,
        location   VARCHAR                      NULL,
        user_agent VARCHAR                      NULL
    )                       
""")

user_table_create = ("""
CREATE TABLE IF NOT EXISTS users
    (
        user_id    INT PRIMARY KEY sortkey      NOT NULL,
        first_name VARCHAR                      NULL,
        last_name  VARCHAR                      NULL,
        gender     VARCHAR                      NULL,
        level      VARCHAR                      NULL
    )
    diststyle ALL;
""")

song_table_create = ("""
CREATE TABLE IF NOT EXISTS songs
  (
        song_id   VARCHAR PRIMARY KEY      NOT NULL,
        title     VARCHAR                  NULL,
        artist_id VARCHAR                  NULL,
        year      INT                      NULL,
        duration  DECIMAL                  NULL
  ) 
    diststyle ALL; 
""")

artist_table_create = ("""
CREATE TABLE IF NOT EXISTS artists
    (
        artist_id VARCHAR PRIMARY KEY SORTKEY   NOT NULL,
        name      VARCHAR                       NULL,
        location  VARCHAR                       NULL,
        latitude  DECIMAL                       NULL,
        longitude DECIMAL                       NULL
    )
    diststyle ALL;
""")

time_table_create = ("""
CREATE TABLE IF NOT EXISTS time
    (
        start_time TIMESTAMP       NOT NULL    PRIMARY KEY  SORTKEY,
        hour       INT             NULL,
        day        INT             NULL,
        week       INT             NULL,
        month      INT             NULL,
        year       INT             NULL,
        weekday    INT             NULL
    )
    diststyle ALL;
""")

# STAGING TABLES
ARN = config.get('IAM_ROLE', 'ARN')
LOG_DATA = config.get('S3', 'LOG_DATA')
LOG_JSONPATH = config.get('S3', 'LOG_JSONPATH')
SONG_DATA = config.get('S3', 'SONG_DATA')

staging_events_copy = ("""
    COPY staging_events from {}
    IAM_ROLE '{}'
    JSON {}
    TIMEFORMAT 'epochmillisecs'  
    REGION 'us-west-2';                        
""").format(LOG_DATA , ARN ,LOG_JSONPATH)

staging_songs_copy = ("""
    COPY staging_songs FROM {}
    CREDENTIALS 'aws_iam_role={}'
    JSON 'auto'
    REGION 'us-west-2';
""").format(SONG_DATA ,ARN)

# FINAL TABLES

songplay_table_insert = ("""
INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
SELECT DISTINCT 
    timestamp 'epoch' + e.ts / 1000 * interval '1 second' AS start_time,
    e.userId,
    e.level,
    s.song_id,
    s.artist_id,
    e.sessionId,
    e.location,
    e.userAgent 
   FROM
      staging_events e 
    JOIN
         staging_songs s
         ON e.artist = s.artist_name 
         AND s.title = e.song 
   WHERE
      e.page = 'NextSong';                                                                   
                         
""")

user_table_insert = ("""
INSERT INTO users (user_id, first_name, last_name, gender, level) 
   SELECT DISTINCT
      e.userid,
      e.firstName,
      e.lastName,
      e.gender,
      e.level 
   FROM
      staging_events e
   WHERE
      e.page = 'NextSong';
""")

song_table_insert = ("""
INSERT INTO songs (song_id, title, artist_id, year, duration) 
   SELECT DISTINCT
      s.song_id,
      s.title,
      s.artist_id,
      s.year,
      s.duration 
   FROM
      staging_songs s;
""")

artist_table_insert = ("""
INSERT INTO artists (artist_id, name, location, latitude, longitude) 
   SELECT DISTINCT
      s.artist_id,
      s.artist_name,
      s.artist_location,
      s.artist_latitude,
      s.artist_longitude 
   FROM
      staging_songs s;
""")

time_table_insert = ("""
INSERT INTO time ( start_time, hour, day, week, month, year, weekday ) 
   SELECT DISTINCT
      timestamp 'epoch' + e.ts * interval '1 second' as start_time,
      extract(hour    FROM   start_time),
      extract(day     FROM   start_time),
      extract(week    FROM   start_time),
      extract(month   FROM  start_time),
      extract(year    FROM   start_time),
      extract(week    FROM   start_time) 
   FROM
      staging_events e 
   WHERE
      e.page = 'NextSong';


""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
