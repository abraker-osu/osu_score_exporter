import sys
import os
import time
import requests
import hashlib
import base64
import struct
import datetime

from ossapi import *
import numpy as np

from osu_analysis import BeatmapIO, ReplayIO
from osu_analysis import StdMapData, StdReplayData, StdScoreData
from rate_limited import rate_limited
from api_key import client_id, client_secret, apiv1_key


# Thanks https://github.com/Xferno2/CSharpOsu/blob/master/CSharpOsu/CSharpOsu.cs
@rate_limited(rate_limit=10)
def fetch_replay_file(apiv1, score_id, mods, beatmap_id, player_id, username):
    gamemode = 0

    replay_data = apiv1.get_replay({
        's' : score_id
    })

    try: replay_data = base64.b64decode(replay_data['content'], validate=True)
    except KeyError:
        print(f'Error decoding replay. content: {replay_data}')
        return None

    beatmap_info = apiv1.get_beatmaps({
        'b' : beatmap_id
    })

    if len(beatmap_info) == 0:
        print(f'apiv1.get_beatmaps: No beatmaps with beatmap id {beatmap_id} found!')
        return None

    beatmap_info = beatmap_info[0]

    score_info = apiv1.get_scores({
        'b' : map_id,
        'u' : player_id,
        'm' : gamemode,
        'mods' : mods
    })

    if len(score_info) == 0:
        print(f'apiv1.get_scores: No scores found!')
        return None
    score_info = score_info[0]

    version     = 0
    rank        = score_info['rank']
    count_300   = score_info['count300']
    count_100   = score_info['count100']
    count_50    = score_info['count50']
    count_geki  = score_info['countgeki']
    count_katsu = score_info['countkatu']
    count_miss  = score_info['countmiss']
    score       = score_info['score']
    max_combo   = score_info['maxcombo']
    perfect     = score_info['perfect']
    mods        = score_info['enabled_mods']
    lifebar_hp  = ''
    score_date  = score_info['date']
    score_id    = score_info['score_id']

    beatmap_md5 = beatmap_info['file_md5']
    replay_hash = hashlib.md5(str(max_combo + 'osu' + username + beatmap_md5 + score + rank).encode('utf-8')).hexdigest()

    data =  struct.pack('<bi', int(gamemode), int(version))
    data += struct.pack('<x' + str(len(beatmap_md5)) + 'sx', str(beatmap_md5).encode('utf-8'))
    data += struct.pack('<x' + str(len(username))   + 'sx', str(username).encode('utf-8'))
    data += struct.pack('<x' + str(len(replay_hash)) + 'sx', str(replay_hash).encode('utf-8'))
    data += struct.pack('<hhhhhhih?i',
        int(count_300), int(count_100), int(count_50), int(count_geki), int(count_katsu), int(count_miss),
        int(score), int(max_combo), int(perfect), int(mods))
    data += struct.pack('<x' + str(len(lifebar_hp)) + 'sx', str(lifebar_hp).encode('utf-8'))

    score_date, score_time = score_date.split(' ')
    score_year, score_month, score_day = score_date.split('-')
    score_hour, score_min, score_sec   = score_time.split(':')
    timestamp = datetime.datetime.timestamp(datetime.datetime(int(score_year), month=int(score_month), day=int(score_day), hour=int(score_hour), minute=int(score_min), second=int(score_sec)))
    
    data += struct.pack('<qi', int(timestamp), int(len(replay_data)))
    data += replay_data
    data += struct.pack('<q', int(score_id))

    return data


