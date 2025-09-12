import streamlit as st
import requests
import json
import time

# Show title and description.
st.title("💬 学習プランニングチャットボット")
st.write(
    "このチャットボットは、あなたの学習目標達成をサポートします。目標を具体的に設定して、学習の進捗を管理しましょう！"
)

# --- Add input fields for user goals on the landing page ---
st.header("あなたの学習目標を設定しましょう")
learning_theme = st.text_input("① どんなテーマの学習に取り組んでいますか？ (例：簿記、英語、資格試験、業務スキルなど)")
goal_date_and_progress = st.text_input("② いつまでにどのくらいの進捗を目指していますか？ (例：1か月後にテキスト1冊終える、来月の試験に合格する など)")
achievement_criteria = st.text_input("③ 「達成できた！」と感じるために、どんな行動や成果物があればよいですか？ (例：練習問題を9割正答、英単語を毎日30語覚える)")
# --- End of new feature ---

# Use st.secrets to access the API key stored in .streamlit/secrets.toml
google_api_key = st.secrets.get("GOOGLE_API_KEY")

if not google_api_key:
    st.info("secrets.tomlファイルにGoogle APIキーが設定されていません。")
else:
    # Set up the Gemini API endpoint
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={google_api_key}"

    # Set a fixed system prompt for the chatbot's role
    system_prompt = "あなたは、ユーザーの学習プランニングをサポートするAIアシスタントです。ユーザーが設定した目標に基づき、具体的な学習計画やモチベーション維持のためのアドバイスを提供してください。"

    # Create a session state variable to store the chat messages.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("何が知りたいですか？"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Prepare the chat history for the Gemini API.
        history = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Include the system prompt in the API payload
        payload = {
            "contents": history,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            }
        }

        # Implement exponential backoff for API requests
        retries = 3
        delay = 1

        for i in range(retries):
            try:
                # Send the request to the Gemini API.
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()

                # Parse the JSON response.
                response_json = response.json()
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
