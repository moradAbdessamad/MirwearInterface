import os
import json
import tkinter as tk
from tkinter import Label, Button
from transformers import CLIPProcessor, CLIPModel
from PIL import Image, ImageTk

# Initialize CLIP model and processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Define the path to the image folder and output JSON file
image_folder = "./static/imagesformcam"
output_json_file = "./static/JSONstyles/style_recommendations.json"

# Define the possible types of clothing features
clothing_items = [
    "T-shirt", "Polo shirt", "Blouse", "Dress shirt", "Sweater", "Hoodie", "Cardigan", "Tank top",
    "Blazer", "Suit jacket", "Crop top", "Tube top", "Long sleeve shirt", "Henley shirt", "Graphic tee",
    "Rugby shirt", "Tunic", "Peplum top", "Wrap top", "Bodysuit", "Camisole", "Sweatshirt", "Pullover",
    "Jeans", "Chinos", "Dress pants", "Cargo pants", "Shorts", "Skirt", "Mini skirt", "Maxi skirt", 
    "Pencil skirt", "A-line skirt", "Pleated skirt", "Wrap skirt", "Culottes", "Capri pants", "Leggings",
    "Joggers", "Sweatpants", "Tracksuit", "Palazzo pants", "Wide-leg pants", "Overalls", "Jumpsuit", 
    "Romper", "Dungarees", "Bike shorts", "Skort",
    "Coat", "Raincoat", "Trench coat", "Overcoat", "Windbreaker", "Parka", "Down jacket", "Bomber jacket", 
    "Denim jacket", "Leather jacket", "Blazer", "Cardigan", "Vest", "Poncho", "Cape", "Peacoat", 
    "Duster coat", "Anorak", "Shacket", "Gilet",
    "Dress", "Evening gown", "Cocktail dress", "Sundress", "Wrap dress", "Maxi dress", "Midi dress", 
    "Mini dress", "Sheath dress", "Shift dress", "A-line dress", "Peplum dress", "Ball gown", "Bodycon dress",
    "Tunic dress", "T-shirt dress", "Skater dress", "Shirt dress", "Sweater dress", "Slip dress", 
    "Off-the-shoulder dress", "Pinafore dress", "Blazer dress",
    "Flip flops", "Sandals", "Sneakers", "Dress shoes", "Loafers", "Oxfords", "Boots", "Ankle boots",
    "Knee-high boots", "Chelsea boots", "Combat boots", "Cowboy boots", "Wellington boots", "Riding boots",
    "Wedges", "Heels", "Flats", "Espadrilles", "Mules", "Clogs", "Brogues", "Slippers", "Moccasins", 
    "Derby shoes", "Monk strap shoes", "Boat shoes", "Ballet flats", "Platform shoes", "Stilettos", "Kitten heels",
    "Belt", "Scarf", "Hat", "Beanie", "Cap", "Gloves", "Tie", "Bow tie", "Suspenders", "Sunglasses",
    "Watch", "Bracelet", "Necklace", "Earrings", "Ring", "Cufflinks", "Pocket square", "Handbag", 
    "Backpack", "Briefcase", "Wallet", "Purse", "Clutch", "Duffel bag", "Tote bag", "Bangle", 
    "Brooch", "Hairband", "Headscarf", "Bandana", "Visor", "Fascinator",
    "Bathing suit", "Bikini", "One-piece swimsuit", "Tankini", "Swim trunks", "Board shorts", 
    "Swim briefs", "Sarong", "Cover-up", "Wetsuit", "Rash guard",
    "Pajamas", "Nightgown", "Nightshirt", "Robe", "Bathrobe", "Slippers", "Lounge pants", 
    "Sweatshirt", "Hoodie", "Sleep shorts", "Sleep mask", "House shoes", "Housecoat",
    "Bra", "Sports bra", "Panties", "Briefs", "Boxer shorts", "Boxer briefs", "Thong", "G-string", 
    "Bodysuit", "Undershirt", "Thermal underwear", "Long johns", "Slip", "Shapewear", "Camisole", 
    "Lingerie", "Stockings", "Tights", "Socks", "Compression socks",
    "Kimono", "Sari", "Sarong", "Kaftan", "Abaya", "Hijab", "Burqa", "Cheongsam", "Hanbok", 
    "Dirndl", "Lederhosen", "Kilt", "Toga", "Gown", "Academic robe", "Chef's coat", "Lab coat",
    "Scrubs", "Jersey", "Team uniform", "Coveralls", "Work boots", "Apron", "Chef's hat", 
    "Nurse's uniform", "Pilot's uniform", "Military uniform", "Priest's robe", "Nun's habit"
]

