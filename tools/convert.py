import pathlib as pl
import sqlite3 as sql

DIR_ASSETS = pl.Path.cwd() / 'assets'
DIR_MAP = DIR_ASSETS / 'map'
DIR_MOBS = DIR_ASSETS / 'npc' / 'pre-re' / 'mobs'
DIR_DUNGEON_SPAWN = DIR_MOBS / 'dungeons'
DIR_FIELD_SPAWN = DIR_MOBS / 'fields'
DIR_SPAWN = [DIR_DUNGEON_SPAWN, DIR_FIELD_SPAWN]


def convert():
    con = sql.connect(str(DIR_ASSETS / 'ro.db'))
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS map (name TEXT PRIMARY KEY, UNIQUE(name))")

    for file in DIR_MAP.glob('**/*.fld'):
        name = file.name.replace('.fld', '')
        cur.execute("INSERT OR IGNORE INTO map (name) VALUES (?)", (name, ))

    cur.execute("""
    CREATE TABLE IF NOT EXISTS spawn (
            map TEXT, 
            mob INTEGER,
            amount INTEGER, 
            x0 INTEGER, 
            y0 INTEGER, 
            x1 INTEGER, 
            y1 INTEGER,
            t0 INTEGER,
            t1 INTEGER,
            PRIMARY KEY (map, mob),
            FOREIGN KEY (map) REFERENCES map(name),
            FOREIGN KEY (mob) REFERENCES mob(ID)
        )
    """)

    for directory in DIR_SPAWN:
        for file in directory.glob('**/*.txt'):
            with open(file) as f:
                for line in f.readlines():
                    if line.startswith('//') or line.startswith('\n'):
                        continue
                    line = line.replace('\n', '')
                    line = line.replace('\t', ',')
                    line = line.replace('monster', ',')
                    line = line.replace('boss_', '')
                    line = line.replace(',,,', ',')
                    line = line.split(',')
                    if len(line) < 11:
                        continue

                    if line[7] == 'Detardeurus':
                        print(line)

                    cur.execute("INSERT OR IGNORE INTO spawn VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (line[0], line[6], line[7], line[1], line[2], line[3], line[4], line[8], line[9]))

    con.commit()


if __name__ == '__main__':
    convert()
