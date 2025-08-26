# Load data from testdata.txt
# Read each line and match it against the regex
# Print the match

import re
import json

REGEXS = []
CAPTURES = []

with open('config.json.example', 'r') as f:
    config = json.load(f)
    for regex in config['config']['regex']:
        REGEXS.append(regex['match'])
        CAPTURES.append(regex['capture'])

with open('testdata.txt', 'r') as f:
    for line in f:
        for i in range(len(REGEXS)):
            REGEX = REGEXS[i]
            CAPTURE = CAPTURES[i]
            match = re.match(REGEX, line)
            if match:
                # print(match.group(1), match.group(2), match.group(3))
                groups = match.groups()
                ouput = CAPTURE.format(groups=groups)
                print(ouput)