men_clothing_items = [
    "Polo shirt", "Dress shirt", "Henley shirt", "Graphic tee", "Rugby shirt", 
    "Suit jacket", "Jeans", "Chinos", "Dress pants", "Cargo pants", "Shorts", 
    "Sweatpants", "Tracksuit", "Blazer", "Coat", "Overcoat", "Bomber jacket", 
    "Denim jacket", "Leather jacket", "Vest", "Peacoat", "Raincoat", "Tie", 
    "Bow tie", "Suspenders", "Watch", "Bracelet", "Cufflinks", "Pocket square", 
    "Briefcase", "Wallet", "Swim trunks", "Board shorts", "Swim briefs", 
    "Boxer shorts", "Boxer briefs", "Undershirt", "Thermal underwear", 
    "Long johns", "Socks", "Compression socks", "Work boots"
]

women_clothing_items = [
    "Blouse", "Dress shirt", "Sweater", "Cardigan", "Crop top", "Tube top", 
    "Long sleeve shirt", "Tunic", "Peplum top", "Wrap top", "Bodysuit", 
    "Camisole", "Sweatshirt", "Pullover", "Dress", "Evening gown", 
    "Cocktail dress", "Sundress", "Wrap dress", "Maxi dress", "Midi dress", 
    "Mini dress", "Sheath dress", "Shift dress", "A-line dress", 
    "Peplum dress", "Ball gown", "Bodycon dress", "Tunic dress", 
    "T-shirt dress", "Skater dress", "Shirt dress", "Sweater dress", 
    "Slip dress", "Off-the-shoulder dress", "Pinafore dress", "Blazer dress", 
    "Mini skirt", "Maxi skirt", "Pencil skirt", "A-line skirt", 
    "Pleated skirt", "Wrap skirt", "Culottes", "Leggings", "Palazzo pants", 
    "Wide-leg pants", "Romper", "Dungarees", "Skort", "Coat", 
    "Trench coat", "Cape", "Poncho", "Duster coat", "Anorak", 
    "Gilet", "High heels", "Wedges", "Flats", "Espadrilles", "Mules", 
    "Clogs", "Ballet flats", "Platform shoes", "Stilettos", 
    "Kitten heels", "Handbag", "Purse", "Clutch", "Tote bag", 
    "Bangle", "Brooch", "Hairband", "Headscarf", "Fascinator", 
    "Bikini", "One-piece swimsuit", "Tankini", "Cover-up", 
    "Nightgown", "Slip", "Lingerie", "Stockings", "Tights", "Hijab", 
    "Burqa", "Kaftan", "Sari", "Abaya", "Cheongsam", "Hanbok", 
    "Dirndl", "Chef's coat", "Apron", "Nurse's uniform", 
    "Pilot's uniform", "Nun's habit"
]

both_clothing_items = [
    "T-shirt", "Hoodie", "Tank top", "Sweater", "Sweatshirt", "Pullover", 
    "Jeans", "Joggers", "Cargo pants", "Shorts", "Overalls", "Coat", 
    "Raincoat", "Denim jacket", "Cardigan", "Blazer", "Bomber jacket", 
    "Windbreaker", "Parka", "Down jacket", "Shacket", "Sweatpants", 
    "Dungarees", "Bike shorts", "Flip flops", "Sneakers", "Loafers", 
    "Oxfords", "Boots", "Ankle boots", "Knee-high boots", "Chelsea boots", 
    "Combat boots", "Cowboy boots", "Wellington boots", "Riding boots", 
    "Brogues", "Slippers", "Moccasins", "Derby shoes", "Monk strap shoes", 
    "Boat shoes", "Scarf", "Hat", "Beanie", "Cap", "Gloves", 
    "Sunglasses", "Backpack", "Duffel bag", "Belt", "Bandana", 
    "Visor", "Bathing suit", "Robe", "Bathrobe", "Pajamas", 
    "Lounge pants", "Sweatshirt", "Hoodie", "Sleep shorts", "Sleep mask", 
    "House shoes", "Housecoat", "Socks", "Kimono", "Scrubs", 
    "Jersey", "Team uniform", "Coveralls", "Chef's hat", "Priest's robe", 
    "Lab coat", "Academic robe", "Military uniform", "Gown", "Toga", 
    "Apron", "Sarong"
]


