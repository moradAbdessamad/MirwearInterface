from groq import Groq
import os
import json

# Initialize the Groq client with your API key
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

wardrobe_file_path = r'D:\OSC\MirwearInterface\static\JSONstyles\style.json'

# User wardrobe data
def load_wordrobe_data(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)
    

def extract_and_save_json(response_content, file_path):
    # Check if response_content is a ChatCompletionMessage object and extract content
    if hasattr(response_content, 'content'):
        response_content = response_content.content
    
    # Print the response to the terminal 
    print("The response of the llama model is:")
    print(response_content)

    # Ensure response_content is now a string
    if isinstance(response_content, str):        
        # Since the JSON is already in the response_content, we can attempt to directly parse it
        try:
            # Convert the string to a dictionary
            json_data = json.loads(response_content)
            
            # Write the dictionary to a file as JSON
            with open(file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            
            print(f"JSON content has been saved to {file_path}")

            # Emit the JSON data via socketio to the client
            print("The data is emitted:", json_data)
            
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
    else:
        print(f"Expected a string, but got {type(response_content)}")


wardrobe_data = load_wordrobe_data(wardrobe_file_path)

# Recommendation criteria
criteria = {
    "season": "None",
    "gender": "None",
    "color": "None",
    "style": "None"
}

# Define the prompt
prompt = f"""
    You are tasked with creating fashion style recommendations based on the user's wardrobe data and specific criteria.

    User wardrobe data:
    {json.dumps(wardrobe_data, indent=2)}

    Recommendation criteria:
    {json.dumps(criteria, indent=2)}

    Your goal is to generate complete style recommendations that meet the criteria provided. Each style should include a distinct top, bottom, and shoes. Ensure that each item (top, bottom, shoes) used in a style is unique and not repeated in other styles. The combinations should be coherent, stylish, and diverse across the styles.

    If any criteria elements are `None`, then simply recommend styles that include a top, bottom, and shoes that look good together, while respecting the gender of the items. For example, generate complete random styles for men or women, but do not mix items for women in a men's style and vice versa.

    If there are multiple items available in a category (e.g., multiple tops), make sure to use different items in each style. No item should be repeated across different styles. If you run out of unique items to use, limit the number of styles generated accordingly.

    The output should be formatted as follows:

    {{
        "style_1": {{
            "top": {{
                "image": "image_name.jpg",
                "type": "Top_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "bottom": {{
                "image": "image_name.jpg",
                "type": "Bottom_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "shoes": {{
                "image": "image_name.jpg",
                "type": "Shoes_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }}
        }},
        "style_2": {{
            "top": {{
                "image": "another_image_name.jpg",
                "type": "Another_Top_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "bottom": {{
                "image": "another_image_name.jpg",
                "type": "Another_Bottom_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }},
            "shoes": {{
                "image": "another_image_name.jpg",
                "type": "Another_Shoes_Type",
                "gender": "Gender",
                "color": "Color",
                "season": "Season",
                "style": "Style"
            }}
        }},
        "style_3": {{
            // Another complete outfit recommendation with distinct items if available
        }} 
    }}

    Please provide at least three style options that align with the given criteria, ensuring that each style is unique and does not repeat items across different styles. If the criteria elements are `None`, create complete random styles that look good together while respecting the gender of the items.
"""

    # Request completion from the model
completion = client.chat.completions.create(
            model="llama3-groq-70b-8192-tool-use-preview",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=4096,
            top_p=1,
            stream=False,
            stop=None,
        )

response_content = completion.choices[0].message['content'] if 'content' in completion.choices[0].message else completion.choices[0].message

extract_and_save_json(response_content=response_content, file_path='D:/OSC/MirwearInterface/static/JSONstyles/style_recommendations.json')
