#!/usr/bin/env python3
import argparse
import yaml
import os
import re
import numpy as np

def convert_triggers_to_markdown(yaml_content, result, key_comments, value_comments, extra_comments):
    """Convert trigger YAML content to markdown."""
    if 'top' in extra_comments.keys(): result += f"{extra_comments['top']}\n"
    for trigger_name, trigger_data in yaml_content.items():

        result += f"## {trigger_name}\n"

        # Process legs
        leg_count = 0
        for key in trigger_data:
            if key.startswith('leg'):
                leg_count += 1

        for i in range(1, leg_count + 1):
            leg_key = f'leg{i}'
            if leg_key in trigger_data:
                leg = trigger_data[leg_key]
                obj_name = leg.get('obj', 'Unknown')
                threshold = leg.get('threshold_cut', 'None')

                obj_path = f"{trigger_name}.{leg_key}.obj"
                if i == 1 and leg_count == 1:
                    default_result = f"- **Object**: {obj_name}\n"
                    result += insert_comment(obj_path, key_comments, value_comments, default_result)
                    if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"
                else:
                    default_result = f"- **Object {i}**: {obj_name}\n"
                    result += insert_comment(obj_path, key_comments, value_comments, default_result)
                    if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

                obj_path = f"{trigger_name}.{leg_key}.threshold_cut"
                if threshold:
                    default_result = f"  - **Threshold**: {threshold}\n"
                    result += insert_comment(obj_path, key_comments, value_comments, default_result)
                    if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

        try:
            # Process cross masks (event-level cuts)
            cross_masks = trigger_data.get('cross_masks', [])
            if cross_masks:
                default_result = "- **Cross Masks**:\n"
                obj_path = f"{trigger_name}.cross_masks"
                result += insert_comment(obj_path, key_comments, value_comments, default_result)
                if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"
                for mask in cross_masks:
                    if mask:  # Skip empty masks
                        default_result = f"  - {mask}\n"
                        obj_path = f"{trigger_name}.cross_masks.{mask}"
                        result += insert_comment(obj_path, key_comments, value_comments, default_result)
                        if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"
            else:
                result += "- **Cross Masks**: None\n"
        except:
            None

        result += "\n"

    return result

def insert_comment(obj_path, key_comments, value_comments, def_res):
    """Insert comments from YAML into markdown."""
    if obj_path in key_comments.keys():
        try:
            result = def_res.split(':')[0] + f" ({key_comments[obj_path]})" + ":" + def_res.split(':')[1] + "\n"
        except:
            result = def_res + f" ({key_comments[obj_path]})" + "\n"
    elif obj_path in value_comments.keys():
        result = def_res + f" ({value_comments[obj_path]})" + "\n"
    else:
        result = def_res + "\n"
    return result

def convert_objects_to_markdown(yaml_content, result, key_comments, value_comments, extra_comments):
    """Convert object definition YAML content to markdown."""

    for obj_name, obj_data in yaml_content.items():
        result += f"## {obj_name}\n"
        # Match dR
        if 'match_dR' in obj_data:
            obj_path = f"{obj_name}.match_dR"
            default_result = f"- **Matching ΔR**: {obj_data['match_dR']}"
            result += insert_comment(obj_path, key_comments, value_comments, default_result)
            if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

        # Eta ranges
        if 'eta_ranges' in obj_data:
            obj_path = f"{obj_name}.eta_ranges"
            default_result = "- **Eta Ranges**:"
            result += insert_comment(obj_path, key_comments, value_comments, default_result)
            for range_name, range_values in obj_data['eta_ranges'].items():
                sub_path = f"{obj_path}.{range_name}"
                default_result = f"  - **{range_name}**: {range_values}"
                result += insert_comment(sub_path, key_comments, value_comments, default_result)
                if sub_path in extra_comments.keys(): result += f"{extra_comments[sub_path]}\n"
            if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

        # Global label if present
        if 'label' in obj_data:
            obj_path = f"{obj_name}.label"
            default_result = f"- **Label**: \"{obj_data['label']}\""
            result += insert_comment(obj_path, key_comments, value_comments, default_result)
            if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

        # Process IDs
        if 'ids' in obj_data:
            obj_path = f"{obj_name}.ids"
            default_result = "\n### IDs:"
            result += insert_comment(obj_path, key_comments, value_comments, default_result)

            for id_name, id_data in obj_data['ids'].items():
                sub_path = f"{obj_path}.{id_name}"
                default_result = f"#### {id_name}"
                result += insert_comment(sub_path, key_comments, value_comments, default_result)
                if sub_path in extra_comments.keys(): result += f"{extra_comments[sub_path]}\n"

                # Label
                if 'label' in id_data:
                    sub_sub_path = f"{sub_path}.label"
                    default_result = f"- **Label**: \"{id_data['label']}\""
                    result += insert_comment(sub_sub_path, key_comments, value_comments, default_result)
                    if sub_sub_path in extra_comments.keys(): result += f"{extra_comments[sub_sub_path]}\n"

                # Notes (comments in YAML)
                comment_lines = []
                for key, value in id_data.items():
                    if isinstance(value, str) and value.startswith('#'):
                        comment_lines.append(value[1:].strip())

                # Look for comments above the ID section in the original YAML
                if comment_lines:
                    for comment in comment_lines:
                        result += f"- **Note**: {comment}\n"

                # Cuts
                if 'cuts' in id_data:
                    sub_sub_path = f"{sub_path}.cuts"
                    default_result = "- **Cuts**:"
                    result += insert_comment(sub_sub_path, key_comments, value_comments, default_result)
                    for region, cuts in id_data['cuts'].items():
                        sub_sub_sub_path = f"{sub_sub_path}.{region}"
                        default_result = f"  - **{region}**:"
                        result += insert_comment(sub_sub_sub_path, key_comments, value_comments, default_result)
                        for cut in cuts:
                            result += f"    - {cut}\n"
                        if sub_sub_sub_path in extra_comments.keys(): result += f"{extra_comments[sub_sub_sub_path]}\n"
                    if sub_sub_path in extra_comments.keys(): result += f"{extra_comments[sub_sub_path]}\n"
                result += "\n"
            if obj_path in extra_comments.keys(): result += f"{extra_comments[obj_path]}\n"

        result += "\n"

    return result

