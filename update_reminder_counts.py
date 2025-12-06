import json
import os
from collections import Counter

def get_integer_input(prompt):
    """Continuously prompts the user until a valid integer is entered."""

    while True:
        try:
            value = input(prompt)
            # Allow empty input to mean 0
            if value.strip() == "":
                return 1
            if value.strip() == "skip":
                return None
            return int(value)
        except ValueError:
            print("  Invalid input. Please enter a whole number.")


def update_reminder_counts(input_file, output_file):
    """
    Interactively updates reminder counts for characters in a JSON file.

    Reads character data from input_file, prompts the user for the number
    of each reminder token needed, and writes the updated data to output_file.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file not found at '{input_file}'")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        all_characters = json.load(f)

    combine_workaround_data(all_characters)
    updated_characters = []

    print("--- Starting Reminder Count Update ---")
    print("For each character, please enter the number of tokens you need for each reminder type.")
    print("Pressing Enter without a number will count as 0.\n")

    for character in all_characters:
        char_name = character.get("name", "Unknown Character")
        
        if "reminders" in character and isinstance(character["reminders"], list) and character["reminders"]:
            print(f"--- Character: {char_name} ---")
            print(f'Ability: {character["ability"]}')
            print(f'Reminders: {character["reminders"]}')
            
            unique_reminders = sorted(list(Counter(character["reminders"]).keys()))
            
            new_reminders_data = []
            for reminder_text in unique_reminders:
                prompt = f"  - How many '{reminder_text}' reminder tokens are needed? "
                count = get_integer_input(prompt)
                if count is None:
                    continue
                if count > 0:
                    new_reminders_data.append({"text": reminder_text, "count": count})
            
            character["reminders"] = new_reminders_data
            print(f"Updated reminders for {char_name}.\n")

        updated_characters.append(character)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(updated_characters, f, indent=4, ensure_ascii=False)

    print("--- Update Complete ---")
    print(f"New JSON file with updated reminder counts has been saved to '{output_file}'")


def combine_workaround_data(data):
    for character in data:
        if 'tokens' in character['id']:
            id =  character['id'].replace('tokens', '')
            for char in data:
                if char['id'].lower() == id:
                    if 'reminders' in char:
                        char['reminders'].extend(character['reminders'])
                    else:
                        char['reminders'] = character['reminders']
    # output_file = 'menagerie_debug.json'
    # print('debug')
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)




if __name__ == '__main__':
    INPUT_JSON_PATH = 'menagerie.json'
    OUTPUT_JSON_PATH = 'menagerie_with_counts.json'
    update_reminder_counts(INPUT_JSON_PATH, OUTPUT_JSON_PATH)