# osu_score_exporter

Processes and exports top 50 scores to npy format

Usage: `py run.py {map_id}`

Exports a file to `tmp/{map_id}.npy`


Format:
|Column | Description                   |
|-------|-------------------------------|
| 0     | player's rank                 |
| 1     | score id                      |
| 2     | map time (ms)                 |
| 3     | map x-pos (px)                |
| 4     | map y-pos (px)                |
| 5     | temporal hit offset (ms)      |
| 6     | x-axis hit offset (px)        |
| 7     | y-axis hit offset (px)        |
| 8     | score type (enum, see below)  |
| 9     | action type (enum, see below) |
| 10    | map's AR (ms)                 |
| 11    | map's CS (px)                 |

Score type:

| Value | Name  | Description
|-------|-------|----------------------------------------------------
| 0     | HITP  | A hit press has a hitobject and offset associated with it
| 1     | HITR  | A release has a hitobject and offset associated with it
| 2     | AIMH  | A hold has an aimpoint and offset associated with it
| 3     | MISS  | A miss has a hitobject associated with it, but not offset
| 4     | EMPTY | An empty has neither hitobject nor offset associated with it  

Action type:

| Value | Name    | Description
|-------|---------|----------------------------------------------------
| 0     | FREE    | Finger free to float
| 1     | PRESS   | Finger must impart force to press key
| 2     | HOLD    | Finger must keep imparting force to keep key down
| 3     | RELEASE | Finger must depart force to unpress key