def extract_comments(yaml_file):
    """Extract comments from a YAML file that might be associated with sections."""
    with open(yaml_file, 'r') as f:
        content = f.readlines()

    key_comments = {}
    value_comments = {}
    extra_comments = {}
    current_path = []

    level, recent_indent = 0, 0
    indent_steps = [0]
    for i, line in enumerate(content):
        stripped = line.strip()

        # Handle indentation to track the current path
        indent = len(line) - len(line.lstrip())

        # reset for next object that are separated by an empty line
        if indent == 1:
            indent_steps = [0]
            current_path = []
            recent_indent = 0
            continue

        # Adjust level based on indentation
        if not stripped.startswith('#'):
            if indent > recent_indent:
                level += 1
            elif indent < recent_indent:
                level -= np.where(np.array(indent_steps[::-1]) == indent)[0][0]
            elif indent == recent_indent:
                current_path = current_path[:-1] # remove last element if same dict level
            level = level if indent > 0 else 0
            # keep track of indentation steps used (fail save for irregelar indentations)
            if indent != recent_indent:
                indent_steps.append(indent)
            recent_indent = indent

            # Adjust current path based on indentation
            current_path = current_path[:level]

            # Extract key
            if ':' in stripped and not stripped.startswith('#'):
                key = stripped.split(':', 1)[0].strip()
                current_path.append(key)

        # Store comment
        if stripped.startswith('#'):
            if ":" not in stripped and "-" not in stripped:
                # capture multipleline-comments
                try:
                    extra_comments[path_str] += "<br>" + stripped[1:].strip()
                except:
                    if 'path_str' in locals():
                        extra_comments[path_str] = ">" + stripped[1:].strip()
                    else:
                        # special treatment for the first line comment
                        extra_comments["top"] = ">" + stripped[1:].strip()
                continue
            else:
                continue

        # for the extra comments store the old path str and the indentation for proper formatting
        path_str = '.'.join(current_path)
        if "#" in stripped:
            if ": #" in stripped or ":#" in stripped:
                key_comments[path_str] = stripped.split('#')[1].strip()
            else:
                value_comments[path_str] = stripped.split('#')[1].strip()

    return key_comments, value_comments, extra_comments

def detect_file_type(yaml_content):
    """Detect if the YAML file is a trigger definition or object definition."""
    # Check for trigger-specific keys
    trigger_indicators = ['cross_masks', 'threshold_cut']
    object_indicators = ['match_dR', 'eta_ranges', 'ids']

    # Count indicators
    trigger_count = 0
    object_count = 0

    for key, value in yaml_content.items():
        if isinstance(value, dict):
            for subkey in value:
                if subkey in trigger_indicators:
                    trigger_count += 1
                if subkey in object_indicators:
                    object_count += 1
    return "objects" if object_count > trigger_count else "triggers"

def main():
    parser = argparse.ArgumentParser(description='Convert CMS YAML files to Markdown documentation')
    parser.add_argument('yaml_path', help='Path to YAML files')
    parser.add_argument('--type', '-t', choices=['triggers', 'objects', 'auto'], default='auto',
                        help='Type of YAML file (trigger, object, or auto-detect)')

    args = parser.parse_args()

    # Auto-detect file type if not specified
    file_type = args.type
    yaml_files = [y for y in os.listdir(args.yaml_path) if (y.endswith('.yaml') or y.endswith('.yml'))]

    # Load YAML file with comments
    if file_type == 'auto':
        with open(os.path.join(args.yaml_path, yaml_files[0]), 'r') as f:
            yaml_content = yaml.safe_load(f)
        file_type = detect_file_type(yaml_content)

    # Write header
    result = f"# CMS Phase-2 Level-1 {file_type.capitalize()}\n\n"

    for file in yaml_files:
        print(file)
        with open(os.path.join(args.yaml_path, file)) as f:
            yaml_content = yaml.safe_load(f)

        # Convert based on file type
        result += f"## <u>{file.replace('.yaml', '').capitalize()}</u> \n"
        if file_type == 'triggers':
            key_comments, value_comments, extra_comments = extract_comments(os.path.join(args.yaml_path, file))
            result = convert_triggers_to_markdown(yaml_content, result, key_comments, value_comments, extra_comments)
            outputDir = args.yaml_path.replace("configs", "outputs")
            outputDir = outputDir.replace("rate_table", "rate_tables")
            output = os.path.join(outputDir, 'triggers.md')
        else:  # object
            # Try to extract comments for object definitions
            key_comments, value_comments, extra_comments = extract_comments(os.path.join(args.yaml_path, file))
            result = convert_objects_to_markdown(yaml_content, result, key_comments, value_comments, extra_comments)
            outputDir = args.yaml_path.replace("configs", "outputs")
            outputDir = outputDir.replace("objects", "object_performance")
            output = os.path.join(outputDir, 'objects.md')
        result += "\n\n"

    # Write output
    with open(output, 'w') as f:
        f.write(result)

    print(f"Converted all yaml files of {args.yaml_path} to markdown file in {output}")

if __name__ == "__main__":
    main()
