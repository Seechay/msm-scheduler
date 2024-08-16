import pandas as pd
import re

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday',
                'Thursday', 'Friday', 'Saturday', 'Sunday']


def _replace_n_plus_func(match):
    # Extract the number before the "+" symbol
    n = int(match.group(1))
    # Generate the sequence from n to 23
    replacement = ",".join(str(i) for i in range(n, 24))
    return replacement


def _replace_n_plus(s):
    # Function changes n+ to n,n+1,...,23
    if isinstance(s, int):
        return str(s)
    if s is None:
        return ""
    return re.sub(r"(\d+)\+", _replace_n_plus_func, s)


def format_data(df):
    stats = []
    availabilities = [{d: '' for d in DAYS_OF_WEEK + ['Identity']}
                      for i in range(df['Identity'].nunique())]
    availability_ids = set()
    experiences = []

    for i, row in df.iterrows():
        if row['Identity'] in availability_ids:
            continue

        # === Stats
        stats.append({'arcane_power': row['Arcane Power'],
                      'hp': row['HP'],
                      'identity': row['Identity'],
                      'max_damage_cap': row['MDC'],
                      'name': row['Name'],
                      'class': row['Class']})

        # === Availabilities
        n_ids = len(availability_ids)
        for dow in DAYS_OF_WEEK:
            if row[dow] == '':
                continue
            availabilities[n_ids][dow] = _replace_n_plus(row[dow])
        availabilities[n_ids]['Identity'] = row['Identity']
        availability_ids.add(row['Identity'])

        # === Experiences
        experiences.append({
            'name': row['Name'],
            'hard_damien': row['Hard Damien']
        })
    return stats, availabilities, experiences


def clean_data(df):
    # Clean data
    df["MDC"] = df["Max Damage Cap (in M)"]
    df["MDC"] = df["MDC"].astype(float)
    df["Bishop"] = df["Class"] == "Bishop"
    df['Arcane Power'] = pd.to_numeric(df['Arcane Power'], errors='coerce')
    df['Arcane Power'] = df['Arcane Power'].fillna(0).astype(int)
    df['HP'] = pd.to_numeric(df['HP (in K)'], errors='coerce')
    df['HP'] = df['HP'].fillna(70).astype(int)
    df.dropna(subset=['Max Damage Cap (in M)', 'HP (in K)'], inplace=True)

    # Mising entry in experience column is set to 0
    for boss in ['Lotus', 'Normal Damien', 'Hard Damien', 'Lucid']:
        df[boss] = pd.to_numeric(df[boss])
        df[boss] = df[boss].fillna(0).astype(int)

    df.reset_index(drop=True, inplace=True)
    return format_data(df)