def process_mods(map_data, replay_data, replay, ar, cs):
    mods = 0
    print(f' applying mods: [ {replay.mods} ]...', end='')

    if replay.mods.has_mod('DT') or replay.mods.has_mod('NC'):
        mods |= (1 << 0)

    if replay.mods.has_mod('HT'):
        mods |= (1 << 1)

    if replay.mods.has_mod('HR'):
        mods |= (1 << 2)
        cs += min(10, cs*1.3)
        ar += min(10, ar*1.4)

    if replay.mods.has_mod('EZ'):
        mods |= (1 << 3)
        cs /= 2
        ar /= 2

    if replay.mods.has_mod('HD'):
        mods |= (1 << 4)

    if replay.mods.has_mod('FL'):
        mods |= (1 << 5)

    return mods, ar, cs


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('TODO: print help')
        sys.exit(1)

    try: map_id = int(sys.argv[1])
    except (IndexError, ValueError):
        print('TODO: print help')
        sys.exit(1)

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    # Fetch the map
    session = requests.session()
    response = session.get(f'https://osu.ppy.sh/osu/{map_id}', timeout=5)

    if response.status_code != 200:
        print(f'Error downloading beatmap | Error {response.status_code}')
        sys.exit(1)

    # OssapiV2 caches oauth token, so clear it in case it has expired
    OssapiV2.clear_authentication()

    # Initialize osu!api
    apiv2 = OssapiV2(client_id, client_secret)
    apiv1 = Ossapi(apiv1_key)

    # Download the map
    map_path = f'tmp/{map_id}.osu'
    with open(map_path, 'wb') as fd:
        fd.write(response.content)

    # Process the map
    beatmap = BeatmapIO.open_beatmap(map_path)
    
    try: map_data = StdMapData.get_map_data(beatmap)
    except TypeError as e:
        print(e)
        sys.exit(1)

    # osu!apiv2 request to get top 50 scores
    scores = apiv2.beatmap_scores(map_id, 'osu').scores
    user_ids = [ score.user_id for score in scores ]

    scores   = []
    metadata = []
    
    # Got through scores and get replays
    for user_id, i in zip(user_ids, range(len(user_ids))):
        score = apiv2.beatmap_user_score(map_id, user_id, 'osu').score

        if score.replay == False:
            print(f'{i}: Score id {score.id} has no replay. Skipping...')
            continue

        print(f'{i} - score id {score.id}: downloading replay...', end='')

        # osu!apiv1 request to download replay
        replay_data = fetch_replay_file(apiv1, score.id, score.mods.value, map_id, user_id, score.user.username)
        if type(replay_data) == type(None):
            sys.exit(1)

        # Process the replay
        print(' processing replay...', end='')
        replay = ReplayIO.load_replay(replay_data)

        try: replay_data = StdReplayData.get_replay_data(replay)
        except TypeError as e:
            print(e)
            sys.exit(1)

        # Process score
        print(' processing score...', end='')

        mods, ar, cs = process_mods(map_data, replay_data, replay, beatmap.difficulty.ar, beatmap.difficulty.cs)
        ar_ms = 1800 - 120*ar if ar <= 5 else 1950 - 150*ar
        cs_px = (109 - 9*cs)/2

        score_data = StdScoreData.get_score_data(replay_data, map_data, ar_ms=ar_ms, cs_px=cs_px)
        scores.append(score_data)
        metadata.append({
            'score_id' : score.id, 
            'ar_ms'    : ar_ms,
            'cs_px'    : cs_px
        })

        print(' done')

    # Calculate numpy array size
    num_rows = 0

    for score in scores:
        num_rows += len(score)

    score_data = np.zeros((num_rows, 12))

    # Compile data into numpy array
    offset = 0

    for score, i in zip(scores, range(len(scores))):
        block_size = len(score)

        score_data[offset : offset + block_size, 0] = i
        score_data[offset : offset + block_size, 1] = metadata[i]['score_id']
        score_data[offset : offset + block_size, 2] = score['map_t']
        score_data[offset : offset + block_size, 3] = score['map_x']
        score_data[offset : offset + block_size, 4] = score['map_y']
        score_data[offset : offset + block_size, 5] = score['replay_t'] - score['map_t']
        score_data[offset : offset + block_size, 6] = score['replay_x'] - score['map_x']
        score_data[offset : offset + block_size, 7] = score['replay_y'] - score['map_y']
        score_data[offset : offset + block_size, 8] = score['type']
        score_data[offset : offset + block_size, 9] = score['action']
        score_data[offset : offset + block_size, 10] = metadata[i]['ar_ms']
        score_data[offset : offset + block_size, 11] = metadata[i]['cs_px']

        offset += block_size
        
    with open(f'tmp/{map_id}.npy', 'wb') as f:
        np.save(f, score_data)

    sys.exit(0)