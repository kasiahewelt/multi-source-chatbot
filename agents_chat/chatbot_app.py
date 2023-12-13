import pandas as pd
import streamlit as st
from orchestrator import get_response, SYSTEM_PROMPT
import psycopg2

st.set_page_config(page_title="Multi source Chatbot", page_icon=":robot_face:")
st.title("ChatBot")


def main():
    query = st.text_input("Enter your query:")
    if query:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            response = get_response(query, messages)
            format_response(response)
        except psycopg2.OperationalError:
            st.error("Database connection error. Please try again later.")
        except Exception as e:
            st.error(f"An error occurred: {e}")


def format_response(response):
    if isinstance(response, tuple):
        response_text = response[0]
    elif isinstance(response, list):
        response_text = "\n".join([f"* {item}" for item in response])
    elif isinstance(response, pd.DataFrame):
        st.dataframe(response)
        return
    else:
        response_text = str(response)
    st.markdown(response_text)


if __name__ == "__main__":
    main()
