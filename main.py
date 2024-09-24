import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Config Generator API"}), 200

@app.route('/generate-config', methods=['POST'])
def generate_config():
    try:
        data = request.json

        # Access the rune_design key in a case-insensitive manner
        rune_design_param = data.get('rune_design', '').lower()
        if rune_design_param not in ['cosmic rainbow', 'classic']:
            return jsonify({"error": "Invalid rune_design parameter"}), 400
        
        # Access the filter_blocks key in a case-insensitive manner
        filter_blocks_param = data.get('filter_blocks', [])
        invalid_blocks = [block for block in filter_blocks_param if block.lower() not in ['sorceress', 'paladin', 'necromancer', 'amazon', 'assassin', 'barbarian', 'druid', 'leveling']]
        if invalid_blocks:
            return jsonify({"error": f"Invalid filter_blocks parameter: {', '.join(invalid_blocks)}"}), 400

        # Fetch base file
        base_url = "https://raw.githubusercontent.com/DoctorWoot420/cosmic-resurgence-bh/main/BH.cfg"
        base_response = requests.get(base_url)
        if base_response.status_code != 200:
            return jsonify({"error": "Failed to fetch base file"}), 400
        base_content = base_response.text

        # Fetch rune design block file
        if rune_design_param == 'cosmic-rainbow':
            rune_design_block_url = "https://raw.githubusercontent.com/DoctorWoot420/cosmic-resurgence-bh/main/filter-blocks/runes-cosmic-rainbow.bh"
        else:
            rune_design_block_url = "https://raw.githubusercontent.com/DoctorWoot420/cosmic-resurgence-bh/main/filter-blocks/runes-classic.bh"

        rune_design_block_response = requests.get(rune_design_block_url)
        if rune_design_block_response.status_code != 200:
            return jsonify({"error": f"Failed to fetch block file for {rune_design_param}"}), 400
        rune_design_block_content = rune_design_block_response.text

        # Insert block content into base content
        base_lines = base_content.splitlines()
        rune_design_insert_index = None
        for i, line in enumerate(base_lines):
            if "// start runes block" in line.lower():
                rune_design_insert_index = i + 3
                break

        if rune_design_insert_index is None:
            return jsonify({"error": "Indicator '// START RUNES BLOCK' not found in base file"}), 400

        # Fetch filter blocks block files
        filter_blocks_block_content = ""
        for block in filter_blocks_param:
            filter_blocks_block_url = f"https://raw.githubusercontent.com/DoctorWoot420/cosmic-resurgence-bh/main/filter-blocks/{block.lower()}.bh"
            filter_blocks_block_response = requests.get(filter_blocks_block_url)
            if filter_blocks_block_response.status_code != 200:
                return jsonify({"error": f"Failed to fetch block file for {block}"}), 400
            filter_blocks_block_content += filter_blocks_block_response.text + "\n"

        # Remove duplicate lines (except lines with '/////////' or empty lines)
        seen_lines = set()
        unique_block_content = []
        for line in filter_blocks_block_content.splitlines():
            if "///////" in line or line == "" or line not in seen_lines:
                unique_block_content.append(line)
                if line:  # Don't track empty lines in the seen set
                    seen_lines.add(line)

        # Clean up junk lines (extra blank lines and unnecessary headers)
        unique_block_content = clean_up_junk_lines(unique_block_content)          

        # Insert block content into base content
        base_lines = base_content.splitlines()
        filter_blocks_insert_index = None
        for i, line in enumerate(base_lines):
            if "// start filter blocks" in line.lower():
                filter_blocks_insert_index = i + 3
                break

        if filter_blocks_insert_index is None:
            return jsonify({"error": "Indicator '// START FILTER BLOCKS' not found in base file"}), 400

        # Build merged file lines from all blocks
        merged_lines = base_lines[:filter_blocks_insert_index] + unique_block_content + base_lines[filter_blocks_insert_index:rune_design_insert_index] + rune_design_block_content.splitlines() + base_lines[rune_design_insert_index:]
        merged_content = "\n".join(merged_lines)

        return jsonify({"config": merged_content}), 200
    except requests.RequestException as e:
        logging.error(f"Network error: {str(e)}")
        return jsonify({"error": "Failed to fetch required files"}), 500
    except KeyError as e:
        logging.error(f"Missing key in data: {str(e)}")
        return jsonify({"error": "Invalid request data"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def clean_up_junk_lines(lines):
    cleaned_lines = []
    blank_line_allowed = True

    for i, line in enumerate(lines):
        # If line is blank, allow only one blank line unless the next line contains slashes
        if line.strip() == "":
            if blank_line_allowed:
                cleaned_lines.append(line)
                blank_line_allowed = False  # Disable additional blank lines
        else:
            # If the current or next line has slashes, reset the blank line allowance
            if re.match(r"^/{60,}$", line.strip()) or (i + 1 < len(lines) and re.match(r"^/{60,}$", lines[i + 1].strip())):
                blank_line_allowed = True

            cleaned_lines.append(line)
            blank_line_allowed = True  # Reset to allow a blank line after content

    return cleaned_lines

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)