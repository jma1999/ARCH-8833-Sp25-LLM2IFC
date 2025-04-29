from openai import OpenAI

client = OpenAI(
  api_key="Insert your openAI API key"
)

user_input = "Generate a simple small rectangular building block."

prompt_text = f"""
You are a building-model assistant.
Given user instructions about building geometry, output a 3D mesh in simplified OBJ text. 
User instructions: "{user_input}"
Now produce an OBJ-like text with vertex (v) lines and face (f) lines.
"""

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "system", "content": "You are a helpful 3D-building assistant."},
    {"role": "user", "content": prompt_text}
  ]
)

print(completion.choices[0].message);
