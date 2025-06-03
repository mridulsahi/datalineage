
import openai

def generate_summary(dataframe, api_key):
    openai.api_key = api_key
    prompt = f"Summarize the following data lineage:\n{dataframe.head(5).to_string(index=False)}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['choices'][0]['message']['content']
