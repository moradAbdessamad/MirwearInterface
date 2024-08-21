import json
import re

def extract_and_save_json(message_content, output_file):
    # Extract JSON content from the message using regular expression
    json_match = re.search(r'```json\n(.*?)\n```', message_content, re.DOTALL)
    
    if json_match:
        json_content = json_match.group(1)
        
        # Convert the JSON content string to a Python dictionary
        try:
            json_data = json.loads(json_content)
            
            # Save the JSON data to a file
            with open(output_file, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            
            print(f"JSON data successfully extracted and saved to {output_file}")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON content: {e}")
    else:
        print("No JSON content found in the message.")

# Example usage:
message = """
ChatCompletionMessage(content='Based on the provided wardrobe data and the given criteria, I\'ve generated three complete style recommendations that meet the requirements. Here are the recommendations:\n\n```json\n{\n    "style_1": {\n        "top": {\n            "image": "2135.jpg",\n            "type": "Kurtas",\n            "gender": "Women",\n            "color": "saddlebrown",\n            "season": "Summer",\n            "style": "Ethnic"\n        },\n        "bottom": {\n            "image": "13247.jpg",\n            "type": "Leggings",\n            "gender": "Women",\n            "color": "darkslategray",\n            "season": "Summer",\n            "style": "Casual"\n        },\n        "shoes": {\n            "image": "15331.jpg",\n            "type": "Sports Shoes",\n            "gender": "Women",\n            "color": "gainsboro",\n            "season": "Summer",\n            "style": "Casual"\n        }\n    },\n    "style_2": {\n        "top": {\n            "image": "2268.jpg",\n            "type": "Tops",\n            "gender": "Women",\n            "color": "darkgrey",\n            "season": "Summer",\n            "style": "Casual"\n        },\n        "bottom": {\n            "image": "13249.jpg",\n            "type": "Track Pants",\n            "gender": "Women",\n            "color": "black",\n            "season": "Summer",\n            "style": "Casual"\n        },\n        "shoes": {\n            "image": "15331.jpg",\n            "type": "Sports Shoes",\n            "gender": "Women",\n            "color": "gainsboro",\n            "season": "Summer",\n            "style": "Casual"\n        }\n    },\n    "style_3": {\n        "top": {\n            "image": "2293.jpg",\n            "type": "Tshirts",\n            "gender": "Women",\n            "color": "hotpink",\n            "season": "Summer",\n            "style": "Casual"\n        },\n        "bottom": {\n            "image": "13259.jpg",\n            "type": "Jeans",\n            "gender": "Women",\n            "color": "darkslategray",\n            "season": "Summer",\n            "style": "Casual"\n        },\n        "shoes": {\n            "image": "15331.jpg",\n            "type": "Sports Shoes",\n            "gender": "Women",\n            "color": "gainsboro",\n            "season": "Summer",\n            "style": "Casual"\n        }\n    }\n}\n```\n\nThese style recommendations meet the given criteria, which includes:\n\n* Season: Summer\n* Gender: Female\n* Color: Any\n* Style: Casual\n\nEach style recommendation includes a top, bottom, and shoes that align with the given criteria. The combinations are coherent and stylish, and the output is formatted as required.', role='assistant', function_call=None, tool_calls=None)
"""

extract_and_save_json(message_content=message, output_file="D:/OSC/MirwearInterface/JSONstyles/style_recommendations.json")
