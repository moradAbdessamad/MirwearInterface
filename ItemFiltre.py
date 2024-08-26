import json

# Define your lists
top_list = [['Belts', 'Blazers', 'Dresses', 'Dupatta', 'Jackets', 'Kurtas',
       'Kurtis', 'Lehenga Choli', 'Nehru Jackets', 'Rain Jacket',
       'Rompers', 'Shirts', 'Shrug', 'Suspenders', 'Sweaters',
       'Sweatshirts', 'Tops', 'Tshirts', 'Tunics', 'Waistcoat']]
bottom_list = [['Capris', 'Churidar', 'Jeans', 'Jeggings', 'Leggings', 'Patiala',
       'Salwar', 'Salwar and Dupatta', 'Shorts', 'Skirts', 'Stockings',
       'Swimwear', 'Tights', 'Track Pants', 'Tracksuits', 'Trousers']]
foot_list = [['Casual Shoes', 'Flats', 'Flip Flops', 'Formal Shoes', 'Heels',
       'Sandals', 'Sports Sandals', 'Sports Shoes']]

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
