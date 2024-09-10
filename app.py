import streamlit as st
from io import BytesIO
import IPython
import json
import os
from PIL import Image
import requests
import time
import streamlit.components.v1 as com
from dotenv import load_dotenv
# @markdown To get your API key visit https://platform.stability.ai/account/keys
load_dotenv()
STABILITY_KEY = os.getenv("STABILITY_KEY")
VALID_KEYCODE = os.getenv("VALID_KEYCODE")  # Keycode để kiểm tra


com.iframe("https://lottie.host/embed/6413cf24-d224-4f9b-92ea-7bbe0e569a7e/qX7jVy5xFe.json")

page_bg_img = '''
<style>
.stApp {
  background-image: url("https://images.unsplash.com/photo-1502657877623-f66bf489d236?q=80&w=3869&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
  background-size: cover;
}

h2 {
    font-family: 'Arial', sans-serif;
    color: #FFFFFF;
    text-align: center;
    font-size: 30px;
    font-weight: bold;
    text-shadow: 2px 2px 5px #000000;
    margin-bottom: 20px;
}

.chat-bubble {
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
    max-width: 70%;
    display: inline-block;
    white-space: normal;
    overflow-wrap: break-word;
    background-color: rgba(0, 0, 0, 0.4);  /* Set transparency for chat bubbles */
}

.user-bubble {
    color: #c6c6c6;
    text-align: left;
    animation: fadeInLeft 0.5s;
}

.assistant-bubble {
    color: white;
    text-align: right;
    animation: fadeInRight 0.5s;
}

input[type="text"], textarea {
    background-color: rgba(0,0,0,1);
}

div.stButton > button {
    background-color: green;
    color: white;
}

@keyframes fadeInLeft {
    from {
        transform: translateX(-20px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes fadeInRight {
    from {
        transform: translateX(20px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
'''

st.markdown(page_bg_img, unsafe_allow_html=True)

#@title Define functions

def send_generation_request(
    host,
    params,
):
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {STABILITY_KEY}"
    }

    # Encode parameters
    files = {}
    image = params.pop("image", None)
    mask = params.pop("mask", None)
    if image is not None and image != '':
        files["image"] = open(image, 'rb')
    if mask is not None and mask != '':
        files["mask"] = open(mask, 'rb')
    if len(files)==0:
        files["none"] = ''

    # Send request
    print(f"Sending REST request to {host}...")
    response = requests.post(
        host,
        headers=headers,
        files=files,
        data=params
    )
    if not response.ok:
        raise Exception(f"HTTP {response.status_code}: {response.text}")

    return response

# Streamlit UI
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Login")
    st.markdown("### Please enter your credentials to login.")
    username = st.text_input("Username")
    keycode = st.text_input("Keycode", type="password")
    if st.button("Login"):
        if keycode == VALID_KEYCODE:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful")
        else:
            st.error("Invalid keycode")
else:
    st.title(f"Welcome, {st.session_state.username} 👋")
    st.markdown("### Generate a Stable Image")

    with st.form(key='image_generation_form'):
        prompt = st.text_input("Prompt", "op art dog illusion red blue chromostereopsis maximum saturation")
        negative_prompt = st.text_input("Negative Prompt", "")
        aspect_ratio = st.selectbox("Aspect Ratio", ["21:9", "16:9", "3:2", "5:4", "1:1", "4:5", "2:3", "9:16", "9:21"])
        seed = st.number_input("Seed", value=42)
        output_format = st.selectbox("Output Format", ["webp", "jpeg", "png"])
        submit_button = st.form_submit_button(label='Generate Image')

    if submit_button:
        host = f"https://api.stability.ai/v2beta/stable-image/generate/core"

        params = {
            "prompt" : prompt,
            "negative_prompt" : negative_prompt,
            "aspect_ratio" : aspect_ratio,
            "seed" : seed,
            "output_format": output_format
        }

        try:
            response = send_generation_request(
                host,
                params
            )

            # Decode response
            output_image = response.content
            finish_reason = response.headers.get("finish-reason")
            seed = response.headers.get("seed")

            # Check for NSFW classification
            if finish_reason == 'CONTENT_FILTERED':
                st.warning("Generation failed NSFW classifier")
            else:
                # Save and display result
                generated = f"generated_{seed}.{output_format}"
                with open(generated, "wb") as f:
                    f.write(output_image)
                st.image(generated, caption="Generated Image")

                # Download button
                st.download_button(
                    label="Download Image",
                    data=output_image,
                    file_name=generated,
                    mime=f"image/{output_format}"
                )
        except Exception as e:
            st.error(f"Error: {e}")