clothing_colors = [
    "Black", "White", "Gray", "Silver", "Charcoal", "Ivory", "Beige", "Tan", "Khaki", 
    "Brown", "Chocolate", "Espresso", "Navy", "Blue", "Sky blue", "Baby blue", "Royal blue", 
    "Cobalt", "Turquoise", "Teal", "Mint", "Green", "Olive", "Forest green", "Emerald", 
    "Lime", "Chartreuse", "Yellow", "Mustard", "Gold", "Amber", "Orange", "Peach", "Coral", 
    "Salmon", "Apricot", "Red", "Crimson", "Burgundy", "Maroon", "Pink", "Hot pink", "Fuchsia", 
    "Magenta", "Blush", "Rose", "Lavender", "Purple", "Violet", "Mauve", "Plum", "Lilac", 
    "Indigo", "Denim", "Aqua", "Seafoam", "Mint green", "Cyan", "Periwinkle", "Rust", 
    "Copper", "Bronze", "Wine", "Peacock blue", "Cerulean", "Slate", "Ash", "Sage", 
    "Moss", "Kelly green", "Hunter green", "Sand", "Camel", "Off-white", "Eggshell", 
    "Cream", "Champagne", "Cinnamon", "Scarlet", "Brick red", "Terracotta", "Oxblood", 
    "Aubergine", "Taupe", "Dusty rose", "Pale pink", "Light blue", "Dark blue", 
    "Midnight blue", "Olive drab", "Neon green", "Electric blue", "Burnt orange", 
    "Sunset orange", "Ice blue", "Lilac gray", "Steel blue", "Powder blue", 
    "Mustard yellow", "Grape", "Mulberry", "Blush pink", "Mint", "Ivory white", 
    "Jet black", "Pearl", "Smoke", "Cloud", "Stone", "Cement", "Honeysuckle", 
    "Daffodil", "Sapphire", "Ruby", "Amethyst", "Jade", "Onyx", "Opal", "Coral pink", 
    "Rose gold", "Blonde", "Vanilla", "Mocha", "Espresso brown", "Mahogany", 
    "Chestnut", "Umber", "Ochre", "Saffron", "Citrine", "Malachite", "Aquamarine", 
    "Topaz", "Flamingo", "Sunflower", "Daisy", "Papaya", "Cranberry", "Raspberry", 
    "Peachy", "Teal blue", "Emerald green", "Deep purple", "Royal purple", "Pastel yellow", 
    "Pastel green", "Pastel pink", "Pastel blue", "Pastel lavender", "Neon pink", 
    "Neon yellow", "Neon orange", "Neon purple", "Neon blue", "Neon green", 
    "Bright red", "Bright blue", "Bright yellow", "Bright orange", "Dark red", 
    "Dark green", "Dark purple", "Dark gray", "Light gray", "Pale yellow", 
    "Pale blue", "Pale green", "Pale purple", "Warm gray", "Cool gray", "Bright white"
]


