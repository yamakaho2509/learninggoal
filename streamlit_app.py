import streamlit as st
import requests
import json
import time # For exponential backoff

# Show title and description.
st.title("💬 チャットボット")
st.write(
    "このチャットボットは、GoogleのGemini APIを使用して応答を生成します。"
    "Google APIキーが必要です。"
)

# Use st.secrets to access the API key stored in .streamlit/secrets.toml
# See https://docs.streamlit.io/develop/concepts/connections/secrets-management
google_api_key = st.secrets.get("GOOGLE_API_KEY")

if not google_api_key:
    st.info("secrets.tomlファイルにGoogle APIキーが設定されていません。")
else:
    # Set up the Gemini API endpoint
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={google_api_key}"

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages.
    for message in st.session_state.messages:
        # Use 'assistant' for the display role for consistency with OpenAI's original code
        # while mapping to 'model' for the API call.
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("何が知りたいですか？"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare the chat history for the Gemini API.
        # The Gemini API uses 'user' and 'model' roles.
        # We need to map 'assistant' role from the session state to 'model' for the API payload.
        history = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg["content"]}]})

        payload = {
            "contents": history
        }

        # Implement exponential backoff for API requests
        retries = 3
        delay = 1

        for i in range(retries):
            try:
                # Send the request to the Gemini API.
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

                # Parse the JSON response.
                response_json = response.json()

                # Extract the text from the API response.
                # Handle potential errors if the response format is unexpected.
                gemini_response = response_json.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'エラー: 応答がありませんでした。')

                # Display the Gemini response.
                with st.chat_message("assistant"):
                    st.markdown(gemini_response)

                # Store the Gemini response in session state.
                st.session_state.messages.append({"role": "assistant", "content": gemini_response})

                # If successful, break the loop
                break

            except requests.exceptions.RequestException as e:
                st.error(f"APIリクエスト中にエラーが発生しました: {e}")
                if i < retries - 1:
                    st.info(f"リトライします... {delay}秒後")
                    time.sleep(delay)
                    delay *= 2
                else:
                    st.error("リトライの最大回数に達しました。")
            except (IndexError, KeyError) as e:
                st.error(f"API応答の解析中にエラーが発生しました: {e}")
                break
