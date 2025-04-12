import pandas as pd
import json
import re


df = pd.read_csv("haas_3_25.csv", header=None, names=["Index", "Timestamp", "RawData"])


def fix_and_parse_json(raw):
    try:
        raw = str(raw)

        # Remove outermost quotes if present
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]

        # Replace "" with " (double-double quote to single)
        raw = raw.replace('""', '"')

        
        raw = re.sub(r'\\"([^"]+)\\"(?=\s*:)', r'"\1"', raw)

       
        raw = re.sub(r'"{1,2}([^":]+)"{1,2}(?=\s*:)', r'"\1"', raw)

        # Try parsing
        return json.loads(raw)

    except json.JSONDecodeError as e:
        print("JSON error:", e)
        print("Offending raw data:", raw[:300])
        return {}
    except Exception as e:
        print("Unexpected error:", e)
        return {}


parsed_data = df["RawData"].apply(fix_and_parse_json)


expanded_df = pd.json_normalize(parsed_data)


final_df = pd.concat([df[["Index", "Timestamp"]], expanded_df], axis=1)


final_df.to_csv("3_25_expanded.csv", index=False)


print("Successfully expanded data:")
print(final_df.head())