clothing_styles = [
    "Casual", "Formal", "Business Casual", "Smart Casual", "Athleisure", "Sportswear",
    "Vintage", "Retro", "Bohemian", "Boho-chic", "Minimalist", "Streetwear", 
    "Grunge", "Punk", "Gothic", "Preppy", "Hipster", "Classic", "Elegant", 
    "Chic", "Edgy", "Artsy", "Romantic", "Beachwear", "Resortwear", "Loungewear", 
    "Urban", "Avant-garde", "High Fashion", "Eco-friendly", "Sustainable", "Denim", 
    "Western", "Country", "Military", "Workwear", "Business", "Professional", "Mod", 
    "Skater", "Surfer", "Hippie", "Y2K", "Kawaii", "Rockabilly", "Steampunk", 
    "Cyberpunk", "Industrial", "Glam", "Haute Couture", "Feminine", "Masculine", 
    "Unisex", "Androgynous", "Ethnic", "Cultural", "Luxury", "Tailored", "Monochrome", 
    "Color-blocking", "Layered", "Sporty", "Outdoor", "Safari", "Retro-futuristic", 
    "Casual Friday", "Officewear", "Vintage-inspired", "Festival", "Glamorous", 
    "Corporate", "Dressy", "Partywear", "Eveningwear", "Cocktail", "Summer", 
    "Winter", "Autumn", "Spring", "Nautical", "Tropical", "Athletic", "Relaxed",
    "Comfortable", "All-Weather", "Formalwear", "Occasionwear", "Nightwear",
    "Daywear", "Clubwear", "Rave", "Alternative", "Underground", "Kitsch",
    "Playful", "Bold", "Sophisticated", "Subtle", "Traditional", "Modern", 
    "Contemporary", "Futuristic", "Vintage-modern", "Eclectic", "Fusion", 
    "Global", "Boho", "Resort", "Designer", "Ready-to-wear", "Pret-a-porter", 
    "Capsule Wardrobe", "Transitional", "Seaside", "Cruise", "Holiday", "Winterwear",
    "Rainwear", "Coastal", "Cottagecore", "Dark Academia", "Light Academia", 
    "E-girl", "E-boy", "Minimal", "Maximal", "Casual Chic", "Functional", 
    "Utilitarian", "Dress-down", "Polished", "Refined", "Distressed", "Layered Looks",
    "Retro Revival", "Throwback", "Era-specific", "Subculture", "Indie", 
    "Techwear", "Virtual Fashion", "Mixed Prints", "Tailored Casual", "Rural",
    "Urban Chic", "Sophisticated Urban", "Laid-back Luxury", "Artisan", 
    "Bohemian Luxe", "Gothic Chic", "Athletic Luxe", "Retro Sportswear",
    "Festival Chic", "Indie Sleek", "Classic Vintage", "Statement Pieces", 
    "Bespoke", "Handmade", "Avant-Garde Streetwear", "Vintage Boho",
    "Luxe Loungewear", "High-Street", "Designer Vintage", "Utility Fashion"
]


clothing_genders = ["Men", "Women", "Both"]


image_files = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]

# Dictionary to hold the classification results
classification_results = {}

def classify_image(image_path, text_labels):
    """Classifies the image using the CLIP model for the given text labels."""
    image = Image.open(image_path)
    inputs = processor(text=text_labels, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    best_match = text_labels[probs.argmax()]
    return best_match

def load_existing_results():
    """Load existing results from the JSON file."""
    try:
        with open(output_json_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def process_images():
    """Processes only new images in the folder and saves each result to the JSON file immediately."""
    global classification_results
    classification_results = load_existing_results()
    
    for i, image_file in enumerate(image_files, start=1):
        if image_file in classification_results:
            print(f"Skipping {i}/{len(image_files)}: {image_file} (already processed)")
            continue
        
        image_path = os.path.join(image_folder, image_file)
        
        # Classify the image in all categories
        gender_result = classify_image(image_path, clothing_genders)
        style_result = classify_image(image_path, clothing_styles)
        color_result = classify_image(image_path, clothing_colors)
        item_result = classify_image(image_path, clothing_items)
        
        # Determine gender based on the classified item
        if item_result in men_clothing_items:
            gender_result = "Men"
        elif item_result in women_clothing_items:
            gender_result = "Women"
        elif item_result in both_clothing_items:
            gender_result = "Both"

        # Store the result in the dictionary
        classification_results[image_file] = {
            "type": item_result,
            "gender": gender_result,
            "color": color_result,
            "style": style_result
        }
        
        # Save the result to the JSON file incrementally
        save_results_to_json()
        
        # Display the number of items processed
        print(f"Processed {i}/{len(image_files)}: {image_file}")

def save_results_to_json():
    """Save the classification results to a JSON file."""
    with open(output_json_file, 'w') as f:
        json.dump(classification_results, f, indent=4)

# Process all images
process_images()