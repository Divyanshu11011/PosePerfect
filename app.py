import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv
import os
import requests
import io
from PIL import Image
import webcolors
import fal_client

# Load environment variables
load_dotenv()

# Set the FAL AI API key environment variable
os.environ['FAL_KEY'] = st.secrets["fal_ai"]["api_key"]

st.set_page_config(
    page_title="Pose Suggestions For Photographers",
)

# Define the sidebar
with st.sidebar:
    # Create the options menu
    selected = option_menu(menu_title="अtithi PosePerfect",
                           options=["Generate Pose Suggestions"],
                           icons=["camera"],
                           menu_icon="boxes",
                           default_index=0
                           )

def hex_to_name(hex_color):
    try:
        return webcolors.hex_to_name(hex_color)
    except ValueError:
        # If the exact name is not found, find the closest match
        min_colors = {}
        for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - int(hex_color[1:3], 16)) ** 2
            gd = (g_c - int(hex_color[3:5], 16)) ** 2
            bd = (b_c - int(hex_color[5:7], 16)) ** 2
            min_colors[(rd + gd + bd)] = name
        return min_colors[min(min_colors.keys())]

def generate_prompt(selected_options, day, color_theme):
    number_of_people = selected_options.get("number_of_people", "")
    event_type = selected_options["event_type"]
    photo_type = selected_options["photo_type"]
    gender = selected_options.get("gender", "")
    color = hex_to_name(color_theme[day - 1]) if len(color_theme) > 1 else hex_to_name(color_theme[0])
    
    if photo_type == "solo":
        return f"Generate a pose suggestion for a {photo_type} photo of a {gender} at a {event_type} event, with a focus on {color} color theme"
    elif number_of_people:
        return f"Generate a pose suggestion for a {photo_type} photo of {number_of_people} people at a {event_type} event, with a focus on {color} color theme"
    else:
        return f"Generate a pose suggestion for a {photo_type} photo at a {event_type} event, with a focus on {color} color theme"

if selected == "Generate Pose Suggestions":
    st.title("Pose Suggestions For Photographers")
    st.markdown("<p style='text-align:center;'>You can download the image with right click > save image</p>", unsafe_allow_html=True)

    options = {
        "event_type": ["wedding", "birthday", "anniversary", "corporate event", "casual outing"],
        "photo_type": ["solo", "couple", "group", "bride and groom"]
    }

    selected_options = {
        "event_type": st.selectbox("Event Type", options["event_type"]),
        "photo_type": st.selectbox("Photo Type", options["photo_type"])
    }

    if selected_options["photo_type"] == "group":
        selected_options["number_of_people"] = st.selectbox("Number of People", ["3-5", "6-10", "10+"])
    elif selected_options["photo_type"] == "solo":
        selected_options["number_of_people"] = "1"
        selected_options["gender"] = st.selectbox("Gender", ["male", "female"])
    elif selected_options["photo_type"] == "couple":
        selected_options["number_of_people"] = "2"
    else:
        selected_options["number_of_people"] = ""

    num_poses = st.selectbox("Number of Poses", [1, 2, 3, 4, 5])

    if num_poses > 1:
        color_theme_choice = st.selectbox("Color Theme", ["Same for all poses", "Different for each pose"])
    else:
        color_theme_choice = "Same for all poses"

    color_theme = []
    if color_theme_choice == "Same for all poses":
        color = st.color_picker("Pick a Color")
        color_theme = [color] * (num_poses if num_poses is not None else 1)
    else:
        for i in range(num_poses if num_poses is not None else 1):
            color = st.color_picker(f"Pick a Color for Pose {i+1}")
            color_theme.append(color)

    if st.button("Generate Pose Suggestions"):
        try:
            for day in range(1, num_poses + 1 if num_poses is not None else 1):
                prompt = generate_prompt(selected_options, day, color_theme)

                handler = fal_client.submit(
                    "fal-ai/fast-lightning-sdxl",
                    arguments={
                        "model_name": "stabilityai/stable-diffusion-xl-base-1.0",
                        "prompt": prompt
                    }
                )

                result = handler.get()

                if result and "images" in result and len(result["images"]) > 0:
                    image_url = result["images"][0]["url"]
                    response = requests.get(image_url)
                    image = Image.open(io.BytesIO(response.content))
                    st.image(image, caption=f"Pose {day}: {prompt}", use_column_width=True)
                else:
                    st.error(f"Failed to generate pose suggestion for pose {day}.")
        except Exception as e:
            st.error(f"Error generating pose suggestions: {e}")
