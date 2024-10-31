######      USAGE       ########
#   Change input file to be the json file with knobs from llamatune
#   Change output file to be the file you want to store converted knobs
#   Change knob_spec in the config file (i.e. cybernetics/configs/benchbase/tpcc/postgres_bo_gp.local.ini) to match OUPUT_FILE
################################

import json

INPUT_FILE = "llamatune_13_knobs.json"

with open(INPUT_FILE, "r") as f:
    knobs = json.load(f)

for knob in knobs:
    knob["vartype"] = knob["type"]
    knob["boot_val"] = knob["default"]
    knob["reset_val"] = knob["default"]
    knob["setting"] = knob["default"]
    # print(knob.keys())
    if "min" in knob:
        knob["min_val"] = knob["min"]
    if "max" in knob:
        knob["max_val"] = knob["max"]
    if "choices" in knob:
        knob["enumvals"] = knob["choices"]

OUTPUT_FILE = "converted_file.json"

with open("converted_file.json", 'w') as f:
    json.dump(knobs, f, indent = 4)
