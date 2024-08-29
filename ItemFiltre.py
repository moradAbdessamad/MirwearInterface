import json

# Define your lists
top_list = [[
    "T-shirt", "Polo shirt", "Blouse", "Dress shirt", "Sweater", "Hoodie", "Cardigan", "Tank top",
    "Blazer", "Suit jacket", "Crop top", "Tube top", "Long sleeve shirt", "Henley shirt", "Graphic tee",
    "Rugby shirt", "Tunic", "Peplum top", "Wrap top", "Bodysuit", "Camisole", "Sweatshirt", "Pullover",
    "Coat", "Raincoat", "Trench coat", "Overcoat", "Windbreaker", "Parka", "Down jacket", "Bomber jacket",
    "Denim jacket", "Leather jacket", "Vest", "Poncho", "Cape", "Peacoat", "Duster coat", "Anorak", 
    "Shacket", "Gilet", "Dress", "Evening gown", "Cocktail dress", "Sundress", "Wrap dress", 
    "Maxi dress", "Midi dress", "Mini dress", "Sheath dress", "Shift dress", "A-line dress", 
    "Peplum dress", "Ball gown", "Bodycon dress", "Tunic dress", "T-shirt dress", "Skater dress", 
    "Shirt dress", "Sweater dress", "Slip dress", "Off-the-shoulder dress", "Pinafore dress", "Blazer dress"
]]
bottom_list = [[
    "Jeans", "Chinos", "Dress pants", "Cargo pants", "Shorts", "Skirt", "Mini skirt", "Maxi skirt", 
    "Pencil skirt", "A-line skirt", "Pleated skirt", "Wrap skirt", "Culottes", "Capri pants", "Leggings",
    "Joggers", "Sweatpants", "Tracksuit", "Palazzo pants", "Wide-leg pants", "Overalls", "Jumpsuit", 
    "Romper", "Dungarees", "Bike shorts", "Skort", "Swim trunks", "Board shorts", "Swim briefs", "Sarong",
    "Cover-up", "Pajamas", "Lounge pants", "Sleep shorts"
]]
foot_list = [[
    "Flip flops", "Sandals", "Sneakers", "Dress shoes", "Loafers", "Oxfords", "Boots", "Ankle boots",
    "Knee-high boots", "Chelsea boots", "Combat boots", "Cowboy boots", "Wellington boots", "Riding boots",
    "Wedges", "Heels", "Flats", "Espadrilles", "Mules", "Clogs", "Brogues", "Slippers", "Moccasins", 
    "Derby shoes", "Monk strap shoes", "Boat shoes", "Ballet flats", "Platform shoes", "Stilettos", "Kitten heels"
]]

# Flatten the lists
top_list = [item for sublist in top_list for item in sublist]
bottom_list = [item for sublist in bottom_list for item in sublist]
foot_list = [item for sublist in foot_list for item in sublist]

# Load the original JSON data
input_path = 'D:/OSC/MirwearInterface/static/JSONstyles/style.json'
with open(input_path, 'r') as file:
    data = json.load(file)

# Initialize the output dictionary
filtered_data = {'top': {}, 'bottom': {}, 'foot': {}}

# Filter the data based on the lists
for image, attributes in data.items():
    if attributes['type'] in top_list:
        filtered_data['top'][image] = attributes
    elif attributes['type'] in bottom_list:
        filtered_data['bottom'][image] = attributes
    elif attributes['type'] in foot_list:
        filtered_data['foot'][image] = attributes

# Clear the existing items in itemsByType.json
output_path = 'D:/OSC/MirwearInterface/static/JSONstyles/itemsByType.json'
with open(output_path, 'w') as outfile:
    json.dump({}, outfile, indent=4)  # Save an empty dictionary to clear the file

# Save the filtered JSON to itemsByType.json
with open(output_path, 'w') as outfile:
    json.dump(filtered_data, outfile, indent=4)

print(f"Filtered JSON has been saved to {output_path}")
